# Expone el catálogo compartido de categorías y productos de compra.
"""Authenticated API for the shared shopping catalog."""

from fastapi import APIRouter, Depends, HTTPException, Request
from uuid import UUID
import hashlib
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import ActiveSession, get_active_session, require_csrf
from app.database import get_database_session
from app.models import ShoppingCategory, ShoppingProduct
from app import meal_planning_api as images
from app.food_images import publish_temporary

router = APIRouter(prefix="/api/v1/shopping-categories", tags=["shopping-catalog"])


def _product_image_url(product: ShoppingProduct) -> str:
    """Construye la dirección versionada de la imagen del producto."""
    version = hashlib.sha256(product.image_path.encode("utf-8")).hexdigest()
    return f"/shopping-categories/{product.category_id}/products/{product.id}/image?v={version}"


@router.get("")
async def list_categories(
    _session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, list[dict[str, str]]]:
    categories = db.scalars(select(ShoppingCategory).order_by(ShoppingCategory.name)).all()
    return {"categories": [{"id": str(category.id), "name": category.name, **({"image_url": f"/shopping-categories/{category.id}/image?v={hashlib.sha256(category.image_path.encode('utf-8')).hexdigest()}"} if category.image_path else {})} for category in categories]}


@router.post("", status_code=201)
@images.serialized_image_publication
async def create_category(
    payload: dict[str, str],
    request: Request,
    session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, str]:
    # Crea una categoría en el catálogo compartido.
    require_csrf(request, session)
    name = payload.get("name", "").strip()
    if set(payload) - {"name", "image_token"} or not name:
        raise HTTPException(status_code=422, detail="Invalid category")
    token = payload.get("image_token")
    image_path = publish_temporary(images.DATA_ROOT, session.session.id, token, category="productos") if token else None
    if token and image_path is None:
        raise HTTPException(status_code=422, detail="Prepared image expired")
    category = ShoppingCategory(name=name, image_path=image_path)
    db.add(category)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category already exists") from error
    db.refresh(category)
    return {"id": str(category.id), "name": category.name, "image_url": f"/shopping-categories/{category.id}/image?v={hashlib.sha256(category.image_path.encode('utf-8')).hexdigest()}"} if category.image_path else {"id": str(category.id), "name": category.name}


@router.get("/{category_id}/image")
async def get_category_image(category_id: UUID,
    _session: ActiveSession = Depends(get_active_session), db: Session = Depends(get_database_session)):
    """Devuelve la imagen gestionada de una categoría autenticada."""
    category = db.get(ShoppingCategory, category_id)
    if category is None or not category.image_path:
        raise HTTPException(status_code=404, detail="Image not found")
    path = images._managed_food_image_path(category.image_path, "productos")
    if path is None or not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/webp", headers={"Cache-Control": "private, max-age=3600"})


@router.patch("/{category_id}")
@images.serialized_image_publication
async def update_category_image(category_id: UUID, payload: dict[str, object], request: Request,
    session: ActiveSession = Depends(get_active_session), db: Session = Depends(get_database_session)):
    """Sustituye o elimina la imagen de una categoría."""
    require_csrf(request, session)
    if set(payload) not in ({"image_token"}, {"remove_image"}) or ("remove_image" in payload and payload["remove_image"] is not True):
        raise HTTPException(status_code=422, detail="Invalid image update")
    if "image_token" in payload and not isinstance(payload["image_token"], str):
        raise HTTPException(status_code=422, detail="Invalid image token")
    category = db.get(ShoppingCategory, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    old_path = category.image_path
    new_path = None if payload.get("remove_image") else publish_temporary(images.DATA_ROOT, session.session.id, payload["image_token"], category="productos")
    if not payload.get("remove_image") and new_path is None:
        raise HTTPException(status_code=422, detail="Prepared image expired")
    category.image_path = new_path
    db.commit()
    if old_path and old_path != new_path:
        images._remove_food_image(old_path, "productos")
    return {"id": str(category.id), "name": category.name, "image_url": f"/shopping-categories/{category.id}/image?v={hashlib.sha256(new_path.encode('utf-8')).hexdigest()}" if new_path else None}


@router.post("/{category_id}/products", status_code=201)
@images.serialized_image_publication
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
    if set(payload) - {"name", "image_token"} or not name:
        raise HTTPException(status_code=422, detail="Invalid product")
    category = db.get(ShoppingCategory, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    token = payload.get("image_token")
    image_path = publish_temporary(images.DATA_ROOT, session.session.id, token, category="productos") if token else None
    if token and image_path is None:
        raise HTTPException(status_code=422, detail="Prepared image expired")
    product = ShoppingProduct(category_id=category.id, name=name, image_path=image_path)
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
            {"id": str(product.id), "name": product.name, **({"image_url": _product_image_url(product)} if product.image_path else {})} for product in products
        ]
    }


@router.patch("/{category_id}/products/{product_id}")
@images.serialized_image_publication
async def update_product_image(category_id: UUID, product_id: UUID, payload: dict[str, object],
    request: Request, session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session)):
    """Sustituye o elimina la imagen del producto sin alterar su nombre."""
    require_csrf(request, session)
    if set(payload) not in ({"image_token"}, {"remove_image"}) or ("remove_image" in payload and payload["remove_image"] is not True):
        raise HTTPException(status_code=422, detail="Invalid image update")
    if "image_token" in payload and not isinstance(payload["image_token"], str):
        raise HTTPException(status_code=422, detail="Invalid image token")
    product = db.get(ShoppingProduct, product_id)
    if product is None or product.category_id != category_id:
        raise HTTPException(status_code=404, detail="Product not found")
    old_path = product.image_path
    new_path = None if payload.get("remove_image") else publish_temporary(images.DATA_ROOT, session.session.id, payload["image_token"], category="productos")
    if not payload.get("remove_image") and new_path is None:
        raise HTTPException(status_code=422, detail="Prepared image expired")
    product.image_path = new_path
    db.commit()
    if old_path and old_path != new_path:
        images._remove_food_image(old_path, "productos")
    return {"id": str(product.id), "name": product.name, "image_url": _product_image_url(product) if new_path else None}


@router.get("/{category_id}/products/{product_id}/image")
async def get_product_image(category_id: UUID, product_id: UUID,
    _session: ActiveSession = Depends(get_active_session), db: Session = Depends(get_database_session)):
    """Devuelve la imagen gestionada de un producto autenticado."""
    product = db.get(ShoppingProduct, product_id)
    if product is None or product.category_id != category_id or not product.image_path:
        raise HTTPException(status_code=404, detail="Image not found")
    path = images._managed_food_image_path(product.image_path, "productos")
    if path is None or not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/webp", headers={"Cache-Control": "private, max-age=3600"})
