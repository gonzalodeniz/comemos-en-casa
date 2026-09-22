from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
import sys
from uuid import UUID

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.meal_calendar.service import (
    current_week_start,
    occurrence_in_week,
    validate_week_start,
    week_dates,
)
from comemos_en_casa.meal_calendar.settings import CANARY_TIMEZONE
from comemos_en_casa.meal_calendar.schemas import (
    AssignmentDraft,
    MealCalendarValidationError,
    RecurrenceRule,
    RecurrenceRuleDraft,
    RECURRENCE_INTERVALS,
    normalize_free_text,
)


def test_current_week_start_uses_the_canary_date_at_utc_midnight() -> None:
    instant = datetime(2025, 1, 1, 0, 30, tzinfo=timezone.utc)

    assert current_week_start(instant, timezone=CANARY_TIMEZONE) == datetime(2024, 12, 30).date()


def test_normalize_free_text_normalizes_trims_and_removes_html() -> None:
    assert normalize_free_text("  Cafe\u0301 <b>hoy</b>  ") == "Café hoy"


def test_current_week_start_handles_the_canary_dst_transition() -> None:
    before_jump = datetime(2025, 3, 30, 0, 30, tzinfo=timezone.utc)
    after_jump = datetime(2025, 3, 30, 1, 30, tzinfo=timezone.utc)

    assert current_week_start(before_jump, timezone=CANARY_TIMEZONE) == datetime(2025, 3, 24).date()
    assert current_week_start(after_jump, timezone=CANARY_TIMEZONE) == datetime(2025, 3, 24).date()


def test_week_dates_accepts_monday_and_returns_a_monday_to_sunday_range() -> None:
    monday = datetime(2025, 6, 2).date()

    assert validate_week_start(monday) == monday
    assert week_dates(monday) == tuple(datetime(2025, 6, day).date() for day in range(2, 9))


def test_week_dates_rejects_a_non_monday_start() -> None:
    with pytest.raises(MealCalendarValidationError, match="Monday"):
        week_dates(datetime(2025, 6, 3).date())


def test_normalize_free_text_rejects_whitespace_only_values() -> None:
    with pytest.raises(MealCalendarValidationError, match="free text"):
        normalize_free_text("   ")


def test_normalize_free_text_counts_unicode_code_points_after_sanitizing_html() -> None:
    value = "<i>" + ("😀" * 100) + "</i>"

    assert normalize_free_text(value) == "😀" * 100
    with pytest.raises(MealCalendarValidationError, match="1 to 100"):
        normalize_free_text("😀" * 101)


def test_normalize_free_text_leaves_html_content_as_plain_text() -> None:
    assert normalize_free_text("<script>alert(1)</script><strong> cena</strong>") == "alert(1) cena"


def test_assignment_draft_enforces_the_slot_kind_and_value_combination() -> None:
    recipe_id = UUID("a756d3e5-6f90-478e-a2f6-3a5eedf40a4f")
    recipe = AssignmentDraft.create(
        meal_date=datetime(2025, 6, 2).date(),
        slot="lunch",
        kind="recipe",
        recipe_id=recipe_id,
    )
    text = AssignmentDraft.create(
        meal_date=datetime(2025, 6, 2).date(),
        slot="dinner",
        kind="free_text",
        free_text="  Sopa  ",
    )

    assert recipe.recipe_id == recipe_id
    assert recipe.free_text is None
    assert text.recipe_id is None
    assert text.free_text == "Sopa"
    with pytest.raises(MealCalendarValidationError, match="slot"):
        AssignmentDraft.create(
            meal_date=datetime(2025, 6, 2).date(),
            slot="breakfast",
            kind="free_text",
            free_text="Sopa",
        )
    with pytest.raises(MealCalendarValidationError, match="recipe assignments"):
        AssignmentDraft.create(
            meal_date=datetime(2025, 6, 2).date(),
            slot="lunch",
            kind="recipe",
            free_text="not allowed",
        )


def test_assignment_draft_rejects_a_recipe_value_that_is_not_a_uuid() -> None:
    with pytest.raises(MealCalendarValidationError, match="recipe id"):
        AssignmentDraft.create(
            meal_date=datetime(2025, 6, 2).date(),
            slot="lunch",
            kind="recipe",
            recipe_id="a756d3e5-6f90-478e-a2f6-3a5eedf40a4f",  # type: ignore[arg-type]
        )


def test_recurrence_rule_draft_normalizes_free_text_and_rejects_no_repeat_value() -> None:
    assert RECURRENCE_INTERVALS == frozenset({1, 2, 3, 4})
    draft = RecurrenceRuleDraft.create(
        initial_date=datetime(2026, 9, 16).date(),
        slot="lunch",
        free_text="  Café <strong>hoy</strong>  ",
        interval_weeks=2,
    )

    assert draft.initial_date == datetime(2026, 9, 16).date()
    assert draft.slot == "lunch"
    assert draft.free_text == "Café hoy"
    assert draft.interval_weeks == 2
    rule = RecurrenceRule.create(
        id=UUID("a756d3e5-6f90-478e-a2f6-3a5eedf40a4f"),
        initial_date=draft.initial_date,
        slot=draft.slot,
        free_text=draft.free_text,
        interval_weeks=draft.interval_weeks,
    )
    assert rule.series_id == rule.id
    assert rule.calendar_key == "shared"

    with pytest.raises(MealCalendarValidationError, match="interval"):
        RecurrenceRuleDraft.create(
            initial_date=datetime(2026, 9, 16).date(),
            slot="lunch",
            free_text="Sopa",
            interval_weeks=0,
        )


def test_recurrence_rule_draft_rejects_recipe_values_invalid_dates_slots_and_intervals() -> None:
    with pytest.raises(MealCalendarValidationError, match="free-text"):
        RecurrenceRuleDraft.create(
            initial_date=datetime(2026, 9, 16).date(),
            slot="lunch",
            free_text="Sopa",
            interval_weeks=1,
            recipe_id=UUID("a756d3e5-6f90-478e-a2f6-3a5eedf40a4f"),
        )
    with pytest.raises(MealCalendarValidationError, match="free text"):
        RecurrenceRuleDraft.create(
            initial_date=datetime(2026, 9, 16).date(),
            slot="lunch",
            free_text="   ",
            interval_weeks=1,
        )
    with pytest.raises(MealCalendarValidationError, match="date"):
        RecurrenceRuleDraft.create(
            initial_date=datetime(2026, 9, 16, 12, 0),  # type: ignore[arg-type]
            slot="lunch",
            free_text="Sopa",
            interval_weeks=1,
        )
    with pytest.raises(MealCalendarValidationError, match="slot"):
        RecurrenceRuleDraft.create(
            initial_date=datetime(2026, 9, 16).date(),
            slot="breakfast",
            free_text="Sopa",
            interval_weeks=1,
        )
    with pytest.raises(MealCalendarValidationError, match="interval"):
        RecurrenceRuleDraft.create(
            initial_date=datetime(2026, 9, 16).date(),
            slot="lunch",
            free_text="Sopa",
            interval_weeks=5,
        )


def _rule(*, initial_date: str, interval_weeks: int) -> RecurrenceRule:
    return RecurrenceRule.create(
        id=UUID("a756d3e5-6f90-478e-a2f6-3a5eedf40a4f"),
        initial_date=datetime.fromisoformat(initial_date).date(),
        slot="lunch",
        free_text="Sopa",
        interval_weeks=interval_weeks,
    )


def test_occurrence_in_week_includes_both_boundaries_and_preserves_the_weekday() -> None:
    week_start = datetime(2026, 9, 14).date()
    week_end = week_dates(week_start)[-1]

    assert (
        occurrence_in_week(_rule(initial_date="2026-09-14", interval_weeks=1), week_start, week_end)
        == week_start
    )
    assert (
        occurrence_in_week(_rule(initial_date="2026-09-20", interval_weeks=1), week_start, week_end)
        == week_end
    )
    assert occurrence_in_week(
        _rule(initial_date="2026-09-16", interval_weeks=2),
        datetime(2026, 9, 21).date(),
        datetime(2026, 9, 27).date(),
    ) is None
    assert occurrence_in_week(
        _rule(initial_date="2026-09-16", interval_weeks=2),
        datetime(2026, 9, 28).date(),
        datetime(2026, 10, 4).date(),
    ) == datetime(2026, 9, 30).date()


def test_occurrence_in_week_handles_all_intervals_month_year_crossings_and_future_anchors() -> None:
    week_start = datetime(2026, 2, 2).date()
    week_end = week_dates(week_start)[-1]

    assert (
        occurrence_in_week(_rule(initial_date="2026-01-05", interval_weeks=4), week_start, week_end)
        == week_start
    )
    assert (
        occurrence_in_week(_rule(initial_date="2025-12-29", interval_weeks=1), week_start, week_end)
        == week_start
    )
    assert occurrence_in_week(
        _rule(initial_date="2026-02-09", interval_weeks=1), week_start, week_end
    ) is None
    assert [
        occurrence_in_week(
            _rule(initial_date="2026-01-05", interval_weeks=interval), week_start, week_end
        )
        for interval in range(1, 5)
    ] == [datetime(2026, 2, 2).date(), datetime(2026, 2, 2).date(), None, datetime(2026, 2, 2).date()]


def test_occurrence_in_week_rejects_non_inclusive_monday_to_sunday_ranges() -> None:
    monday = date(2026, 9, 14)
    rule = _rule(initial_date="2026-09-16", interval_weeks=1)

    with pytest.raises(MealCalendarValidationError, match="Monday"):
        occurrence_in_week(rule, date(2026, 9, 15), date(2026, 9, 21))
    with pytest.raises(MealCalendarValidationError, match="Sunday"):
        occurrence_in_week(rule, monday, date(2026, 9, 19))
