from __future__ import annotations

import importlib
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from comemos_en_casa.config import ConfigurationError, load_settings


def _import_app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db/app")
    sys.modules.pop("comemos_en_casa.app", None)
    return importlib.import_module("comemos_en_casa.app")


def test_database_url_is_required() -> None:
    with pytest.raises(ConfigurationError, match="DATABASE_URL must be set"):
        load_settings({})


def test_blank_database_url_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="DATABASE_URL must be set"):
        load_settings({"DATABASE_URL": "  "})


def test_database_url_is_loaded_without_modification() -> None:
    settings = load_settings({"DATABASE_URL": "postgresql://user:pass@db/app"})

    assert settings.database_url == "postgresql://user:pass@db/app"


def test_app_import_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    sys.modules.pop("comemos_en_casa.app", None)

    with pytest.raises(ConfigurationError, match="DATABASE_URL must be set"):
        importlib.import_module("comemos_en_casa.app")


def test_health_checks_the_database_with_a_request_scoped_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class Cursor:
        def __enter__(self) -> "Cursor":
            return self

        def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
            return None

        def execute(self, statement: str) -> None:
            calls.append(statement)

    class Connection:
        def cursor(self) -> Cursor:
            return Cursor()

    module = _import_app(monkeypatch)
    app = module.create_app()
    app.dependency_overrides[module.get_connection] = lambda: Connection()
    try:
        response = TestClient(app).get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == ["SELECT 1"]


def test_calendar_and_recipe_routes_are_deferred(monkeypatch: pytest.MonkeyPatch) -> None:
    paths = {route.path for route in _import_app(monkeypatch).create_app().routes}

    assert "/health" in paths
    assert "/calendar" not in paths
    assert "/recipes" not in paths
