from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.database import database_url

engine = create_engine(database_url(), pool_pre_ping=True)

app = FastAPI(title="Comemos en casa API")


def database_is_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    if not database_is_ready():
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok"}
