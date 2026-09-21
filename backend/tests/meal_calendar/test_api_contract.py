from __future__ import annotations

import importlib
from datetime import date
from pathlib import Path
import sys
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.meal_calendar.repository import CalendarAssignment
from comemos_en_casa.meal_calendar.schemas import RecurrenceRule, RecurrenceRuleDraft
from comemos_en_casa.meal_calendar.service import occurrence_in_week


RECIPE_ID = UUID("00000000-0000-0000-0000-000000000100")
ASSIGNMENT_ID = UUID("00000000-0000-0000-0000-000000000200")


class FakeCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...] | None]] = []
        self._one: tuple[object, ...] | None = None
        self._many: list[tuple[object, ...]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        self.calls.append((query, params))
        if "FROM meal_assignments AS assignments" in query:
            self._many = [
                (
                    ASSIGNMENT_ID,
                    date(2025, 6, 2),
                    "lunch",
                    "recipe",
                    RECIPE_ID,
                    None,
                    "Tortilla Española",
                    "https://example.test/tortilla.jpg",
                ),
                (
                    UUID("00000000-0000-0000-0000-000000000201"),
                    date(2025, 6, 2),
                    "lunch",
                    "free_text",
                    None,
                    "  Sopa  ",
                    None,
                    None,
                ),
            ]
        elif "SELECT id, title, image_url, detail" in query:
            self._one = (RECIPE_ID, "Tortilla Española", "https://example.test/tortilla.jpg", "Current detail")
        elif "SELECT id, title, image_url" in query:
            self._many = [(RECIPE_ID, "Tortilla Española", "https://example.test/tortilla.jpg")]

    def fetchone(self) -> tuple[object, ...] | None:
        return self._one

    def fetchall(self) -> list[tuple[object, ...]]:
        return self._many


class FakeTransaction:
    def __enter__(self) -> "FakeTransaction":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()

    def cursor(self) -> FakeCursor:
        return self.cursor_instance

    def transaction(self) -> FakeTransaction:
        return FakeTransaction()


class StatefulCalendarRepository:
    state: "CalendarState"

    def __init__(self, connection: object) -> None:
        pass

    def find_by_id(self, assignment_id: UUID) -> CalendarAssignment | None:
        return self.state.assignments.get(assignment_id)

    def insert(self, assignment_id: UUID, draft: object) -> bool:
        if assignment_id in self.state.assignments:
            return False
        self.state.assignments[assignment_id] = CalendarAssignment(
            id=assignment_id,
            meal_date=draft.meal_date,  # type: ignore[attr-defined]
            slot=draft.slot,  # type: ignore[attr-defined]
            kind=draft.kind,  # type: ignore[attr-defined]
            recipe_id=draft.recipe_id,  # type: ignore[attr-defined]
            free_text=draft.free_text,  # type: ignore[attr-defined]
            recipe_title=None,
            recipe_image_url=None,
        )
        return True

    def update(self, assignment_id: UUID, draft: object) -> bool:
        if assignment_id not in self.state.assignments:
            return False
        self.state.assignments[assignment_id] = CalendarAssignment(
            id=assignment_id,
            meal_date=draft.meal_date,  # type: ignore[attr-defined]
            slot=draft.slot,  # type: ignore[attr-defined]
            kind=draft.kind,  # type: ignore[attr-defined]
            recipe_id=draft.recipe_id,  # type: ignore[attr-defined]
            free_text=draft.free_text,  # type: ignore[attr-defined]
            recipe_title=None,
            recipe_image_url=None,
        )
        return True

    def delete(self, assignment_id: UUID) -> bool:
        return self.state.assignments.pop(assignment_id, None) is not None

    def find_rule_by_id(self, series_id: UUID) -> RecurrenceRule | None:
        return self.state.rules.get(series_id)

    def insert_rule(self, series_id: UUID, draft: RecurrenceRuleDraft) -> bool:
        if series_id in self.state.rules:
            return False
        self.state.rules[series_id] = RecurrenceRule.create(
            id=series_id,
            initial_date=draft.initial_date,
            slot=draft.slot,
            free_text=draft.free_text,
            interval_weeks=draft.interval_weeks,
        )
        return True

    def update_rule(self, series_id: UUID, draft: RecurrenceRuleDraft) -> bool:
        if series_id not in self.state.rules:
            return False
        self.state.rules[series_id] = RecurrenceRule.create(
            id=series_id,
            initial_date=draft.initial_date,
            slot=draft.slot,
            free_text=draft.free_text,
            interval_weeks=draft.interval_weeks,
        )
        return True

    def delete_rule(self, series_id: UUID) -> bool:
        return self.state.rules.pop(series_id, None) is not None

    def list_week(self, week_start: date, week_end: date) -> list[CalendarAssignment]:
        entries = [
            assignment
            for assignment in self.state.assignments.values()
            if week_start <= assignment.meal_date <= week_end
        ]
        for rule in self.state.rules.values():
            occurrence_date = occurrence_in_week(rule, week_start, week_end)
            if occurrence_date is not None:
                entries.append(
                    CalendarAssignment(
                        id=f"series:{rule.series_id}:{occurrence_date.isoformat()}",
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
                )
        return sorted(entries, key=lambda entry: (entry.meal_date, entry.slot, entry.visible_text, str(entry.id)))


class CalendarState:
    def __init__(self) -> None:
        self.assignments = {
            ASSIGNMENT_ID: CalendarAssignment(
                id=ASSIGNMENT_ID,
                meal_date=date(2025, 6, 2),
                slot="lunch",
                kind="recipe",
                recipe_id=RECIPE_ID,
                free_text=None,
                recipe_title="Tortilla Española",
                recipe_image_url="https://example.test/tortilla.jpg",
            ),
            UUID("00000000-0000-0000-0000-000000000201"): CalendarAssignment(
                id=UUID("00000000-0000-0000-0000-000000000201"),
                meal_date=date(2025, 6, 2),
                slot="lunch",
                kind="free_text",
                recipe_id=None,
                free_text="  Sopa  ",
                recipe_title=None,
                recipe_image_url=None,
            ),
        }
        self.rules: dict[UUID, RecurrenceRule] = {}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db/app")
    state = CalendarState()
    StatefulCalendarRepository.state = state
    from comemos_en_casa.meal_calendar import api

    monkeypatch.setattr(api, "MealCalendarRepository", StatefulCalendarRepository)
    sys.modules.pop("comemos_en_casa.app", None)
    module = importlib.import_module("comemos_en_casa.app")
    application = module.create_app()
    application.state.calendar_state = state
    application.dependency_overrides[module.get_connection] = FakeConnection
    try:
        yield TestClient(application)
    finally:
        application.dependency_overrides.clear()


def seed_free_text_assignment(assignment_id: UUID) -> None:
    StatefulCalendarRepository.state.assignments[assignment_id] = CalendarAssignment(
        id=assignment_id,
        meal_date=date(2025, 6, 2),
        slot="lunch",
        kind="free_text",
        recipe_id=None,
        free_text="Sopa",
        recipe_title=None,
        recipe_image_url=None,
    )


def seed_series(series_id: UUID) -> None:
    StatefulCalendarRepository.state.rules[series_id] = RecurrenceRule.create(
        id=series_id,
        initial_date=date(2025, 6, 2),
        slot="lunch",
        free_text="Sopa",
        interval_weeks=1,
    )


def test_calendar_context_and_week_reads_use_no_store_and_public_recipe_presentation(client: TestClient) -> None:
    context = client.get("/api/v1/meal-calendar/context")
    week = client.get("/api/v1/meal-calendar/weeks/2025-06-02")

    assert context.status_code == 200
    assert context.headers["cache-control"] == "no-store"
    assert context.json()["timezone"] == "Europe/Canary"
    assert context.json()["guestMode"] is True
    assert week.status_code == 200
    assert week.json() == {
        "weekStart": "2025-06-02",
        "weekEnd": "2025-06-08",
        "timezone": "Europe/Canary",
        "assignments": [
            {
                "id": "00000000-0000-0000-0000-000000000201",
                "entryType": "assignment",
                "date": "2025-06-02",
                "slot": "lunch",
                "kind": "free_text",
                "text": "  Sopa  ",
            },
            {
                "id": str(ASSIGNMENT_ID),
                "entryType": "assignment",
                "date": "2025-06-02",
                "slot": "lunch",
                "kind": "recipe",
                "recipe": {
                    "id": str(RECIPE_ID),
                    "available": True,
                    "title": "Tortilla Española",
                    "coverImageUrl": "https://example.test/tortilla.jpg",
                },
            },
        ],
    }


def test_calendar_rejects_non_monday_week_starts_with_the_stable_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/meal-calendar/weeks/2025-06-03")

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["error"]["code"] == "invalid_week_start"
    assert response.json()["error"]["fieldErrors"] == {"weekStart": "week start must be a Monday"}


def test_public_recipe_search_and_detail_expose_only_current_catalogue_fields(client: TestClient) -> None:
    search = client.get("/api/v1/meal-calendar/recipes", params={"q": "tortilla espanola", "limit": 1})
    detail = client.get(f"/api/v1/meal-calendar/recipes/{RECIPE_ID}")

    assert search.status_code == 200
    assert search.headers["cache-control"] == "no-store"
    assert search.json()["recipes"] == [
        {"id": str(RECIPE_ID), "title": "Tortilla Española", "coverImageUrl": "https://example.test/tortilla.jpg"}
    ]
    assert search.json()["nextCursor"] is not None
    assert detail.status_code == 200
    assert detail.json() == {
        "id": str(RECIPE_ID),
        "title": "Tortilla Española",
        "coverImageUrl": "https://example.test/tortilla.jpg",
        "detail": "Current detail",
    }


def test_assignment_create_is_idempotent_for_the_same_uuid_and_payload(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from comemos_en_casa.meal_calendar import api
    from comemos_en_casa.meal_calendar.repository import CalendarAssignment

    class InMemoryRepository:
        assignment: CalendarAssignment | None = None

        def __init__(self, connection: object) -> None:
            pass

        def find_by_id(self, assignment_id: UUID) -> CalendarAssignment | None:
            return self.assignment

        def insert(self, assignment_id: UUID, draft: object) -> bool:
            if self.assignment is not None:
                return False
            self.__class__.assignment = CalendarAssignment(
                id=assignment_id,
                meal_date=draft.meal_date,  # type: ignore[attr-defined]
                slot=draft.slot,  # type: ignore[attr-defined]
                kind=draft.kind,  # type: ignore[attr-defined]
                recipe_id=draft.recipe_id,  # type: ignore[attr-defined]
                free_text=draft.free_text,  # type: ignore[attr-defined]
                recipe_title=None,
                recipe_image_url=None,
            )
            return True

    monkeypatch.setattr(api, "MealCalendarRepository", InMemoryRepository)
    payload = {
        "id": str(ASSIGNMENT_ID),
        "date": "2025-06-02",
        "slot": "dinner",
        "kind": "free_text",
        "text": "  Sopa  ",
    }

    created = client.post("/api/v1/meal-calendar/assignments", json=payload)
    repeated = client.post("/api/v1/meal-calendar/assignments", json=payload)
    conflict = client.post("/api/v1/meal-calendar/assignments", json={**payload, "text": "Ensalada"})

    assert created.status_code == 201
    assert created.headers["cache-control"] == "no-store"
    assert created.json() == {
        "id": str(ASSIGNMENT_ID),
        "entryType": "assignment",
        "date": "2025-06-02",
        "slot": "dinner",
        "kind": "free_text",
        "text": "Sopa",
    }
    assert repeated.status_code == 200
    assert repeated.json() == created.json()
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency_conflict"


def test_series_create_retry_is_idempotent_and_conflicting_payload_is_rejected(client: TestClient) -> None:
    series_id = UUID("00000000-0000-0000-0000-000000000300")
    payload = {
        "id": str(series_id),
        "date": "2025-06-02",
        "slot": "lunch",
        "kind": "free_text",
        "text": "  Sopa  ",
        "recurrenceWeeks": 1,
    }

    created = client.post("/api/v1/meal-calendar/assignments", json=payload)
    repeated = client.post("/api/v1/meal-calendar/assignments", json=payload)
    conflict = client.post(
        "/api/v1/meal-calendar/assignments", json={**payload, "text": "Ensalada"}
    )

    expected = {
        "id": f"series:{series_id}:2025-06-02",
        "entryType": "recurring_occurrence",
        "date": "2025-06-02",
        "slot": "lunch",
        "kind": "free_text",
        "text": "Sopa",
        "seriesId": str(series_id),
        "occurrenceDate": "2025-06-02",
        "initialDate": "2025-06-02",
        "recurrenceWeeks": 1,
    }
    assert created.status_code == 201
    assert created.json() == expected
    assert repeated.status_code == 200
    assert repeated.json() == expected
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency_conflict"


def test_ordinary_free_text_conversion_is_atomic_and_returns_one_series_occurrence(
    client: TestClient,
) -> None:
    assignment_id = UUID("00000000-0000-0000-0000-000000000301")
    seed_free_text_assignment(assignment_id)

    response = client.patch(
        f"/api/v1/meal-calendar/assignments/{assignment_id}",
        json={
            "date": "2025-06-02",
            "slot": "lunch",
            "kind": "free_text",
            "text": "Sopa",
            "recurrenceWeeks": 2,
        },
    )

    assert response.status_code == 200
    assert response.json()["entryType"] == "recurring_occurrence"
    assert response.json()["seriesId"] == str(assignment_id)
    assert response.json()["id"] == f"series:{assignment_id}:2025-06-02"


def test_series_patch_requires_anchor_confirmation_and_keeps_slot_immutable(client: TestClient) -> None:
    series_id = UUID("00000000-0000-0000-0000-000000000302")
    seed_series(series_id)
    path = f"/api/v1/meal-calendar/series/{series_id}"
    body = {"initialDate": "2025-06-06", "text": "Crema", "recurrenceWeeks": 2}

    unconfirmed = client.patch(path, json=body)
    confirmed = client.patch(path, json={**body, "confirmAnchorChange": True})
    slot_change = client.patch(path, json={**body, "slot": "dinner", "confirmAnchorChange": True})

    assert unconfirmed.status_code == 422
    assert confirmed.status_code == 200
    assert confirmed.json() == {
        "seriesId": str(series_id),
        "initialDate": "2025-06-06",
        "slot": "lunch",
        "text": "Crema",
        "recurrenceWeeks": 2,
    }
    assert slot_change.status_code == 422
    assert slot_change.json()["error"]["code"] == "validation_failed"


def test_series_delete_requires_confirmation_is_destructive_and_idempotent(client: TestClient) -> None:
    series_id = UUID("00000000-0000-0000-0000-000000000303")
    seed_series(series_id)
    path = f"/api/v1/meal-calendar/series/{series_id}"

    missing_confirmation = client.delete(path)
    declined = client.delete(path, params={"confirmed": "false"})
    deleted = client.delete(path, params={"confirmed": "true"})
    repeated = client.delete(path, params={"confirmed": "true"})

    assert missing_confirmation.status_code == 422
    assert declined.status_code == 422
    assert deleted.status_code == 204
    assert repeated.status_code == 204


def test_invalid_recurrence_requests_are_non_mutating_and_no_repeat_is_not_a_patch_mode(
    client: TestClient,
) -> None:
    series_id = UUID("00000000-0000-0000-0000-000000000304")
    invalid_payloads = [
        {
            "id": str(series_id),
            "date": "2025-06-02",
            "slot": "lunch",
            "kind": "recipe",
            "recipeId": str(RECIPE_ID),
            "recurrenceWeeks": 1,
        },
        {
            "id": str(series_id),
            "date": "2025-06-02",
            "slot": "lunch",
            "kind": "free_text",
            "text": "Sopa",
            "recurrenceWeeks": 5,
        },
        {
            "id": str(series_id),
            "date": "2025-06-02",
            "slot": "lunch",
            "kind": "free_text",
            "text": "   ",
            "recurrenceWeeks": 1,
        },
    ]

    before = client.get("/api/v1/meal-calendar/weeks/2025-06-02").json()
    responses = [client.post("/api/v1/meal-calendar/assignments", json=payload) for payload in invalid_payloads]
    occurrence_only = client.patch(
        "/api/v1/meal-calendar/assignments/series:00000000-0000-0000-0000-000000000304:2025-06-02",
        json={"text": "Otra", "recurrenceWeeks": 1},
    )
    no_repeat_patch = client.patch(
        f"/api/v1/meal-calendar/series/{series_id}",
        json={"initialDate": "2025-06-02", "text": "Sopa", "recurrenceWeeks": 0},
    )

    after = client.get("/api/v1/meal-calendar/weeks/2025-06-02").json()

    assert [response.status_code for response in responses] == [422, 422, 422]
    assert occurrence_only.status_code in {404, 422}
    assert no_repeat_patch.status_code == 422
    assert after == before


def test_legacy_recipe_response_remains_distinct_from_recurring_free_text(client: TestClient) -> None:
    response = client.get("/api/v1/meal-calendar/weeks/2025-06-02")

    recipe = next(item for item in response.json()["assignments"] if item["kind"] == "recipe")
    free_text = next(item for item in response.json()["assignments"] if item["kind"] == "free_text")

    assert recipe["entryType"] == "assignment"
    assert recipe["recipe"]["available"] is True
    assert "seriesId" not in recipe
    assert free_text["entryType"] == "assignment"
    assert "recipe" not in free_text
