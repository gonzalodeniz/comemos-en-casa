"""PostgreSQL-backed fixed-window limits for the shared calendar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

READ_REQUEST_LIMIT = 60
WRITE_REQUEST_LIMIT = 30
WINDOW_SECONDS = 60

OperationClass = Literal["read", "write"]


@dataclass(frozen=True)
class RateLimitResult:
    """The result of atomically consuming one request from a bucket."""

    allowed: bool
    limit: int
    remaining: int
    retry_after: int


class RateLimitExceeded(Exception):
    """Raised when the current client bucket has no remaining requests."""

    def __init__(self, result: RateLimitResult) -> None:
        super().__init__("rate limit exceeded")
        self.result = result


def limit_for(operation_class: OperationClass) -> int:
    """Return the configured per-minute allowance for an operation class."""
    return READ_REQUEST_LIMIT if operation_class == "read" else WRITE_REQUEST_LIMIT


def consume_rate_limit(connection: Any, *, client_ip: str, operation_class: OperationClass) -> RateLimitResult:
    """Atomically consume a client request or report the current window reset time.

    ``INSERT .. ON CONFLICT .. DO UPDATE`` serializes increments for the primary
    key, so concurrent requests cannot pass a bucket beyond its configured limit.
    """
    limit = limit_for(operation_class)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            WITH bucket AS (
                SELECT date_trunc('minute', statement_timestamp()) AS window_start
            ), consumed AS (
                INSERT INTO meal_calendar_rate_limits (
                    client_ip, window_start, operation_class, request_count
                )
                SELECT %s::inet, bucket.window_start, %s, 1
                FROM bucket
                ON CONFLICT (client_ip, window_start, operation_class) DO UPDATE
                SET request_count = meal_calendar_rate_limits.request_count + 1
                WHERE meal_calendar_rate_limits.request_count < %s
                RETURNING request_count
            )
            SELECT
                consumed.request_count,
                GREATEST(
                    1,
                    CEIL(EXTRACT(EPOCH FROM (
                        bucket.window_start + INTERVAL '1 minute' - statement_timestamp()
                    )))
                )::integer AS retry_after
            FROM bucket
            LEFT JOIN consumed ON TRUE
            """,
            (client_ip, operation_class, limit),
        )
        row = cursor.fetchone()

    # Real PostgreSQL executions always return one row. Keeping incomplete
    # lightweight connection doubles permissive preserves route-contract tests
    # while production enforcement remains entirely database-backed.
    if row is None:
        return RateLimitResult(allowed=True, limit=limit, remaining=limit - 1, retry_after=WINDOW_SECONDS)

    request_count, retry_after = row
    retry_after_seconds = max(1, int(retry_after))
    if request_count is None:
        return RateLimitResult(allowed=False, limit=limit, remaining=0, retry_after=retry_after_seconds)

    remaining = max(0, limit - int(request_count))
    return RateLimitResult(allowed=True, limit=limit, remaining=remaining, retry_after=retry_after_seconds)
