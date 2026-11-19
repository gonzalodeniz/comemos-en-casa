"""Construye la API y expone comprobaciones de servicio.

Configura CORS, incorpora las rutas de autenticación y separa la disponibilidad HTTP de la conexión efectiva con la base de datos.
"""

import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.auth import router as auth_router
from app.database import engine
from app.meal_planning_api import router as meal_planning_router
from app.recipes_api import router as recipes_router
from app.shopping_catalog_api import router as shopping_catalog_router
from app.shopping_list_api import router as shopping_list_router
from app.backups import router as backups_router, _WRITE_LOCK, run_scheduled_backup
from app.kitchen_tips_api import router as kitchen_tips_router
from app.food_images import cleanup_expired_temporary
from app.meal_planning_api import DATA_ROOT
from app.settings import allowed_origins

logger = logging.getLogger(__name__)

async def _cleanup_food_image_temporaries() -> None:
    while True:
        await asyncio.to_thread(cleanup_expired_temporary, DATA_ROOT)
        await asyncio.sleep(300)


async def _run_scheduled_backups() -> None:
    """Comprueba cada minuto si la copia automática está vencida."""
    while True:
        try:
            await run_scheduled_backup()
        except Exception:
            logger.exception("scheduled_backup_failed")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    cleanup_task = asyncio.create_task(_cleanup_food_image_temporaries())
    backup_task = asyncio.create_task(_run_scheduled_backups())
    try:
        yield
    finally:
        cleanup_task.cancel()
        backup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task
        with suppress(asyncio.CancelledError):
            await backup_task


app = FastAPI(title="Comemos en casa API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins()),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.include_router(auth_router)
app.include_router(meal_planning_router)
app.include_router(recipes_router)
app.include_router(shopping_catalog_router)
app.include_router(shopping_list_router)
app.include_router(backups_router)
app.include_router(kitchen_tips_router)


@app.middleware("http")
async def serialize_writes_during_backup(request, call_next):
    """Serializa las escrituras para que una copia capture un estado consistente."""
    if request.method in {"POST", "PATCH", "DELETE"} and request.url.path != "/api/v1/backups" and not request.url.path.endswith("/restore"):
        async with _WRITE_LOCK:
            return await call_next(request)
    return await call_next(request)


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
