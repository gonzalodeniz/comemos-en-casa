"""FastAPI application entry point."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from .auth.api import register_routes as register_auth_routes
from .config import load_settings
from .database import get_connection
from .meal_calendar.api import register_routes
from .recipes.api import register_routes as register_recipe_routes


def create_app() -> FastAPI:
    """Create the HTTP application for the currently supported API surface."""
    application = FastAPI(title="Comemos en casa")
    application.state.settings = load_settings()

    @application.get("/health")
    def health(connection: Any = Depends(get_connection)) -> dict[str, str]:
        """Confirm that the application can reach its configured database."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "ok"}

    application.mount("/media", StaticFiles(directory=application.state.settings.media_root, check_dir=False), name="media")
    register_auth_routes(application)
    register_routes(application)
    register_recipe_routes(application)
    return application


app = create_app()
