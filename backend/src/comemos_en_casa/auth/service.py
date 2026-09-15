"""Google OpenID Connect and opaque PostgreSQL session services."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
import json
import secrets
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen
from uuid import UUID, uuid4

from .models import GoogleIdentity, LoginAttempt, User

GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
LOGIN_LIFETIME = timedelta(minutes=10)
SESSION_LIFETIME = timedelta(days=30)


class AuthenticationError(RuntimeError):
    """Raised when a request has no valid authenticated user."""


class AuthenticationFailed(AuthenticationError):
    """Raised when an OAuth callback cannot establish a safe session."""


@dataclass(frozen=True)
class GoogleOidcConfiguration:
    """Non-secret OIDC wiring plus the process-supplied client secret."""

    client_id: str
    client_secret: str
    redirect_uri: str


class AuthRepository:
    """Persistence operations for single-use login attempts and opaque sessions."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def create_login_attempt(self, attempt: LoginAttempt) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO auth_sessions (id, state_hash, oauth_nonce, expires_at)
                VALUES (%s, %s, %s, %s)
                """,
                (uuid4(), _hash_token(attempt.state), attempt.nonce, attempt.expires_at),
            )

    def consume_login_attempt(self, state: str, now: datetime) -> str | None:
        """Atomically consume a non-expired state and return its expected nonce."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM auth_sessions
                WHERE state_hash = %s
                  AND user_id IS NULL
                  AND expires_at > %s
                RETURNING oauth_nonce
                """,
                (_hash_token(state), now),
            )
            row = cursor.fetchone()
        return None if row is None else str(row[0])

    def upsert_user(self, identity: GoogleIdentity) -> User:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (id, google_subject, email, display_name, picture_url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (google_subject) DO UPDATE
                SET email = EXCLUDED.email,
                    display_name = EXCLUDED.display_name,
                    picture_url = EXCLUDED.picture_url,
                    updated_at = now()
                RETURNING id, google_subject, email, display_name, picture_url
                """,
                (uuid4(), identity.subject, identity.email, identity.display_name, identity.picture_url),
            )
            row = cursor.fetchone()
        assert row is not None
        return User(id=row[0], google_subject=row[1], email=row[2], display_name=row[3], picture_url=row[4])

    def create_session(self, user_id: UUID, raw_token: str, expires_at: datetime) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO auth_sessions (id, user_id, session_token_hash, expires_at)
                VALUES (%s, %s, %s, %s)
                """,
                (uuid4(), user_id, _hash_token(raw_token), expires_at),
            )

    def find_user_for_session(self, raw_token: str, now: datetime) -> User | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT users.id, users.google_subject, users.email, users.display_name, users.picture_url
                FROM auth_sessions
                JOIN users ON users.id = auth_sessions.user_id
                WHERE auth_sessions.session_token_hash = %s
                  AND auth_sessions.expires_at > %s
                """,
                (_hash_token(raw_token), now),
            )
            row = cursor.fetchone()
        return None if row is None else User(id=row[0], google_subject=row[1], email=row[2], display_name=row[3], picture_url=row[4])

    def renew_session(self, raw_token: str, expires_at: datetime) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE auth_sessions
                SET expires_at = %s, last_seen_at = now()
                WHERE session_token_hash = %s AND user_id IS NOT NULL
                """,
                (expires_at, _hash_token(raw_token)),
            )

    def revoke_session(self, raw_token: str) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute("DELETE FROM auth_sessions WHERE session_token_hash = %s", (_hash_token(raw_token),))


class GoogleOpenIdClient:
    """Small adapter around Google's OIDC authorization, token, and verification endpoints."""

    def authorization_url(self, configuration: GoogleOidcConfiguration, attempt: LoginAttempt) -> str:
        query = urlencode(
            {
                "client_id": configuration.client_id,
                "redirect_uri": configuration.redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": attempt.state,
                "nonce": attempt.nonce,
            }
        )
        return f"{GOOGLE_AUTHORIZATION_ENDPOINT}?{query}"

    def exchange_code(self, configuration: GoogleOidcConfiguration, code: str) -> str:
        body = urlencode(
            {
                "code": code,
                "client_id": configuration.client_id,
                "client_secret": configuration.client_secret,
                "redirect_uri": configuration.redirect_uri,
                "grant_type": "authorization_code",
            }
        ).encode()
        request = UrlRequest(GOOGLE_TOKEN_ENDPOINT, data=body, method="POST")
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with urlopen(request, timeout=10) as response:  # nosec B310: fixed Google endpoint
                payload = json.loads(response.read())
        except (OSError, ValueError) as error:
            raise AuthenticationFailed("Google token exchange failed") from error
        token = payload.get("id_token")
        if not isinstance(token, str) or not token:
            raise AuthenticationFailed("Google did not return an ID token")
        return token

    def verify_identity(self, configuration: GoogleOidcConfiguration, token: str, nonce: str) -> GoogleIdentity:
        try:
            # Imported here so an unconfigured application can still start and report
            # its configuration status without treating a package install as a secret.
            from google.auth.transport.requests import Request as GoogleRequest
            from google.oauth2 import id_token

            claims = id_token.verify_oauth2_token(token, GoogleRequest(), configuration.client_id)
        except Exception as error:  # Google owns token parsing and may raise several typed errors.
            raise AuthenticationFailed("Google ID token verification failed") from error
        return _identity_from_claims(claims, nonce)


class AuthService:
    """Coordinate OIDC verification with persistence while retaining only opaque session tokens."""

    def __init__(self, repository: AuthRepository, oidc_client: GoogleOpenIdClient | None = None) -> None:
        self._repository = repository
        self._oidc_client = oidc_client or GoogleOpenIdClient()

    def begin_login(self, now: datetime | None = None) -> LoginAttempt:
        now = _utc_now() if now is None else now
        attempt = LoginAttempt(
            state=secrets.token_urlsafe(32),
            nonce=secrets.token_urlsafe(32),
            expires_at=now + LOGIN_LIFETIME,
        )
        self._repository.create_login_attempt(attempt)
        return attempt

    def authorization_url(self, configuration: GoogleOidcConfiguration, attempt: LoginAttempt) -> str:
        """Build the Google redirect only from the configured OIDC client and fresh attempt."""
        return self._oidc_client.authorization_url(configuration, attempt)

    def complete_login(
        self,
        configuration: GoogleOidcConfiguration,
        *,
        state: str,
        code: str,
        now: datetime | None = None,
    ) -> tuple[User, str, datetime]:
        now = _utc_now() if now is None else now
        nonce = self._repository.consume_login_attempt(state, now)
        if nonce is None:
            raise AuthenticationFailed("OAuth state is invalid or expired")
        token = self._oidc_client.exchange_code(configuration, code)
        identity = self._oidc_client.verify_identity(configuration, token, nonce)
        user = self._repository.upsert_user(identity)
        session_token = secrets.token_urlsafe(32)
        expires_at = now + SESSION_LIFETIME
        self._repository.create_session(user.id, session_token, expires_at)
        return user, session_token, expires_at

    def current_user(self, session_token: str | None, now: datetime | None = None) -> User:
        if not session_token:
            raise AuthenticationError("Authentication is required")
        now = _utc_now() if now is None else now
        user = self._repository.find_user_for_session(session_token, now)
        if user is None:
            raise AuthenticationError("Authentication is required")
        self._repository.renew_session(session_token, now + SESSION_LIFETIME)
        return user

    def logout(self, session_token: str | None) -> None:
        if session_token:
            self._repository.revoke_session(session_token)


def _identity_from_claims(claims: Mapping[str, object], nonce: str) -> GoogleIdentity:
    subject = claims.get("sub")
    email = claims.get("email")
    verified = claims.get("email_verified")
    token_nonce = claims.get("nonce")
    if not isinstance(subject, str) or not subject:
        raise AuthenticationFailed("Google ID token has no subject")
    if not isinstance(email, str) or not email.strip() or verified is not True:
        raise AuthenticationFailed("Google ID token has no verified email")
    if not isinstance(token_nonce, str) or not hmac.compare_digest(token_nonce, nonce):
        raise AuthenticationFailed("Google ID token nonce does not match")
    name = claims.get("name")
    picture = claims.get("picture")
    return GoogleIdentity(
        subject=subject,
        email=email.strip().lower(),
        display_name=name if isinstance(name, str) and name else None,
        picture_url=picture if isinstance(picture, str) and picture else None,
    )


def _hash_token(value: str) -> str:
    """Hash a browser- or callback-held bearer value before persistence or lookup."""
    return sha256(value.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
