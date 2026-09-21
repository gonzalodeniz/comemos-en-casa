from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.meal_calendar.repository import MealCalendarRepository
from comemos_en_casa.meal_calendar.schemas import AssignmentDraft, RecurrenceRuleDraft


ASSIGNMENT_ID = UUID("00000000-0000-0000-0000-000000000001")
RECIPE_ID = UUID("00000000-0000-0000-0000-000000000002")
SERIES_ID = UUID("00000000-0000-0000-0000-000000000003")
SECOND_SERIES_ID = UUID("00000000-0000-0000-0000-000000000004")
THIRD_SERIES_ID = UUID("00000000-0000-0000-0000-000000000005")


class RecordingCursor:
    def __init__(self, *, rows: list[tuple[object, ...]] | None = None, row: tuple[object, ...] | None = None) -> None:
        self.rows = rows or []
        self.row = row
        self.calls: list[tuple[str, tuple[object, ...] | None]] = []

    def __enter__(self) -> "RecordingCursor":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        self.calls.append((query, params))

    def fetchall(self) -> list[tuple[object, ...]]:
        return self.rows

    def fetchone(self) -> tuple[object, ...] | None:
        return self.row


class RecordingConnection:
    def __init__(self, cursor: RecordingCursor) -> None:
        self.recording_cursor = cursor
        self.commit_calls = 0

    def cursor(self) -> RecordingCursor:
        return self.recording_cursor

    def commit(self) -> None:
        self.commit_calls += 1


class RecurrenceRecordingCursor(RecordingCursor):
    def __init__(
        self,
        *,
        assignment_rows: list[tuple[object, ...]],
        rule_rows: list[tuple[object, ...]],
    ) -> None:
        super().__init__(rows=assignment_rows)
        self.assignment_rows = assignment_rows
        self.rule_rows = rule_rows

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        super().execute(query, params)
        self.rows = self.rule_rows if "meal_recurrence_rules" in query else self.assignment_rows


def test_week_read_left_joins_current_recipes_and_orders_mixed_visible_text() -> None:
    first = UUID("00000000-0000-0000-0000-000000000010")
    second = UUID("00000000-0000-0000-0000-000000000011")
    cursor = RecordingCursor(
        rows=[
            (second, date(2025, 6, 2), "lunch", "recipe", RECIPE_ID, None, "Árbol", "https://example.test/a.jpg"),
            (first, date(2025, 6, 2), "lunch", "free_text", None, "avena", None, None),
            (ASSIGNMENT_ID, date(2025, 6, 2), "dinner", "recipe", None, None, None, None),
        ]
    )

    assignments = MealCalendarRepository(RecordingConnection(cursor)).list_week(date(2025, 6, 2), date(2025, 6, 8))

    assert [assignment.id for assignment in assignments] == [second, first, ASSIGNMENT_ID]
    query, params = cursor.calls[0]
    assert "LEFT JOIN recipes" in query
    assert "calendar_key = %s" in query
    assert params == ("shared", date(2025, 6, 2), date(2025, 6, 8))


def test_shared_recurrence_candidates_are_listed_without_future_rules() -> None:
    cursor = RecurrenceRecordingCursor(assignment_rows=[], rule_rows=[
        (SERIES_ID, date(2025, 6, 2), "lunch", "Sopa", 1),
    ])
    repository = MealCalendarRepository(RecordingConnection(cursor))

    candidates = repository.list_recurrence_candidates(date(2025, 6, 8))

    assert [rule.series_id for rule in candidates] == [SERIES_ID]
    query, params = cursor.calls[0]
    assert "FROM meal_recurrence_rules" in query
    assert "calendar_key = %s" in query
    assert "initial_date <= %s" in query
    assert params == ("shared", date(2025, 6, 8))


def test_week_read_combines_coexisting_rules_and_ordinary_recipe_rows_deterministically() -> None:
    unavailable_recipe_assignment = UUID("00000000-0000-0000-0000-000000000006")
    cursor = RecurrenceRecordingCursor(
        assignment_rows=[
            (ASSIGNMENT_ID, date(2025, 6, 2), "lunch", "free_text", None, "Arroz", None, None),
            (unavailable_recipe_assignment, date(2025, 6, 2), "lunch", "recipe", RECIPE_ID, None, None, None),
        ],
        rule_rows=[
            (SERIES_ID, date(2025, 6, 2), "lunch", "Sopa", 1),
            (SECOND_SERIES_ID, date(2025, 6, 2), "lunch", "Fruta", 2),
            (THIRD_SERIES_ID, date(2025, 6, 2), "lunch", "Sopa", 1),
        ],
    )

    entries = MealCalendarRepository(RecordingConnection(cursor)).list_week(
        date(2025, 6, 2), date(2025, 6, 8)
    )

    assert [(entry.meal_date, entry.slot, entry.visible_text) for entry in entries] == [
        (date(2025, 6, 2), "lunch", "Arroz"),
        (date(2025, 6, 2), "lunch", "Fruta"),
        (date(2025, 6, 2), "lunch", "Sopa"),
        (date(2025, 6, 2), "lunch", "Sopa"),
        (date(2025, 6, 2), "lunch", "Receta no disponible"),
    ]
    recurring = [entry for entry in entries if getattr(entry, "entry_type", None) == "recurring_occurrence"]
    assert [(entry.series_id, entry.occurrence_date) for entry in recurring] == [
        (SECOND_SERIES_ID, date(2025, 6, 2)),
        (SERIES_ID, date(2025, 6, 2)),
        (THIRD_SERIES_ID, date(2025, 6, 2)),
    ]
    assert len({entry.id for entry in recurring}) == 3
    assert any("meal_recurrence_rules" in query for query, _ in cursor.calls)

    repeated_entries = MealCalendarRepository(RecordingConnection(cursor)).list_week(
        date(2025, 6, 2), date(2025, 6, 8)
    )
    assert [entry.id for entry in repeated_entries if getattr(entry, "entry_type", None) == "recurring_occurrence"] == [
        entry.id for entry in recurring
    ]


def test_recurrence_rule_writes_are_idempotent_and_do_not_materialize_occurrences() -> None:
    cursor = RecordingCursor(row=(SERIES_ID,))
    repository = MealCalendarRepository(RecordingConnection(cursor))
    draft = RecurrenceRuleDraft.create(
        initial_date=date(2025, 6, 2), slot="lunch", free_text="Sopa", interval_weeks=1
    )

    assert repository.insert_rule(SERIES_ID, draft) is True
    assert repository.update_rule(SERIES_ID, draft) is True
    assert repository.delete_rule(SERIES_ID) is True

    queries = [query for query, _ in cursor.calls]
    assert all("meal_assignments" not in query for query in queries)
    assert any("ON CONFLICT (id) DO NOTHING" in query for query in queries)
    assert any(query.startswith("UPDATE meal_recurrence_rules") for query in queries)
    assert any(query.startswith("DELETE FROM meal_recurrence_rules") for query in queries)


def test_assignment_writes_are_parameterized_and_leave_transaction_to_the_caller() -> None:
    cursor = RecordingCursor(row=(ASSIGNMENT_ID,))
    connection = RecordingConnection(cursor)
    repository = MealCalendarRepository(connection)
    draft = AssignmentDraft.create(
        meal_date=date(2025, 6, 2), slot="lunch", kind="recipe", recipe_id=RECIPE_ID
    )

    assert repository.insert(ASSIGNMENT_ID, draft) is True
    assert repository.update(ASSIGNMENT_ID, draft) is True
    assert repository.delete(ASSIGNMENT_ID) is True

    insert_query, insert_params = cursor.calls[0]
    update_query, update_params = cursor.calls[1]
    delete_query, delete_params = cursor.calls[2]
    assert "ON CONFLICT (id) DO NOTHING" in insert_query
    assert insert_params == (ASSIGNMENT_ID, "shared", date(2025, 6, 2), "lunch", "recipe", RECIPE_ID, None)
    assert "assignment_kind = %s" in update_query
    assert update_params[-2:] == (ASSIGNMENT_ID, "recipe")
    assert delete_query.startswith("DELETE FROM meal_assignments")
    assert delete_params == (ASSIGNMENT_ID,)
    assert connection.commit_calls == 0
