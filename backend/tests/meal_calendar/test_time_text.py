from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from uuid import UUID

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.meal_calendar.service import current_week_start, validate_week_start, week_dates
from comemos_en_casa.meal_calendar.settings import CANARY_TIMEZONE
from comemos_en_casa.meal_calendar.schemas import (
    AssignmentDraft,
    MealCalendarValidationError,
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
