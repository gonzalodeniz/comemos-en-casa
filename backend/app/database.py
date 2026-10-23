import os

from sqlalchemy.engine import URL


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
