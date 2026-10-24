"""Construye la API y expone comprobaciones de servicio.

Configura CORS, incorpora las rutas de autenticación y separa la disponibilidad HTTP de la conexión efectiva con la base de datos.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.auth import router as auth_router
from app.database import engine
from app.settings import allowed_origins

app = FastAPI(title="Comemos en casa API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins()),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.include_router(auth_router)


def database_is_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    if not database_is_ready():
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok"}
