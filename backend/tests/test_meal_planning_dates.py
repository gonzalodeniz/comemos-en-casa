from datetime import date

import pytest

from app.meal_planning import annual_maximum_end_date, repetition_dates


@pytest.mark.parametrize(
    ("start", "expected"),
    [
        (date(2026, 11, 2), date(2027, 11, 1)),
        (date(2028, 2, 29), date(2029, 2, 28)),
        (date(2027, 2, 28), date(2028, 2, 27)),
    ],
)
def test_annual_maximum_end_date(start, expected):
    assert annual_maximum_end_date(start) == expected


def test_leap_start_52_week_repetition_stops_at_last_occurrence_before_maximum():
    start = date(2028, 2, 29)
    maximum_end = date(2029, 2, 28)

    assert annual_maximum_end_date(start) == maximum_end
    assert repetition_dates(
        start, interval_weeks=52, end_date=maximum_end
    ) == [date(2028, 2, 29), date(2029, 2, 27)]


def test_weekly_repetition_includes_matching_user_selected_end_date():
    assert repetition_dates(
        date(2026, 11, 2), interval_weeks=1, end_date=date(2026, 11, 30)
    ) == [
        date(2026, 11, 2),
        date(2026, 11, 9),
        date(2026, 11, 16),
        date(2026, 11, 23),
        date(2026, 11, 30),
    ]


def test_repetition_can_include_ordinary_annual_maximum_when_it_matches():
    start = date(2026, 11, 2)
    assert annual_maximum_end_date(start) == date(2027, 11, 1)
    occurrences = repetition_dates(
        start, interval_weeks=1, end_date=annual_maximum_end_date(start)
    )
    assert occurrences[-1] == date(2027, 11, 1)


def test_repetition_does_not_add_non_matching_end_date():
    assert repetition_dates(
        date(2026, 11, 2), interval_weeks=1, end_date=date(2026, 11, 29)
    ) == [
        date(2026, 11, 2),
        date(2026, 11, 9),
        date(2026, 11, 16),
        date(2026, 11, 23),
    ]


def test_start_date_equal_to_end_date_creates_one_occurrence():
    start = date(2026, 11, 2)
    assert repetition_dates(start, interval_weeks=1, end_date=start) == [start]


@pytest.mark.parametrize("interval_weeks", [True, False, 0, -1, 1.5, "2", None])
def test_repetition_rejects_non_positive_or_non_integer_intervals(interval_weeks):
    with pytest.raises(ValueError):
        repetition_dates(
            date(2026, 11, 2),
            interval_weeks=interval_weeks,
            end_date=date(2026, 11, 30),
        )


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (date(2026, 11, 2), date(2026, 11, 1)),
        (date(2026, 11, 2), date(2027, 11, 2)),
        (date(2028, 2, 29), date(2029, 3, 1)),
    ],
)
def test_repetition_rejects_end_dates_outside_valid_window(start, end):
    with pytest.raises(ValueError):
        repetition_dates(start, interval_weeks=1, end_date=end)


def test_historical_start_anchors_annual_window_to_selected_date():
    start = date(2020, 1, 1)
    assert annual_maximum_end_date(start) == date(2020, 12, 31)
    assert repetition_dates(
        start, interval_weeks=26, end_date=date(2020, 12, 31)
    ) == [date(2020, 1, 1), date(2020, 7, 1), date(2020, 12, 30)]


def test_large_interval_stops_after_start_without_overflow():
    start = date(2026, 11, 2)
    assert repetition_dates(
        start, interval_weeks=10**100, end_date=date(2027, 11, 1)
    ) == [start]


def test_annual_maximum_rejects_datetime_input():
    from datetime import datetime

    with pytest.raises(ValueError):
        annual_maximum_end_date(datetime(2026, 11, 2))


def test_date_max_year_uses_last_representable_calendar_date():
    assert annual_maximum_end_date(date.max) == date.max
