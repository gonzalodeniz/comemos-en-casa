"""Validated values shared by future calendar service and repository layers."""

from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
from typing import Literal
from unicodedata import normalize
from uuid import UUID

CALENDAR_KEY = "shared"
MEAL_SLOTS = frozenset({"lunch", "dinner"})
ASSIGNMENT_KINDS = frozenset({"recipe", "free_text"})
FREE_TEXT_MIN_CODE_POINTS = 1
FREE_TEXT_MAX_CODE_POINTS = 100


class MealCalendarValidationError(ValueError):
    """Raised when a value cannot satisfy the meal-calendar domain contract."""


class _TextOnlySanitizer(HTMLParser):
    """Discard markup while retaining its human-readable text content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    @property
    def text(self) -> str:
        return "".join(self.parts)


def normalize_free_text(value: str) -> str:
    """Return NFC, text-only free text with one to 100 Unicode code points."""
    if not isinstance(value, str):
        raise MealCalendarValidationError("free text must be a string")

    sanitizer = _TextOnlySanitizer()
    sanitizer.feed(value)
    sanitizer.close()
    cleaned = normalize("NFC", sanitizer.text).strip()

    if not FREE_TEXT_MIN_CODE_POINTS <= len(cleaned) <= FREE_TEXT_MAX_CODE_POINTS:
        raise MealCalendarValidationError("free text must contain 1 to 100 code points")
    return cleaned


@dataclass(frozen=True)
class AssignmentDraft:
    """A validated assignment ready for persistence, without persistence behavior."""

    meal_date: date
    slot: Literal["lunch", "dinner"]
    kind: Literal["recipe", "free_text"]
    recipe_id: UUID | None = None
    free_text: str | None = None

    @classmethod
    def create(
        cls,
        *,
        meal_date: date,
        slot: str,
        kind: str,
        recipe_id: UUID | None = None,
        free_text: str | None = None,
    ) -> "AssignmentDraft":
        if isinstance(meal_date, datetime) or not isinstance(meal_date, date):
            raise MealCalendarValidationError("meal date must be a date")
        if slot not in MEAL_SLOTS:
            raise MealCalendarValidationError("slot must be lunch or dinner")
        if kind not in ASSIGNMENT_KINDS:
            raise MealCalendarValidationError("kind must be recipe or free_text")

        if kind == "recipe":
            if not isinstance(recipe_id, UUID) or free_text is not None:
                raise MealCalendarValidationError("recipe assignments require a UUID recipe id and no free text")
            return cls(meal_date, slot, kind, recipe_id=recipe_id)

        if recipe_id is not None or free_text is None:
            raise MealCalendarValidationError("free-text assignments require only free text")
        return cls(meal_date, slot, kind, free_text=normalize_free_text(free_text))
