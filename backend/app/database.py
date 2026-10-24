"""Configura la conexión y las sesiones de base de datos.

Prioriza una URL explícita o la compone desde variables de entorno; la dependencia proporciona una sesión por petición.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker


def database_url() -> URL | str:
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url
    return URL.create(
        "postgresql+psycopg",
        username=os.getenv("DB_USER", "comemos"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=5432,
        database=os.getenv("DB_NAME", "comemos"),
    )


engine = create_engine(database_url(), pool_pre_ping=True)
SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)


async def get_database_session():
    with SessionFactory() as session:
        yield session
