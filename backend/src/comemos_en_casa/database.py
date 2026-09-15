"""Database dependencies backed by a direct psycopg connection per request."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import psycopg

from .config import load_settings


def get_connection() -> Generator[Any, None, None]:
    """Open and close one PostgreSQL connection for each consuming request."""
    with psycopg.connect(load_settings().database_url) as connection:
        yield connection
