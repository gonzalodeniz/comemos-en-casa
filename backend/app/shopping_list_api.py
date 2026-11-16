"""Authenticated API for a user's shopping-list items."""

from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import ActiveSession, get_active_session, require_csrf
from app.database import get_database_session
from app.ingredient_images import imagen_ingrediente
from app.models import Recipe, RecipeShoppingIngredient, RecipeShoppingSection, ShoppingCategory, ShoppingListItem, ShoppingProduct

router = APIRouter(prefix="/api/v1/shopping-list", tags=["shopping-list"])


class ShoppingListItemPayload(BaseModel):
    """Define los datos para añadir un producto a la lista de compra."""

    product_id: UUID
    quantity: Decimal | None = None
    unit: str | None = None
    quantity_text: str | None = None
    observation: str | None = None


class ActualizacionCantidad(BaseModel):
    """Describe una cantidad numérica o una descripción libre."""

    quantity: Decimal | None = None
    unit: str | None = None
    quantity_text: str | None = None
    observation: str | None = None


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
    observacion = payload.observation.strip() if payload.observation is not None else None
    if observacion == "":
        observacion = None
    if observacion is not None and len(observacion) > 255:
        raise HTTPException(status_code=422, detail="Invalid observation")
    if payload.quantity_text is not None:
        texto = payload.quantity_text.strip()
        if not texto or len(texto) > 255 or payload.quantity is not None or payload.unit is not None:
            raise HTTPException(status_code=422, detail="Invalid free text")
        item = ShoppingListItem(product_id=payload.product_id, quantity=0, unit="unit", quantity_text=texto, observation=observacion)
        db.add(item)
        db.commit()
        return {"id": str(item.id), "product_id": str(item.product_id), "quantity": 0, "unit": "unit", "quantity_text": texto, **({"observation": observacion} if observacion is not None else {})}
    unit = payload.unit
    quantity = payload.quantity
    if quantity is None or not quantity.is_finite() or quantity <= 0 or unit not in {"unit", "g", "kg"}:
        raise HTTPException(status_code=422, detail="Invalid quantity or unit")
    if unit == "kg":
        quantity = quantity.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 1000
        unit = "g"
    else:
        quantity = quantity.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    criterio_observacion = ShoppingListItem.observation.is_(None) if observacion is None else ShoppingListItem.observation == observacion
    item = db.scalar(
        select(ShoppingListItem).where(
            ShoppingListItem.product_id == payload.product_id,
            ShoppingListItem.unit == unit,
            ShoppingListItem.purchased.is_(False),
            ShoppingListItem.quantity_text.is_(None),
            criterio_observacion,
        )
    )
    if item is None:
        item = ShoppingListItem(
            product_id=payload.product_id, quantity=quantity, unit=unit, observation=observacion
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
        **({"observation": item.observation} if item.observation is not None else {}),
    }


@router.get("")
async def list_shopping_list_items(
    _session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict:
    """Devuelve los productos y las secciones de recetas de la lista."""
    items = db.scalars(select(ShoppingListItem)).all()
    secciones = db.scalars(select(RecipeShoppingSection)).all()
    productos_catalogo = db.scalars(select(ShoppingProduct)).all()
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
            **({"quantity_text": item.quantity_text} if item.quantity_text is not None else {}),
            **({"observation": item.observation} if item.observation is not None else {}),
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
                **({"image_url": imagen_receta_compra(seccion, db)} if imagen_receta_compra(seccion, db) else {}),
                "ingredients": [
                    {"id": str(ingrediente.id), "text": ingrediente.text,
                     "purchased": ingrediente.purchased, **({"image_url": imagen_ingrediente(ingrediente.text, productos_catalogo)} if imagen_ingrediente(ingrediente.text, productos_catalogo) else {})}
                    for ingrediente in ingredientes if ingrediente.section_id == seccion.id
                ],
            }
            for seccion in secciones
        ],
    }


@router.patch("/{item_id}")
async def actualizar_cantidad(
    item_id: UUID, payload: ActualizacionCantidad, request: Request,
    session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict:
    """Actualiza una entrada pendiente sin combinar valores de texto libre."""
    require_csrf(request, session)
    item = db.get(ShoppingListItem, item_id)
    if item is None or item.purchased:
        raise HTTPException(status_code=404, detail="Pending shopping list item not found")
    texto = payload.quantity_text.strip() if payload.quantity_text is not None else None
    observacion = payload.observation.strip() if payload.observation is not None else item.observation
    if observacion == "":
        observacion = None
    if observacion is not None and len(observacion) > 255:
        raise HTTPException(status_code=422, detail="Invalid observation")
    if texto is not None:
        if not texto or len(texto) > 255 or payload.quantity is not None or payload.unit is not None:
            raise HTTPException(status_code=422, detail="Invalid free text")
        item.quantity_text = texto
        item.observation = observacion
    else:
        if payload.quantity is None or not payload.quantity.is_finite() or payload.quantity <= 0 or payload.unit not in {"unit", "g", "kg"}:
            raise HTTPException(status_code=422, detail="Invalid quantity or unit")
        cantidad = (payload.quantity.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 1000 if payload.unit == "kg" else payload.quantity.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        if cantidad <= 0 or cantidad > 999999999:
            raise HTTPException(status_code=422, detail="Invalid quantity")
        unidad = "g" if payload.unit == "kg" else payload.unit
        criterio_observacion = ShoppingListItem.observation.is_(None) if observacion is None else ShoppingListItem.observation == observacion
        duplicado = db.scalar(select(ShoppingListItem).where(ShoppingListItem.id != item.id, ShoppingListItem.product_id == item.product_id, ShoppingListItem.unit == unidad, ShoppingListItem.purchased.is_(False), ShoppingListItem.quantity_text.is_(None), criterio_observacion))
        if duplicado is not None:
            raise HTTPException(status_code=409, detail="A numeric entry already exists for this unit")
        item.quantity = cantidad
        item.unit = unidad
        item.quantity_text = None
        item.observation = observacion
    db.commit()
    return {"id": str(item.id), "product_id": str(item.product_id), "quantity": int(item.quantity), "unit": item.unit, "quantity_text": item.quantity_text, "observation": item.observation}


def imagen_receta_compra(seccion: RecipeShoppingSection, db: Session) -> str | None:
    """Resuelve la imagen de la receta asociada o de una coincidencia antigua única."""
    receta = db.get(Recipe, seccion.recipe_id) if seccion.recipe_id else None
    if seccion.recipe_id is None:
        coincidencias = db.scalars(select(Recipe).where(Recipe.title == seccion.name).limit(2)).all()
        receta = coincidencias[0] if len(coincidencias) == 1 else None
    if receta is None or not receta.image_path:
        return None
    import hashlib
    version = hashlib.sha256(receta.image_path.encode()).hexdigest()
    return f"/recipes/{receta.id}/image?v={version}"


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
            ShoppingListItem.quantity_text.is_(None),
            ShoppingListItem.observation == item.observation if item.observation is not None else ShoppingListItem.observation.is_(None),
        )
    )
    if item.quantity_text is not None:
        purchased_item = None
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
        **({"quantity_text": item.quantity_text} if item.quantity_text is not None else {}),
        **({"observation": item.observation} if item.observation is not None else {}),
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
            ShoppingListItem.quantity_text.is_(None),
            ShoppingListItem.observation == item.observation if item.observation is not None else ShoppingListItem.observation.is_(None),
        )
    )
    if item.quantity_text is not None:
        pending_item = None
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
        **({"quantity_text": item.quantity_text} if item.quantity_text is not None else {}),
        **({"observation": item.observation} if item.observation is not None else {}),
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
