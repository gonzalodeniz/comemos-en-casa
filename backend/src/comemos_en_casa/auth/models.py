"""Authentication domain models with no HTTP or database dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class User:
    """The local account linked to a verified Google OpenID Connect subject."""

    id: UUID
    google_subject: str
    email: str
    display_name: str | None
    picture_url: str | None


@dataclass(frozen=True)
class GoogleIdentity:
    """Claims accepted from a verified Google OpenID Connect ID token."""

    subject: str
    email: str
    display_name: str | None
    picture_url: str | None


@dataclass(frozen=True)
class LoginAttempt:
    """One short-lived, single-use authorization-code exchange attempt."""

    state: str
    nonce: str
    expires_at: datetime
