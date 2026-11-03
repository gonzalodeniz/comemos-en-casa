"""Authenticated API for a user's shopping-list items."""

from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import ActiveSession, get_active_session, require_csrf
from app.database import get_database_session
from app.models import ShoppingListItem, ShoppingProduct

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
    return {"product_id": str(item.product_id), "quantity": int(item.quantity), "unit": item.unit}


@router.get("")
async def list_shopping_list_items(
    _session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, list[dict[str, str | int]]]:
    """Devuelve los productos y cantidades de la lista de compra."""
    items = db.scalars(select(ShoppingListItem)).all()
    return {
        "items": [
            {"product_id": str(item.product_id), "quantity": int(item.quantity), "unit": item.unit}
            for item in items
        ]
    }
