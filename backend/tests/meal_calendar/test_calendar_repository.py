from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.meal_calendar.repository import MealCalendarRepository
from comemos_en_casa.meal_calendar.schemas import AssignmentDraft


ASSIGNMENT_ID = UUID("00000000-0000-0000-0000-000000000001")
RECIPE_ID = UUID("00000000-0000-0000-0000-000000000002")


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
