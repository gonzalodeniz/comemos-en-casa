from __future__ import annotations

import importlib
from pathlib import Path
import sys
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.auth.models import LoginAttempt, User


class Connection:
    """A route fake; auth service behavior is injected below rather than using PostgreSQL."""


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db/app")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "https://example.test/api/v1/auth/callback")
    sys.modules.pop("comemos_en_casa.app", None)
    module = importlib.import_module("comemos_en_casa.app")
    application = module.create_app()
    application.dependency_overrides[module.get_connection] = Connection
    try:
        yield application
    finally:
        application.dependency_overrides.clear()


def test_login_callback_me_and_logout_preserve_the_cookie_and_route_contracts(
    app: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    from comemos_en_casa.auth import api

    user = User(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        google_subject="subject",
        email="person@example.test",
        display_name="Person",
        picture_url="https://example.test/picture.jpg",
    )
    calls: list[tuple[str, object]] = []

    class FakeAuthService:
        def __init__(self, repository: object) -> None:
            pass

        def begin_login(self) -> LoginAttempt:
            calls.append(("begin", None))
            return LoginAttempt("state-value", "nonce-value", __import__("datetime").datetime.now(__import__("datetime").timezone.utc))

        def authorization_url(self, configuration: object, attempt: LoginAttempt) -> str:
            calls.append(("authorization", configuration))
            return "https://accounts.google.test/auth?scope=openid%20email%20profile&state=state-value&nonce=nonce-value"

        def complete_login(self, configuration: object, *, state: str, code: str) -> tuple[User, str, object]:
            calls.append(("callback", (state, code)))
            return user, "opaque-session", object()

        def current_user(self, token: str | None) -> User:
            calls.append(("me", token))
            if token != "opaque-session":
                raise api.AuthenticationError("missing")
            return user

        def logout(self, token: str | None) -> None:
            calls.append(("logout", token))

    monkeypatch.setattr(api, "AuthService", FakeAuthService)
    client = TestClient(app)  # type: ignore[arg-type]

    login = client.get("/api/v1/auth/login", follow_redirects=False)
    callback = client.get("/api/v1/auth/callback", params={"state": "state-value", "code": "code-value"}, follow_redirects=False)
    me = client.get("/api/v1/auth/me", headers={"Cookie": "cec_session=opaque-session"})
    logout = client.post("/api/v1/auth/logout", headers={"Cookie": "cec_session=opaque-session"})

    assert login.status_code == 307
    assert login.headers["location"].startswith("https://accounts.google.test/auth?")
    assert callback.status_code == 303
    assert callback.headers["location"] == "http://localhost:5173"
    assert "HttpOnly" in callback.headers["set-cookie"]
    assert "Secure" not in callback.headers["set-cookie"]
    assert "SameSite=lax" in callback.headers["set-cookie"]
    assert "opaque-session" not in callback.text
    assert me.status_code == 200
    assert me.headers["cache-control"] == "no-store"
    assert me.json() == {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "person@example.test",
        "displayName": "Person",
        "pictureUrl": "https://example.test/picture.jpg",
    }
    assert logout.status_code == 204
    assert "Max-Age=0" in logout.headers["set-cookie"]
    assert ("callback", ("state-value", "code-value")) in calls
    assert ("logout", "opaque-session") in calls


def test_callback_rejects_missing_code_without_creating_a_session(app: object) -> None:
    client = TestClient(app)  # type: ignore[arg-type]

    response = client.get("/api/v1/auth/callback", params={"state": "state-value"})

    assert response.status_code == 400
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["error"]["code"] == "authentication_failed"
