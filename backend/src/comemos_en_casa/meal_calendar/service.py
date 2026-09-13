"""Temporal rules for calendar dates, independent of HTTP and persistence."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .schemas import MealCalendarValidationError
from .settings import CANARY_TIMEZONE


def current_week_start(instant: datetime, *, timezone: ZoneInfo = CANARY_TIMEZONE) -> date:
    """Return the Monday containing an aware instant in the supplied timezone."""
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise MealCalendarValidationError("instant must be timezone-aware")

    local_date = instant.astimezone(timezone).date()
    return local_date - timedelta(days=local_date.weekday())


def validate_week_start(value: date) -> date:
    """Accept only Monday ISO dates used as calendar-week boundaries."""
    if isinstance(value, datetime) or not isinstance(value, date):
        raise MealCalendarValidationError("week start must be a date")
    if value.weekday() != 0:
        raise MealCalendarValidationError("week start must be a Monday")
    return value


def week_dates(week_start: date) -> tuple[date, ...]:
    """Return the inclusive Monday-to-Sunday dates for a validated week."""
    monday = validate_week_start(week_start)
    return tuple(monday + timedelta(days=offset) for offset in range(7))
