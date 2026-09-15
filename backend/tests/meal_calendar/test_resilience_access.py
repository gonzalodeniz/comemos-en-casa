from __future__ import annotations

import importlib
from pathlib import Path
import sys

import psycopg
from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.meal_calendar.rate_limit import consume_rate_limit


class _Cursor:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self.row = row
        self.calls: list[tuple[str, tuple[object, ...] | None]] = []

    def __enter__(self) -> "_Cursor":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def execute(self, statement: str, params: tuple[object, ...] | None = None) -> None:
        self.calls.append((statement, params))

    def fetchone(self) -> tuple[object, ...] | None:
        return self.row


class _Connection:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self.cursor_instance = _Cursor(row)

    def cursor(self) -> _Cursor:
        return self.cursor_instance


def _app(monkeypatch: pytest.MonkeyPatch, *, guest_mode: str | None = None):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db/app")
    if guest_mode is None:
        monkeypatch.delenv("ENABLE_GUEST_USER", raising=False)
    else:
        monkeypatch.setenv("ENABLE_GUEST_USER", guest_mode)
    sys.modules.pop("comemos_en_casa.app", None)
    return importlib.import_module("comemos_en_casa.app")


def test_disabled_guest_access_returns_the_stable_authentication_error(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _app(monkeypatch, guest_mode="false")

    response = TestClient(module.create_app()).get("/api/v1/meal-calendar/context")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "authentication_required"


def test_rate_limit_consumption_uses_an_atomic_read_write_bucket() -> None:
    connection = _Connection((None, 19))

    result = consume_rate_limit(connection, client_ip="127.0.0.1", operation_class="write")

    assert result.allowed is False
    assert result.limit == 30
    assert result.retry_after == 19
    query, params = connection.cursor_instance.calls[0]
    assert "INSERT INTO meal_calendar_rate_limits" in query
    assert "ON CONFLICT (client_ip, window_start, operation_class) DO UPDATE" in query
    assert "request_count < %s" in query
    assert params == ("127.0.0.1", "write", 30)


def test_exhausted_bucket_returns_retry_and_limit_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _app(monkeypatch)
    app = module.create_app()
    app.dependency_overrides[module.get_connection] = lambda: _Connection((None, 12))
    try:
        response = TestClient(app).get("/api/v1/meal-calendar/context")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 429
    assert response.json()["error"] == {
        "code": "rate_limit_exceeded",
        "message": "Too many calendar requests. Try again after the current minute window.",
        "retryable": True,
        "fieldErrors": {},
    }
    assert response.headers["retry-after"] == "12"
    assert response.headers["x-ratelimit-limit"] == "60"
    assert response.headers["x-ratelimit-remaining"] == "0"


def test_direct_connection_retries_a_transient_failure_once(monkeypatch: pytest.MonkeyPatch) -> None:
    from comemos_en_casa import database

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db/app")
    connection = object()
    calls: list[str] = []

    def connect(database_url: str) -> object:
        calls.append(database_url)
        if len(calls) == 1:
            raise psycopg.OperationalError("temporary connection failure")
        return connection

    monkeypatch.setattr(database.psycopg, "connect", connect)

    assert database.connect_with_retry() is connection
    assert calls == ["postgresql://user:pass@db/app", "postgresql://user:pass@db/app"]
