"""Expone la consulta autenticada del catálogo de trucos."""
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import ActiveSession, get_active_session
from app.database import get_database_session
from app.models import KitchenTip

router = APIRouter(prefix="/api/v1", tags=["kitchen-tips"])


class TrucoEntrada(BaseModel):
    """Define los campos necesarios para crear un truco."""
    title: str
    content: str

    @field_validator("title", "content")
    @classmethod
    def validar_texto_no_vacio(cls, valor: str) -> str:
        """Rechaza campos compuestos únicamente por espacios."""
        if not valor.strip():
            raise ValueError("El campo no puede estar vacío.")
        return valor


@router.patch("/kitchen-tips/{truco_id}")
def editar_truco(truco_id: UUID, entrada: TrucoEntrada, _: ActiveSession = Depends(get_active_session), db: Session = Depends(get_database_session)):
    """Actualiza un truco compartido por usuarios autenticados."""
    truco = db.get(KitchenTip, truco_id)
    if truco is None:
        raise HTTPException(status_code=404, detail="Truco no encontrado")
    truco.title = entrada.title
    truco.content = entrada.content
    db.commit()
    return {"id": str(truco.id), "title": truco.title, "content": truco.content}


@router.post("/kitchen-tips", status_code=status.HTTP_201_CREATED)
def crear_truco(entrada: TrucoEntrada, _: ActiveSession = Depends(get_active_session), db: Session = Depends(get_database_session)):
    """Guarda un truco para que lo consulten los usuarios autenticados."""
    truco = KitchenTip(title=entrada.title, content=entrada.content)
    db.add(truco)
    db.commit()
    return {"id": str(truco.id), "title": truco.title, "content": truco.content}


@router.get("/kitchen-tips")
def listar_trucos(_: ActiveSession = Depends(get_active_session), db: Session = Depends(get_database_session)):
    """Devuelve los trucos ordenados por el título."""
    trucos = db.scalars(select(KitchenTip).order_by(KitchenTip.title)).all()
    return {"trucos": [{"id": str(truco.id), "title": truco.title, "content": truco.content} for truco in trucos]}
