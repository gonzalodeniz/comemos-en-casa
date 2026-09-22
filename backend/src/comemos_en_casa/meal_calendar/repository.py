"""PostgreSQL persistence for the shared meal calendar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from .schemas import AssignmentDraft, CALENDAR_KEY, RecurrenceRule, RecurrenceRuleDraft
from .service import occurrence_in_week


@dataclass(frozen=True)
class CalendarAssignment:
    """One calendar entry with its current public recipe presentation."""

    id: UUID | str
    meal_date: date
    slot: str
    kind: str
    recipe_id: UUID | None
    free_text: str | None
    recipe_title: str | None
    recipe_image_url: str | None
    entry_type: str = "assignment"
    series_id: UUID | None = None
    occurrence_date: date | None = None
    initial_date: date | None = None
    recurrence_weeks: int | None = None

    @property
    def visible_text(self) -> str:
        """Return the presentation text used for the shared ordering contract."""
        if self.kind == "free_text":
            return self.free_text or ""
        return self.recipe_title or "Receta no disponible"

    def matches(self, draft: AssignmentDraft) -> bool:
        """Report whether this persisted value is the same idempotent create payload."""
        return (
            self.meal_date == draft.meal_date
            and self.slot == draft.slot
            and self.kind == draft.kind
            and self.recipe_id == draft.recipe_id
            and self.free_text == draft.free_text
        )


class MealCalendarRepository:
    """Execute shared-calendar SQL through a caller-owned connection."""

    _SELECT_ASSIGNMENT = """
        SELECT
            assignments.id,
            assignments.meal_date,
            assignments.meal_slot,
            assignments.assignment_kind,
            assignments.recipe_id,
            assignments.free_text,
            recipes.title,
            recipes.image_url
        FROM meal_assignments AS assignments
        LEFT JOIN recipes ON recipes.id = assignments.recipe_id
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def list_week(self, week_start: date, week_end: date) -> list[CalendarAssignment]:
        """Return ordinary assignments and virtual recurrence occurrences for a week."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                self._SELECT_ASSIGNMENT
                + """
                WHERE assignments.calendar_key = %s
                  AND assignments.meal_date BETWEEN %s AND %s
                """,
                (CALENDAR_KEY, week_start, week_end),
            )
            entries = [self._restore(row) for row in cursor.fetchall()]

        for rule in self.list_recurrence_candidates(week_end):
            occurrence_date = occurrence_in_week(rule, week_start, week_end)
            if occurrence_date is not None:
                entries.append(self._occurrence(rule, occurrence_date))

        slot_order = {"lunch": 0, "dinner": 1}
        return sorted(
            entries,
            key=lambda entry: (
                entry.meal_date,
                slot_order[entry.slot],
                self._entry_sort_key(entry),
                str(entry.id),
            ),
        )

    def find_rule_by_id(self, series_id: UUID) -> RecurrenceRule | None:
        """Return one shared recurrence rule, if it still exists."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, initial_date, meal_slot, free_text, interval_weeks
                FROM meal_recurrence_rules
                WHERE id = %s AND calendar_key = %s
                """,
                (series_id, CALENDAR_KEY),
            )
            row = cursor.fetchone()
        return None if row is None else self._restore_rule(row)

    def list_recurrence_candidates(self, week_end: date) -> list[RecurrenceRule]:
        """Return shared rules that can contribute an occurrence by ``week_end``."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, initial_date, meal_slot, free_text, interval_weeks
                FROM meal_recurrence_rules
                WHERE calendar_key = %s AND initial_date <= %s
                """,
                (CALENDAR_KEY, week_end),
            )
            rows = cursor.fetchall()
        return [self._restore_rule(row) for row in rows if len(row) == 5]

    def insert_rule(self, series_id: UUID, draft: RecurrenceRuleDraft) -> bool:
        """Insert one rule without committing; return false when its UUID exists."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO meal_recurrence_rules (
                    id, calendar_key, initial_date, meal_slot, free_text, interval_weeks
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                RETURNING id
                """,
                (
                    series_id,
                    CALENDAR_KEY,
                    draft.initial_date,
                    draft.slot,
                    draft.free_text,
                    draft.interval_weeks,
                ),
            )
            return cursor.fetchone() is not None

    def update_rule(self, series_id: UUID, draft: RecurrenceRuleDraft) -> bool:
        """Update one shared rule without committing."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                "UPDATE meal_recurrence_rules\n"
                "SET initial_date = %s, meal_slot = %s, free_text = %s, interval_weeks = %s\n"
                "WHERE id = %s AND calendar_key = %s\n"
                "RETURNING id",
                (
                    draft.initial_date,
                    draft.slot,
                    draft.free_text,
                    draft.interval_weeks,
                    series_id,
                    CALENDAR_KEY,
                ),
            )
            return cursor.fetchone() is not None

    def delete_rule(self, series_id: UUID) -> bool:
        """Delete one shared rule without committing."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM meal_recurrence_rules WHERE id = %s AND calendar_key = %s RETURNING id",
                (series_id, CALENDAR_KEY),
            )
            return cursor.fetchone() is not None

    def find_by_id(self, assignment_id: UUID) -> CalendarAssignment | None:
        """Return one assignment and current recipe presentation, if it still exists."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                self._SELECT_ASSIGNMENT + " WHERE assignments.id = %s",
                (assignment_id,),
            )
            row = cursor.fetchone()
        return None if row is None else self._restore(row)

    def insert(self, assignment_id: UUID, draft: AssignmentDraft) -> bool:
        """Insert an assignment without committing; return false for an existing UUID."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO meal_assignments (
                    id, calendar_key, meal_date, meal_slot, assignment_kind, recipe_id, free_text
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                RETURNING id
                """,
                (
                    assignment_id,
                    CALENDAR_KEY,
                    draft.meal_date,
                    draft.slot,
                    draft.kind,
                    draft.recipe_id,
                    draft.free_text,
                ),
            )
            return cursor.fetchone() is not None

    def update(self, assignment_id: UUID, draft: AssignmentDraft) -> bool:
        """Replace mutable assignment fields while requiring its existing immutable kind."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE meal_assignments
                SET meal_date = %s, meal_slot = %s, recipe_id = %s, free_text = %s
                WHERE id = %s AND assignment_kind = %s
                RETURNING id
                """,
                (
                    draft.meal_date,
                    draft.slot,
                    draft.recipe_id,
                    draft.free_text,
                    assignment_id,
                    draft.kind,
                ),
            )
            return cursor.fetchone() is not None

    def delete(self, assignment_id: UUID) -> bool:
        """Delete only the requested assignment, never its referenced recipe."""
        with self._connection.cursor() as cursor:
            cursor.execute("DELETE FROM meal_assignments WHERE id = %s RETURNING id", (assignment_id,))
            return cursor.fetchone() is not None

    @staticmethod
    def _restore(row: tuple[Any, ...]) -> CalendarAssignment:
        return CalendarAssignment(
            id=row[0],
            meal_date=row[1],
            slot=row[2],
            kind=row[3],
            recipe_id=row[4],
            free_text=row[5],
            recipe_title=row[6],
            recipe_image_url=row[7],
        )

    @staticmethod
    def _restore_rule(row: tuple[Any, ...]) -> RecurrenceRule:
        return RecurrenceRule.create(
            id=row[0],
            initial_date=row[1],
            slot=row[2],
            free_text=row[3],
            interval_weeks=row[4],
        )

    @staticmethod
    def _occurrence(rule: RecurrenceRule, occurrence_date: date) -> CalendarAssignment:
        occurrence_id = f"series:{rule.series_id}:{occurrence_date.isoformat()}"
        return CalendarAssignment(
            id=occurrence_id,
            meal_date=occurrence_date,
            slot=rule.slot,
            kind="free_text",
            recipe_id=None,
            free_text=rule.free_text,
            recipe_title=None,
            recipe_image_url=None,
            entry_type="recurring_occurrence",
            series_id=rule.series_id,
            occurrence_date=occurrence_date,
            initial_date=rule.initial_date,
            recurrence_weeks=rule.interval_weeks,
        )

    @classmethod
    def _entry_sort_key(cls, entry: CalendarAssignment) -> tuple[int, str]:
        """Sort unavailable legacy recipes after readable meal text."""
        unavailable_recipe = entry.kind == "recipe" and entry.recipe_title is None
        return (1 if unavailable_recipe else 0, cls._sort_key(entry.visible_text))

    @staticmethod
    def _sort_key(value: str) -> str:
        """Match the catalogue's accent- and case-insensitive visible-text ordering."""
        from comemos_en_casa.recipes.schemas import normalize_title_search

        return normalize_title_search(value)
