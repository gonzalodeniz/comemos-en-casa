"""Pure domain rules for the shared meal calendar."""

from .catalog_adapter import MealCalendarCatalogueAdapter
from .repository import CalendarAssignment, MealCalendarRepository
from .schemas import AssignmentDraft, MealCalendarValidationError, normalize_free_text
from .service import current_week_start, validate_week_start, week_dates

__all__ = [
    "AssignmentDraft",
    "CalendarAssignment",
    "MealCalendarCatalogueAdapter",
    "MealCalendarRepository",
    "MealCalendarValidationError",
    "current_week_start",
    "normalize_free_text",
    "validate_week_start",
    "week_dates",
]
