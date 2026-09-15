"""Process configuration for the application."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


class ConfigurationError(ValueError):
    """Raised when required process configuration is absent or invalid."""


@dataclass(frozen=True)
class GoogleOidcSettings:
    """Google OIDC configuration supplied only through the process environment."""

    client_id: str
    client_secret: str
    redirect_uri: str


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from the process environment."""

    database_url: str
    enable_guest_user: bool
    frontend_url: str
    google_oidc: GoogleOidcSettings | None


def _load_boolean(values: Mapping[str, str], name: str, *, default: bool) -> bool:
    """Load an explicit boolean environment setting with a safe deployment default."""
    raw_value = values.get(name)
    if raw_value is None or not raw_value.strip():
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"{name} must be a boolean")


def _load_google_oidc(values: Mapping[str, str]) -> GoogleOidcSettings | None:
    """Load Google credentials as an all-or-nothing configuration unit."""
    names = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI")
    configured = {name: values.get(name, "").strip() for name in names}
    present = [name for name, value in configured.items() if value]
    if not present:
        return None
    if len(present) != len(names):
        raise ConfigurationError("GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI must be set together")
    if not configured["GOOGLE_REDIRECT_URI"].startswith(("https://", "http://localhost")):
        raise ConfigurationError("GOOGLE_REDIRECT_URI must use HTTPS (or localhost for development)")
    return GoogleOidcSettings(
        client_id=configured["GOOGLE_CLIENT_ID"],
        client_secret=configured["GOOGLE_CLIENT_SECRET"],
        redirect_uri=configured["GOOGLE_REDIRECT_URI"],
    )


def load_settings(environment: Mapping[str, str] | None = None) -> Settings:
    """Load required application settings without providing deployment defaults."""
    values = os.environ if environment is None else environment
    database_url = values.get("DATABASE_URL", "").strip()
    if not database_url:
        raise ConfigurationError("DATABASE_URL must be set")
    return Settings(
        database_url=database_url,
        # Shared calendar access remains usable before an auth integration exists.
        enable_guest_user=_load_boolean(values, "ENABLE_GUEST_USER", default=True),
        frontend_url=values.get("FRONTEND_URL", "http://localhost:5173").strip().rstrip("/"),
        google_oidc=_load_google_oidc(values),
    )
