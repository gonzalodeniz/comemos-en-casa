# Comprueba las consultas y operaciones de planificación de comidas.
from datetime import date
from uuid import uuid4

from sqlalchemy import select, text

from app.models import MealAssignment


from meal_planning_test_support import meal_database, api_get, api_post, authenticate, seed_labels, post_with_session


def test_meal_planning_reads_require_an_active_session(meal_database):
    assert api_get("/api/v1/food-labels").status_code == 401
    assert (
        api_get(
            "/api/v1/meal-planning",
            params={"start_date": "2026-11-02", "end_date": "2026-11-08"},
        ).status_code
        == 401
    )

def test_meal_planning_reads_reject_inactive_users(meal_database):
    cookies = authenticate(meal_database, active=False)

    assert api_get("/api/v1/food-labels", cookies=cookies).status_code == 401
    assert (
        api_get(
            "/api/v1/meal-planning",
            params={"start_date": "2026-11-02", "end_date": "2026-11-08"},
            cookies=cookies,
        ).status_code
        == 401
    )

def test_meal_planning_range_is_inclusive_and_reports_canary_date(
    meal_database, monkeypatch
):
    cookies = authenticate(meal_database)
    pescado, arroz = seed_labels(meal_database)
    with meal_database() as db:
        db.add_all(
            [
                MealAssignment(
                    date=date(2026, 11, 1), slot="dinner", label_id=pescado.id
                ),
                MealAssignment(
                    date=date(2026, 11, 2), slot="lunch", label_id=arroz.id
                ),
                MealAssignment(
                    date=date(2026, 11, 8), slot="dinner", label_id=pescado.id
                ),
                MealAssignment(
                    date=date(2026, 11, 9), slot="lunch", label_id=arroz.id
                ),
            ]
        )
        db.commit()

    monkeypatch.setattr(
        "app.meal_planning_api.canary_today", lambda: date(2026, 11, 2)
    )
    response = api_get(
        "/api/v1/meal-planning",
        params={"start_date": "2026-11-02", "end_date": "2026-11-08"},
        cookies=cookies,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["start_date"] == "2026-11-02"
    assert payload["end_date"] == "2026-11-08"
    assert payload["today"] == "2026-11-02"
    assert payload["timezone"] == "Atlantic/Canary"
    assert [entry["date"] for entry in payload["assignments"]] == [
        "2026-11-02",
        "2026-11-08",
    ]
    assert [entry["slot"] for entry in payload["assignments"]] == [
        "lunch",
        "dinner",
    ]
    assert [entry["label"]["code"] for entry in payload["assignments"]] == [
        "arroz",
        "pescado",
    ]
    with meal_database() as db:
        assert db.query(MealAssignment).count() == 4

def test_meal_planning_rejects_a_reversed_range_without_writes(meal_database):
    cookies = authenticate(meal_database)

    response = api_get(
        "/api/v1/meal-planning",
        params={"start_date": "2026-11-09", "end_date": "2026-11-02"},
        cookies=cookies,
    )

    assert response.status_code == 422
    with meal_database() as db:
        assert db.query(MealAssignment).count() == 0

def test_preview_is_authenticated_csrf_protected_and_has_no_side_effects(
    meal_database,
):
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    payload = {
        "action": "assign",
        "start_date": "2026-11-02",
        "slot": "lunch",
        "label_id": str(pescado.id),
        "repeat": {"interval_weeks": 1, "end_date": "2026-11-16"},
    }

    assert api_post("/api/v1/meal-planning/preview", payload=payload).status_code == 401
    assert (
        api_post(
            "/api/v1/meal-planning/preview",
            payload=payload,
            cookies=cookies,
            csrf_token=cookies["csrf_token"],
            origin=False,
        ).status_code
        == 403
    )
    response = post_with_session("/api/v1/meal-planning/preview", payload, cookies)

    assert response.status_code == 200
    preview = response.json()
    assert [entry["date"] for entry in preview["dates"]] == [
        "2026-11-02",
        "2026-11-09",
        "2026-11-16",
    ]
    assert preview["changed_count"] == 3
    assert preview["requires_confirmation"] is False
    assert preview["preview_token"]
    with meal_database() as db:
        assert db.query(MealAssignment).count() == 0

def test_assignment_repeat_replaces_only_after_confirming_current_preview(
    meal_database,
):
    cookies = authenticate(meal_database)
    pescado, arroz = seed_labels(meal_database)
    with meal_database() as db:
        db.add(
            MealAssignment(date=date(2026, 11, 9), slot="lunch", label_id=arroz.id)
        )
        db.commit()
    payload = {
        "action": "assign",
        "start_date": "2026-11-02",
        "slot": "lunch",
        "label_id": str(pescado.id),
        "repeat": {"interval_weeks": 1, "end_date": "2026-11-16"},
    }

    preview = post_with_session(
        "/api/v1/meal-planning/preview", payload, cookies
    ).json()
    assert preview["requires_confirmation"] is True
    assert [entry["change"] for entry in preview["dates"]] == [
        "assign",
        "replace",
        "assign",
    ]

    unconfirmed = post_with_session(
        "/api/v1/meal-planning/operations", payload, cookies
    )
    assert unconfirmed.status_code == 409
    with meal_database() as db:
        assert db.get(MealAssignment, db.scalar(select(MealAssignment.id))) is not None
        assert db.scalar(
            select(MealAssignment.label_id).where(
                MealAssignment.date == date(2026, 11, 9)
            )
        ) == arroz.id

    operation = {
        **payload,
        "confirmed": True,
        "preview_token": preview["preview_token"],
    }
    response = post_with_session("/api/v1/meal-planning/operations", operation, cookies)
    assert response.status_code == 200
    assert response.json()["changed_count"] == 3
    with meal_database() as db:
        assert db.query(MealAssignment).count() == 3
        assert set(db.scalars(select(MealAssignment.label_id)).all()) == {pescado.id}

def test_stale_preview_returns_fresh_confirmation_without_overwriting(
    meal_database,
):
    cookies = authenticate(meal_database)
    pescado, arroz = seed_labels(meal_database)
    payload = {
        "action": "assign",
        "start_date": "2026-11-02",
        "slot": "dinner",
        "label_id": str(pescado.id),
        "repeat": None,
    }
    original_preview = post_with_session(
        "/api/v1/meal-planning/preview", payload, cookies
    ).json()
    with meal_database() as db:
        db.add(
            MealAssignment(date=date(2026, 11, 2), slot="dinner", label_id=arroz.id)
        )
        db.commit()

    stale_request = {
        **payload,
        "confirmed": True,
        "preview_token": original_preview["preview_token"],
    }
    response = post_with_session(
        "/api/v1/meal-planning/operations", stale_request, cookies
    )
    assert response.status_code == 409
    refreshed = response.json()["detail"]["preview"]
    assert refreshed["requires_confirmation"] is True
    assert refreshed["preview_token"] != original_preview["preview_token"]
    with meal_database() as db:
        assert db.scalar(select(MealAssignment.label_id)) == arroz.id

    fresh_request = {**payload, "confirmed": True, "preview_token": refreshed["preview_token"]}
    applied = post_with_session(
        "/api/v1/meal-planning/operations", fresh_request, cookies
    )
    assert applied.status_code == 200
    with meal_database() as db:
        assert db.scalar(select(MealAssignment.label_id)) == pescado.id

def test_delete_only_removes_exact_matching_label_and_requires_confirmation(
    meal_database,
):
    cookies = authenticate(meal_database)
    pescado, arroz = seed_labels(meal_database)
    with meal_database() as db:
        db.add_all(
            [
                MealAssignment(date=date(2026, 11, 2), slot="dinner", label_id=pescado.id),
                MealAssignment(date=date(2026, 11, 9), slot="dinner", label_id=arroz.id),
            ]
        )
        db.commit()
    payload = {
        "action": "delete",
        "start_date": "2026-11-02",
        "slot": "dinner",
        "label_id": str(pescado.id),
        "repeat": {"interval_weeks": 1, "end_date": "2026-11-09"},
    }
    preview = post_with_session("/api/v1/meal-planning/preview", payload, cookies).json()
    assert [entry["change"] for entry in preview["dates"]] == ["delete", "no_op"]
    assert preview["requires_confirmation"] is True

    unconfirmed = post_with_session("/api/v1/meal-planning/operations", payload, cookies)
    assert unconfirmed.status_code == 409
    operation = {**payload, "confirmed": True, "preview_token": preview["preview_token"]}
    response = post_with_session("/api/v1/meal-planning/operations", operation, cookies)
    assert response.status_code == 200
    assert response.json()["changed_dates"] == ["2026-11-02"]
    with meal_database() as db:
        remaining = db.scalars(select(MealAssignment)).all()
        assert len(remaining) == 1
        assert remaining[0].date == date(2026, 11, 9)
        assert remaining[0].label_id == arroz.id

def test_invalid_operations_reject_bad_dates_interval_slot_and_label(meal_database):
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    base = {
        "action": "assign",
        "start_date": "2026-11-02",
        "slot": "lunch",
        "label_id": str(pescado.id),
        "repeat": None,
    }
    invalid = [
        {**base, "slot": "breakfast"},
        {**base, "label_id": str(uuid4())},
        {**base, "repeat": {"interval_weeks": True, "end_date": "2026-11-16"}},
        {**base, "repeat": {"interval_weeks": 1, "end_date": "2026-11-01"}},
        {**base, "start_date": "not-a-date"},
    ]
    for payload in invalid:
        response = post_with_session(
            "/api/v1/meal-planning/preview", payload, cookies
        )
        assert response.status_code == 422
    with meal_database() as db:
        assert db.query(MealAssignment).count() == 0

def test_failed_repeated_operation_rolls_back_the_entire_batch(meal_database):
    cookies = authenticate(meal_database)
    pescado, _ = seed_labels(meal_database)
    with meal_database() as db:
        db.execute(
            text(
                """CREATE TRIGGER reject_second_meal_date
                   BEFORE INSERT ON meal_assignments
                   WHEN NEW.date = '2026-11-09'
                   BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END"""
            )
        )
        db.commit()
    payload = {
        "action": "assign",
        "start_date": "2026-11-02",
        "slot": "lunch",
        "label_id": str(pescado.id),
        "repeat": {"interval_weeks": 1, "end_date": "2026-11-09"},
    }

    response = post_with_session("/api/v1/meal-planning/operations", payload, cookies)
    assert response.status_code == 503
    with meal_database() as db:
        assert db.query(MealAssignment).count() == 0
