from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentAdminUser
from app.auth.security import hash_password
from app.core.config import get_settings
from app.db.models import (
    Account,
    AIChatMessage,
    Budget,
    FinancialGoal,
    SystemSetting,
    Transaction,
    User,
    UserRole,
    UserStatus,
)
from app.db.session import get_db
from app.ai.rag.vector_store import get_vector_store
from app.ai.rag.knowledge_docs import KnowledgeDocument

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
DbSession = Annotated[Session, Depends(get_db)]


class UserStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: UserStatus


class UserRoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: UserRole


class ResetPasswordPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    new_password: str = Field(min_length=8, max_length=128)


class AIConfigPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str = Field(default="gemini", min_length=1, max_length=50)
    model_name: str = Field(default="gemini-1.5-flash", min_length=1, max_length=100)
    api_key: str = Field(default="", max_length=500)
    rpd: int = Field(default=1000, ge=1, le=100000)
    rpm: int = Field(default=60, ge=1, le=10000)
    tpm: int = Field(default=50000, ge=1, le=1000000)


class RAGDocumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    doc_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    topic: str = Field(default="admin_upload")
    category: str = Field(default="Tài chính cá nhân")
    content: str = Field(min_length=10)
    source: str = Field(default="Admin Upload")


@router.get("/stats")
def get_system_stats(
    admin: CurrentAdminUser,
    db: DbSession,
) -> dict[str, Any]:
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.status == UserStatus.ACTIVE.value).count()
    total_transactions = db.query(Transaction).count()
    total_chat_messages = db.query(AIChatMessage).count()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_transactions": total_transactions,
        "total_chat_messages": total_chat_messages,
        "vector_store_chunks": len(get_vector_store().chunks),
    }


@router.get("/users")
def list_users(
    admin: CurrentAdminUser,
    db: DbSession,
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    query = db.query(User)
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.filter((User.email.ilike(search_term)) | (User.display_name.ilike(search_term)))
    query = query.order_by(User.created_at.desc())
    total = query.count()
    users = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "display_name": u.display_name,
                "role": u.role,
                "status": u.status,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
    }


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: str,
    admin: CurrentAdminUser,
    db: DbSession,
) -> dict[str, Any]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    account_count = db.query(Account).filter(Account.user_id == user.id).count()
    transaction_count = db.query(Transaction).filter(Transaction.user_id == user.id).count()
    budget_count = db.query(Budget).filter(Budget.user_id == user.id).count()
    goal_count = db.query(FinancialGoal).filter(FinancialGoal.user_id == user.id).count()

    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "status": user.status,
        "created_at": user.created_at.isoformat(),
        "stats": {
            "accounts": account_count,
            "transactions": transaction_count,
            "budgets": budget_count,
            "goals": goal_count,
        },
    }


@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: str,
    payload: UserStatusUpdate,
    admin: CurrentAdminUser,
    db: DbSession,
) -> dict[str, Any]:
    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    target_user.status = payload.status.value
    db.commit()
    db.refresh(target_user)
    return {
        "message": f"User status updated to {payload.status.value}",
        "user_id": target_user.id,
        "status": target_user.status,
    }


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    admin: CurrentAdminUser,
    db: DbSession,
) -> dict[str, Any]:
    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.role = payload.role.value
    db.commit()
    db.refresh(target_user)
    return {
        "message": f"User role updated to {payload.role.value}",
        "user_id": target_user.id,
        "role": target_user.role,
    }


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: str,
    payload: ResetPasswordPayload,
    admin: CurrentAdminUser,
    db: DbSession,
) -> dict[str, Any]:
    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": f"Password reset successfully for user {target_user.email}"}


@router.delete("/users/{user_id}")
def delete_user_by_admin(
    user_id: str,
    admin: CurrentAdminUser,
    db: DbSession,
) -> dict[str, Any]:
    from app.auth.service import delete_user_and_purge_all_data

    target_user = db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.email == "admin@finance.app" or target_user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete super admin user account")

    email = target_user.email
    delete_user_and_purge_all_data(db, target_user)
    return {"message": f"Successfully deleted user account {email}"}


@router.get("/ai/config")
def get_ai_config(
    admin: CurrentAdminUser,
    db: DbSession,
) -> dict[str, Any]:
    app_settings = get_settings()
    settings = {s.key: s.value for s in db.query(SystemSetting).all()}
    
    provider = settings.get("ai_provider") or getattr(app_settings, "ai_provider", "gemini")
    model_name = settings.get("ai_model_name") or getattr(app_settings, "ai_model", "gemini-3.1-flash-lite")
    
    api_key_raw = settings.get("ai_api_key") or getattr(app_settings, "gemini_api_key", "") or getattr(app_settings, "openai_api_key", "") or ""
    masked_key = (api_key_raw[:4] + "..." + api_key_raw[-4:]) if len(api_key_raw) > 8 else "********" if api_key_raw else ""

    return {
        "provider": provider,
        "model_name": model_name,
        "api_key_masked": masked_key,
        "rpd": int(settings.get("ai_rpd", "1000")),
        "rpm": int(settings.get("ai_rpm", "60")),
        "tpm": int(settings.get("ai_tpm", str(getattr(app_settings, "daily_user_token_limit", 50000)))),
    }


@router.put("/ai/config")
def update_ai_config(
    payload: AIConfigPayload,
    admin: CurrentAdminUser,
    db: DbSession,
) -> dict[str, Any]:
    updates = {
        "ai_provider": payload.provider,
        "ai_model_name": payload.model_name,
        "ai_rpd": str(payload.rpd),
        "ai_rpm": str(payload.rpm),
        "ai_tpm": str(payload.tpm),
    }
    if payload.api_key and not payload.api_key.startswith("..."):
        updates["ai_api_key"] = payload.api_key

    for k, v in updates.items():
        setting = db.query(SystemSetting).filter(SystemSetting.key == k).first()
        if setting:
            setting.value = v
            setting.updated_by = admin.id
        else:
            db.add(SystemSetting(key=k, value=v, updated_by=admin.id))
    db.commit()

    return {"message": "AI Provider, Model, and Rate Limit configurations saved successfully!"}


@router.post("/knowledge/documents")
def add_knowledge_document(
    payload: RAGDocumentCreate,
    admin: CurrentAdminUser,
) -> dict[str, Any]:
    vector_store = get_vector_store()
    doc = KnowledgeDocument(
        doc_id=payload.doc_id,
        title=payload.title,
        topic=payload.topic,
        category=payload.category,
        content=payload.content,
        source=payload.source,
    )
    indexed_count = vector_store.index_documents([doc])
    return {
        "message": f"Successfully indexed knowledge document '{payload.title}'",
        "doc_id": payload.doc_id,
        "total_vector_chunks": len(vector_store.chunks),
    }

