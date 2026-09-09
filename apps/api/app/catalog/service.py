from __future__ import annotations

import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Category, Merchant, MerchantAlias, User


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


class CatalogError(Exception):
    pass


def visible_categories(db: Session, user: User, category_type: str | None = None) -> list[Category]:
    statement = (
        select(Category)
        .where(
            Category.is_active.is_(True),
            or_(Category.is_system.is_(True), Category.user_id == user.id),
        )
        .order_by(Category.sort_order, Category.name)
    )
    if category_type:
        statement = statement.where(Category.type == category_type)
    return list(db.scalars(statement).all())


def create_category(db: Session, user: User, values: dict[str, object]) -> Category:
    duplicate = db.scalar(
        select(Category).where(
            Category.user_id == user.id,
            Category.name == values["name"],
            Category.type == values["type"],
        )
    )
    if duplicate:
        raise CatalogError("Category already exists")
    parent_id = values.get("parent_id")
    if parent_id:
        parent = db.get(Category, parent_id)
        if parent is None or (not parent.is_system and parent.user_id != user.id):
            raise CatalogError("Category parent is not available")
        if parent.id == user.id:
            raise CatalogError("Category cannot be its own parent")
    category = Category(user_id=user.id, is_system=False, is_active=True, **values)
    db.add(category)
    db.flush()
    return category


def create_merchant(db: Session, values: dict[str, object]) -> Merchant:
    canonical_name = str(values["canonical_name"])
    normalized_name = normalize_name(canonical_name)
    existing = db.scalar(select(Merchant).where(Merchant.normalized_name == normalized_name))
    if existing:
        return existing
    merchant = Merchant(
        canonical_name=canonical_name,
        normalized_name=normalized_name,
        **{k: v for k, v in values.items() if k != "canonical_name"},
    )
    db.add(merchant)
    db.flush()
    return merchant


def add_alias(db: Session, merchant: Merchant, alias: str) -> MerchantAlias:
    normalized_alias = normalize_name(alias)
    existing = db.scalar(
        select(MerchantAlias).where(
            MerchantAlias.merchant_id == merchant.id,
            MerchantAlias.normalized_alias == normalized_alias,
        )
    )
    if existing:
        return existing
    item = MerchantAlias(merchant_id=merchant.id, alias=alias, normalized_alias=normalized_alias)
    db.add(item)
    db.flush()
    return item


def lookup_merchant(db: Session, name: str) -> Merchant | None:
    normalized = normalize_name(name)
    return db.scalar(select(Merchant).where(Merchant.normalized_name == normalized)) or db.scalar(
        select(Merchant).join(MerchantAlias).where(MerchantAlias.normalized_alias == normalized)
    )
