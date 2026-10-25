"""Pure date calculations for meal-planning operations."""

from datetime import date, datetime, timedelta


def annual_maximum_end_date(start_date: date) -> date:
    """Return the inclusive last date allowed by the one-calendar-year limit."""
    _validate_date(start_date, "start_date")

    if start_date.year == date.max.year:
        return date.max

    if start_date.month == 2 and start_date.day == 29:
        return date(start_date.year + 1, 2, 28)

    anniversary = start_date.replace(year=start_date.year + 1)
    return anniversary - timedelta(days=1)


def repetition_dates(
    start_date: date, *, interval_weeks: int, end_date: date
) -> list[date]:
    """Return dates at N-week intervals, including the start and matching end."""
    _validate_date(start_date, "start_date")
    _validate_date(end_date, "end_date")

    if type(interval_weeks) is not int or interval_weeks <= 0:
        raise ValueError("interval_weeks must be a positive integer")

    maximum_end = annual_maximum_end_date(start_date)
    if end_date < start_date or end_date > maximum_end:
        raise ValueError("end_date must be between start_date and its annual limit")

    span_days = (end_date - start_date).days
    if interval_weeks > span_days // 7:
        return [start_date]

    step_days = interval_weeks * 7
    occurrences = [start_date]
    offset_days = step_days
    while offset_days <= span_days:
        occurrences.append(start_date + timedelta(days=offset_days))
        offset_days += step_days
    return occurrences


def _validate_date(value: object, field_name: str) -> None:
    if not isinstance(value, date) or isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a calendar date")
