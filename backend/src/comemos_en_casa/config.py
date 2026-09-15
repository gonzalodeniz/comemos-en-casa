"""Process configuration for the application."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


class ConfigurationError(ValueError):
    """Raised when required process configuration is absent or invalid."""


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from the process environment."""

    database_url: str


def load_settings(environment: Mapping[str, str] | None = None) -> Settings:
    """Load required application settings without providing deployment defaults."""
    values = os.environ if environment is None else environment
    database_url = values.get("DATABASE_URL", "").strip()
    if not database_url:
        raise ConfigurationError("DATABASE_URL must be set")
    return Settings(database_url=database_url)
