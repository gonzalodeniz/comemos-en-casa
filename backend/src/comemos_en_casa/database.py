"""Database dependencies backed by a direct psycopg connection per request."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import psycopg

from .config import load_settings

CONNECTION_ATTEMPTS = 2
_TRANSIENT_DATABASE_ERRORS = (
    psycopg.InterfaceError,
    psycopg.OperationalError,
    psycopg.errors.DeadlockDetected,
    psycopg.errors.SerializationFailure,
)


class TransientDatabaseError(RuntimeError):
    """Raised after bounded fresh-connection retries cannot reach PostgreSQL."""


def is_transient_database_error(error: BaseException) -> bool:
    """Report whether a database exception may succeed on a fresh connection."""
    return isinstance(error, _TRANSIENT_DATABASE_ERRORS)


def connect_with_retry() -> Any:
    """Open a direct connection, retrying transient connection failures once."""
    for attempt in range(CONNECTION_ATTEMPTS):
        try:
            return psycopg.connect(load_settings().database_url)
        except _TRANSIENT_DATABASE_ERRORS as error:
            if attempt + 1 == CONNECTION_ATTEMPTS:
                raise TransientDatabaseError("database connection is temporarily unavailable") from error
    raise AssertionError("connection retry loop must either return or raise")


def get_connection() -> Generator[Any, None, None]:
    """Open and close one direct PostgreSQL connection for each consuming request."""
    with connect_with_retry() as connection:
        yield connection
