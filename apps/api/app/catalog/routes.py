from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.catalog.schemas import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    MerchantAliasCreate,
    MerchantCreate,
    MerchantLookupResponse,
    MerchantResponse,
)
from app.catalog.service import (
    CatalogError,
    add_alias,
    create_category,
    create_merchant,
    lookup_merchant,
    visible_categories,
)
from app.db.models import Merchant
from app.db.session import get_db

router = APIRouter(tags=["catalog"])
DbSession = Annotated[Session, Depends(get_db)]


def catalog_error(exc: CatalogError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": "catalog_validation_error", "message": str(exc)},
    )


@router.get("/api/v1/categories", response_model=CategoryListResponse)
def categories(
    current_user: CurrentUser, db: DbSession, type: str | None = Query(default=None)
) -> CategoryListResponse:
    items = visible_categories(db, current_user, type)
    return CategoryListResponse(items=items, total=len(items))


@router.post(
    "/api/v1/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED
)
def create_category_route(
    payload: CategoryCreate, current_user: CurrentUser, db: DbSession
) -> CategoryResponse:
    try:
        category = create_category(db, current_user, payload.model_dump())
        db.commit()
        db.refresh(category)
        return category
    except CatalogError as exc:
        db.rollback()
        raise catalog_error(exc) from exc


@router.get("/api/v1/merchants/lookup", response_model=MerchantLookupResponse)
def merchant_lookup(name: str, current_user: CurrentUser, db: DbSession) -> MerchantLookupResponse:
    del current_user
    return MerchantLookupResponse(merchant=lookup_merchant(db, name))


@router.post(
    "/api/v1/merchants", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED
)
def merchant_create(
    payload: MerchantCreate, current_user: CurrentUser, db: DbSession
) -> MerchantResponse:
    del current_user
    merchant = create_merchant(db, payload.model_dump())
    db.commit()
    db.refresh(merchant)
    return merchant


@router.post("/api/v1/merchants/{merchant_id}/aliases", response_model=MerchantResponse)
def merchant_alias(
    merchant_id: str, payload: MerchantAliasCreate, current_user: CurrentUser, db: DbSession
) -> MerchantResponse:
    del current_user
    merchant = db.get(Merchant, merchant_id)
    if merchant is None:
        raise HTTPException(
            status_code=404, detail={"code": "merchant_not_found", "message": "Merchant not found"}
        )
    add_alias(db, merchant, payload.alias)
    db.commit()
    db.refresh(merchant)
    return merchant
