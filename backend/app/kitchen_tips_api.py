"""Expone la consulta autenticada del catálogo de trucos."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import ActiveSession, get_active_session
from app.database import get_database_session
from app.models import KitchenTip

router = APIRouter(prefix="/api/v1", tags=["kitchen-tips"])


@router.get("/kitchen-tips")
def listar_trucos(_: ActiveSession = Depends(get_active_session), db: Session = Depends(get_database_session)):
    """Devuelve los trucos ordenados por el título."""
    trucos = db.scalars(select(KitchenTip).order_by(KitchenTip.title)).all()
    return {"trucos": [{"id": str(truco.id), "title": truco.title, "content": truco.content} for truco in trucos]}
