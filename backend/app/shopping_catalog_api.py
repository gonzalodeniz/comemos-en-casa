# Expone el catálogo compartido de categorías y productos de compra.
"""Authenticated API for the shared shopping catalog."""

from fastapi import APIRouter, Depends, HTTPException, Request
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import ActiveSession, get_active_session, require_csrf
from app.database import get_database_session
from app.models import ShoppingCategory, ShoppingProduct

router = APIRouter(prefix="/api/v1/shopping-categories", tags=["shopping-catalog"])


@router.get("")
async def list_categories(
    _session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, list[dict[str, str]]]:
    categories = db.scalars(select(ShoppingCategory).order_by(ShoppingCategory.name)).all()
    return {"categories": [{"id": str(category.id), "name": category.name} for category in categories]}


@router.post("", status_code=201)
async def create_category(
    payload: dict[str, str],
    request: Request,
    session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, str]:
    # Crea una categoría en el catálogo compartido.
    require_csrf(request, session)
    name = payload.get("name", "").strip()
    if set(payload) != {"name"} or not name:
        raise HTTPException(status_code=422, detail="Invalid category")
    category = ShoppingCategory(name=name)
    db.add(category)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category already exists") from error
    db.refresh(category)
    return {"id": str(category.id), "name": category.name}


@router.post("/{category_id}/products", status_code=201)
async def create_product(
    category_id: UUID,
    payload: dict[str, str],
    request: Request,
    session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, str]:
    # Crea un producto en una categoría existente del catálogo compartido.
    require_csrf(request, session)
    name = payload.get("name", "").strip()
    if set(payload) != {"name"} or not name:
        raise HTTPException(status_code=422, detail="Invalid product")
    category = db.get(ShoppingCategory, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    product = ShoppingProduct(category_id=category.id, name=name)
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"id": str(product.id), "name": product.name}


@router.get("/{category_id}/products")
async def list_products(
    category_id: UUID,
    _session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, list[dict[str, str]]]:
    # Devuelve los productos de una categoría a un usuario autenticado.
    if db.get(ShoppingCategory, category_id) is None:
        raise HTTPException(status_code=404, detail="Category not found")
    products = db.scalars(
        select(ShoppingProduct)
        .where(ShoppingProduct.category_id == category_id)
        .order_by(ShoppingProduct.name)
    ).all()
    return {
        "products": [
            {"id": str(product.id), "name": product.name} for product in products
        ]
    }
