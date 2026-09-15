from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from uuid import UUID

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.auth.models import GoogleIdentity, User
from comemos_en_casa.auth.service import (
    AuthService,
    AuthenticationFailed,
    GoogleOidcConfiguration,
    LOGIN_LIFETIME,
    SESSION_LIFETIME,
    _identity_from_claims,
)


NOW = datetime(2025, 6, 1, tzinfo=timezone.utc)
USER = User(
    id=UUID("00000000-0000-0000-0000-000000000001"),
    google_subject="google-subject",
    email="person@example.test",
    display_name="Person",
    picture_url=None,
)
CONFIGURATION = GoogleOidcConfiguration("client-id", "client-secret", "https://example.test/api/v1/auth/callback")


class FakeRepository:
    def __init__(self) -> None:
        self.attempts: dict[str, str] = {}
        self.created_session: tuple[UUID, str, datetime] | None = None
        self.renewed: tuple[str, datetime] | None = None
        self.revoked: str | None = None
        self.session_user: User | None = USER

    def create_login_attempt(self, attempt: object) -> None:
        self.attempts[attempt.state] = attempt.nonce  # type: ignore[attr-defined]

    def consume_login_attempt(self, state: str, now: datetime) -> str | None:
        return self.attempts.pop(state, None)

    def upsert_user(self, identity: GoogleIdentity) -> User:
        assert identity == GoogleIdentity("google-subject", "person@example.test", "Person", None)
        return USER

    def create_session(self, user_id: UUID, token: str, expires_at: datetime) -> None:
        self.created_session = (user_id, token, expires_at)

    def find_user_for_session(self, token: str, now: datetime) -> User | None:
        return self.session_user

    def renew_session(self, token: str, expires_at: datetime) -> None:
        self.renewed = (token, expires_at)

    def revoke_session(self, token: str) -> None:
        self.revoked = token


class FakeOidcClient:
    def __init__(self) -> None:
        self.exchanged: list[str] = []
        self.verified: list[tuple[str, str]] = []

    def authorization_url(self, configuration: GoogleOidcConfiguration, attempt: object) -> str:
        assert configuration == CONFIGURATION
        return f"https://accounts.example.test/?state={attempt.state}"  # type: ignore[attr-defined]

    def exchange_code(self, configuration: GoogleOidcConfiguration, code: str) -> str:
        assert configuration == CONFIGURATION
        self.exchanged.append(code)
        return "signed-id-token"

    def verify_identity(self, configuration: GoogleOidcConfiguration, token: str, nonce: str) -> GoogleIdentity:
        assert configuration == CONFIGURATION
        self.verified.append((token, nonce))
        return GoogleIdentity("google-subject", "person@example.test", "Person", None)


def test_login_state_and_nonce_are_unique_short_lived_and_single_use() -> None:
    repository = FakeRepository()
    oidc = FakeOidcClient()
    service = AuthService(repository, oidc)  # type: ignore[arg-type]

    first = service.begin_login(NOW)
    second = service.begin_login(NOW)
    _, session_token, expires_at = service.complete_login(CONFIGURATION, state=first.state, code="code", now=NOW)

    assert first.state != second.state
    assert first.nonce != second.nonce
    assert first.expires_at == NOW + LOGIN_LIFETIME
    assert oidc.verified == [("signed-id-token", first.nonce)]
    assert repository.created_session == (USER.id, session_token, NOW + SESSION_LIFETIME)
    assert expires_at == NOW + SESSION_LIFETIME
    with pytest.raises(AuthenticationFailed, match="state"):
        service.complete_login(CONFIGURATION, state=first.state, code="replayed", now=NOW)
    assert oidc.exchanged == ["code"]


def test_session_is_renewed_for_thirty_days_and_logout_revokes_only_the_present_token() -> None:
    repository = FakeRepository()
    service = AuthService(repository, FakeOidcClient())  # type: ignore[arg-type]

    assert service.current_user("opaque-token", NOW) == USER
    assert repository.renewed == ("opaque-token", NOW + SESSION_LIFETIME)
    service.logout("opaque-token")
    service.logout(None)

    assert repository.revoked == "opaque-token"


def test_verified_identity_requires_matching_nonce_and_verified_email() -> None:
    claims = {"sub": "subject", "email": "USER@EXAMPLE.TEST", "email_verified": True, "nonce": "expected"}

    assert _identity_from_claims(claims, "expected").email == "user@example.test"
    with pytest.raises(AuthenticationFailed, match="nonce"):
        _identity_from_claims(claims, "wrong")
    with pytest.raises(AuthenticationFailed, match="verified email"):
        _identity_from_claims({**claims, "email_verified": False}, "expected")
