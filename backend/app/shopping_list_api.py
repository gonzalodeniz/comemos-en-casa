"""Authenticated API for a user's shopping-list items."""

from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import ActiveSession, get_active_session, require_csrf
from app.database import get_database_session
from app.models import RecipeShoppingIngredient, RecipeShoppingSection, ShoppingCategory, ShoppingListItem, ShoppingProduct

router = APIRouter(prefix="/api/v1/shopping-list", tags=["shopping-list"])


class ShoppingListItemPayload(BaseModel):
    """Define los datos para añadir un producto a la lista de compra."""

    product_id: UUID
    quantity: Decimal
    unit: str


@router.post("", status_code=201)
async def add_shopping_list_item(
    payload: ShoppingListItemPayload,
    request: Request,
    session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, str | int]:
    """Añade un producto con cantidad y unidad a la lista de compra."""
    require_csrf(request, session)
    if db.get(ShoppingProduct, payload.product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")
    unit = payload.unit
    quantity = payload.quantity
    if unit == "kg":
        quantity = quantity.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 1000
        unit = "g"
    else:
        quantity = quantity.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    item = db.scalar(
        select(ShoppingListItem).where(
            ShoppingListItem.product_id == payload.product_id,
            ShoppingListItem.unit == unit,
            ShoppingListItem.purchased.is_(False),
        )
    )
    if item is None:
        item = ShoppingListItem(
            product_id=payload.product_id, quantity=quantity, unit=unit
        )
        db.add(item)
    else:
        item.quantity += quantity
    db.commit()
    return {
        "id": str(item.id),
        "product_id": str(item.product_id),
        "quantity": int(item.quantity),
        "unit": item.unit,
    }


@router.get("")
async def list_shopping_list_items(
    _session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict:
    """Devuelve los productos y las secciones de recetas de la lista."""
    items = db.scalars(select(ShoppingListItem)).all()
    secciones = db.scalars(select(RecipeShoppingSection)).all()
    ingredientes = db.scalars(
        select(RecipeShoppingIngredient).order_by(RecipeShoppingIngredient.position)
    ).all()
    articulos = [
        {
            "id": str(item.id),
            "product_id": str(item.product_id),
            "product_name": db.get(ShoppingProduct, item.product_id).name,
            "image_url": shopping_product_image_url(db.get(ShoppingProduct, item.product_id)),
            "quantity": int(item.quantity),
            "unit": item.unit,
        }
        for item in items
    ]
    return {
        "items": [article for item, article in zip(items, articulos) if not item.purchased],
        "purchased_items": [
            article for item, article in zip(items, articulos) if item.purchased
        ],
        "recipe_sections": [
            {
                "id": str(seccion.id),
                "name": seccion.name,
                "ingredients": [
                    {"id": str(ingrediente.id), "text": ingrediente.text,
                     "purchased": ingrediente.purchased}
                    for ingrediente in ingredientes if ingrediente.section_id == seccion.id
                ],
            }
            for seccion in secciones
        ],
    }


def shopping_product_image_url(product: ShoppingProduct) -> str | None:
    """Construye la URL autenticada de imagen para una línea de compra."""
    if not product.image_path:
        return None
    import hashlib
    version = hashlib.sha256(product.image_path.encode("utf-8")).hexdigest()
    return f"/shopping-categories/{product.category_id}/products/{product.id}/image?v={version}"


@router.delete("/{item_id}", status_code=204)
async def delete_shopping_list_item(
    item_id: UUID,
    request: Request,
    session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> Response:
    """Elimina una entrada concreta de la lista de la compra compartida."""
    require_csrf(request, session)
    item = db.get(ShoppingListItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Shopping list item not found")
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.post("/{item_id}/purchase")
async def mark_shopping_list_item_as_purchased(
    item_id: UUID,
    request: Request,
    session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, str | int]:
    """Marca como comprado un elemento pendiente de la lista."""
    require_csrf(request, session)
    item = db.get(ShoppingListItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Shopping list item not found")
    purchased_item = db.scalar(
        select(ShoppingListItem).where(
            ShoppingListItem.product_id == item.product_id,
            ShoppingListItem.unit == item.unit,
            ShoppingListItem.purchased.is_(True),
        )
    )
    if purchased_item is not None:
        purchased_item.quantity += item.quantity
        db.delete(item)
        item = purchased_item
    else:
        item.purchased = True
    db.commit()
    return {
        "id": str(item.id),
        "product_id": str(item.product_id),
        "quantity": int(item.quantity),
        "unit": item.unit,
    }


@router.post("/{item_id}/unpurchase")
async def unmark_shopping_list_item_as_purchased(
    item_id: UUID,
    request: Request,
    session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, str | int]:
    """Devuelve un elemento comprado al estado pendiente."""
    require_csrf(request, session)
    item = db.get(ShoppingListItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Shopping list item not found")
    pending_item = db.scalar(
        select(ShoppingListItem).where(
            ShoppingListItem.product_id == item.product_id,
            ShoppingListItem.unit == item.unit,
            ShoppingListItem.purchased.is_(False),
        )
    )
    if pending_item is not None:
        pending_item.quantity += item.quantity
        db.delete(item)
        item = pending_item
    else:
        item.purchased = False
    db.commit()
    return {
        "id": str(item.id),
        "product_id": str(item.product_id),
        "quantity": int(item.quantity),
        "unit": item.unit,
    }


@router.post("/recipe-ingredients/{ingredient_id}/purchase")
async def mark_recipe_ingredient_as_purchased(
    ingredient_id: UUID,
    request: Request,
    session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, str | bool]:
    """Marca como comprado un ingrediente de receta concreto."""
    require_csrf(request, session)
    ingredient = db.get(RecipeShoppingIngredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=404, detail="Recipe ingredient not found")
    ingredient.purchased = True
    db.commit()
    return {"id": str(ingredient.id), "purchased": ingredient.purchased}


@router.post("/recipe-ingredients/{ingredient_id}/unpurchase")
async def unmark_recipe_ingredient_as_purchased(
    ingredient_id: UUID,
    request: Request,
    session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, str | bool]:
    """Devuelve a pendiente un ingrediente de receta concreto."""
    require_csrf(request, session)
    ingredient = db.get(RecipeShoppingIngredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=404, detail="Recipe ingredient not found")
    ingredient.purchased = False
    db.commit()
    return {"id": str(ingredient.id), "purchased": ingredient.purchased}


@router.delete("/recipe-ingredients/{ingredient_id}", status_code=204)
async def delete_recipe_ingredient(
    ingredient_id: UUID,
    request: Request,
    session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> Response:
    """Elimina una línea concreta de una sección de receta."""
    require_csrf(request, session)
    ingredient = db.get(RecipeShoppingIngredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=404, detail="Recipe ingredient not found")
    db.delete(ingredient)
    db.commit()
    return Response(status_code=204)


@router.delete("/recipe-sections/{section_id}", status_code=204)
async def delete_recipe_shopping_section(
    section_id: UUID,
    request: Request,
    session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> Response:
    """Elimina una sección de receta y sus ingredientes asociados."""
    require_csrf(request, session)
    section = db.get(RecipeShoppingSection, section_id)
    if section is None:
        raise HTTPException(status_code=404, detail="Recipe shopping section not found")
    db.query(RecipeShoppingIngredient).filter_by(section_id=section_id).delete()
    db.delete(section)
    db.commit()
    return Response(status_code=204)
