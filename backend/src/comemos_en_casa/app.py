"""FastAPI application entry point."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI

from .config import load_settings
from .database import get_connection


def create_app() -> FastAPI:
    """Create the HTTP application for the currently supported API surface."""
    load_settings()
    application = FastAPI(title="Comemos en casa")

    @application.get("/health")
    def health(connection: Any = Depends(get_connection)) -> dict[str, str]:
        """Confirm that the application can reach its configured database."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "ok"}

    return application


app = create_app()
