# Comprueba las operaciones y validaciones del catálogo de alimentos.
from datetime import date
from uuid import UUID

import pytest
from sqlalchemy import select

from app.auth import SESSION_COOKIE
from app.models import FoodLabel, MealAssignment, UserSession
from app.security import digest_token


from meal_planning_test_support import meal_database, api_get, api_patch, authenticate, seed_labels, post_with_session


def test_food_labels_are_sorted_and_read_does_not_create_meal_assignments(
    meal_database,
):
    cookies = authenticate(meal_database)
    seed_labels(meal_database)

    response = api_get("/api/v1/food-labels", cookies=cookies)

    assert response.status_code == 200
    assert [label["code"] for label in response.json()["labels"]] == [
        "arroz",
        "pescado",
    ]
    assert [label["recipe_count"] for label in response.json()["labels"]] == [0, 0]
    with meal_database() as db:
        assert db.scalar(select(MealAssignment.id)) is None

def test_food_label_casefold_expansion_keeps_valid_visible_name(meal_database):
    from app.meal_planning_api import canonical_label_name

    name, canonical = canonical_label_name("ß" * 50 + "a" * 50)
    assert len(name) == 100
    assert len(canonical) == 150
    assert canonical == "ss" * 50 + "a" * 50

def test_duplicate_integrity_error_is_classified_narrowly():
    from sqlalchemy.exc import IntegrityError
    from app.meal_planning_api import _is_duplicate_label_error

    duplicate = IntegrityError("insert", {}, Exception("UNIQUE constraint failed: food_labels.name_canonical"))
    unrelated = IntegrityError("insert", {}, Exception("UNIQUE constraint failed: users.email"))
    assert _is_duplicate_label_error(duplicate)
    assert not _is_duplicate_label_error(unrelated)

def test_create_food_label_reports_duplicate_name(meal_database):
    cookies = authenticate(meal_database)
    seed_labels(meal_database)
    response = post_with_session("/api/v1/food-labels", {"name":"  ARROZ "}, cookies)
    assert response.status_code == 409

def test_update_food_label_reports_duplicate_name(meal_database):
    cookies = authenticate(meal_database)
    pescado, arroz = seed_labels(meal_database)
    response = api_patch(f"/api/v1/food-labels/{pescado.id}", payload={"name":" arroz "}, cookies=cookies, csrf_token=cookies["csrf_token"])
    assert response.status_code == 409

def test_update_succeeds_when_old_image_cleanup_fails(meal_database, tmp_path, monkeypatch, caplog):
    import app.meal_planning_api as api
    from pathlib import Path

    cookies = authenticate(meal_database)
    monkeypatch.setattr(api, "DATA_ROOT", tmp_path)
    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    with meal_database() as db:
        label = FoodLabel(code="cleanup-test", name="Before", image_path=f"comidas/{image.name}")
        db.add(label)
        db.commit()
        label_id = label.id
    original_unlink = Path.unlink
    def fail_old_image(self, *args, **kwargs):
        if self == image:
            raise PermissionError("denied")
        return original_unlink(self, *args, **kwargs)
    monkeypatch.setattr(Path, "unlink", fail_old_image)
    response = api_patch(f"/api/v1/food-labels/{label_id}", payload={"name": "After", "remove_image": True}, cookies=cookies, csrf_token=cookies["csrf_token"])
    assert response.status_code == 200
    with meal_database() as db:
        label = db.get(FoodLabel, label_id)
        assert label.name == "After" and label.image_path is None
    assert image.exists() and "food_image_cleanup_failed" in caplog.text

def test_create_commit_failure_preserves_published_image(meal_database, tmp_path, monkeypatch):
    import app.meal_planning_api as api
    from app.food_images import save_temporary
    from sqlalchemy.orm import Session

    cookies = authenticate(meal_database)
    monkeypatch.setattr(api, "DATA_ROOT", tmp_path)
    # The endpoint uses the authenticated session's ID, so seed the temp under it.
    with meal_database() as db:
        session = db.scalar(select(UserSession).where(UserSession.token_digest == digest_token(cookies[SESSION_COOKIE])))
        token = save_temporary(tmp_path, session.id, b"webp")
    original_commit = Session.commit
    def failing_commit(self):
        if any(isinstance(item, FoodLabel) for item in self.new):
            raise RuntimeError("simulated database failure")
        return original_commit(self)
    monkeypatch.setattr(Session, "commit", failing_commit)
    with pytest.raises(RuntimeError, match="simulated database failure"):
        post_with_session("/api/v1/food-labels", {"name":"Test dish", "image_token":token}, cookies)
    monkeypatch.setattr(Session, "commit", original_commit)
    assert len(list((tmp_path / "comidas").glob("*.webp"))) == 1

def test_ambiguous_commit_preserves_committed_image(meal_database, tmp_path, monkeypatch):
    import app.meal_planning_api as api
    from app.food_images import save_temporary
    from sqlalchemy.orm import Session

    cookies = authenticate(meal_database)
    monkeypatch.setattr(api, "DATA_ROOT", tmp_path)
    with meal_database() as db:
        session = db.scalar(select(UserSession).where(UserSession.token_digest == digest_token(cookies[SESSION_COOKIE])))
        token = save_temporary(tmp_path, session.id, b"webp")
    original_commit = Session.commit
    def ambiguous_commit(self):
        is_food_commit = any(isinstance(item, FoodLabel) for item in self.new)
        original_commit(self)
        if is_food_commit:
            raise RuntimeError("commit acknowledgement lost")
    monkeypatch.setattr(Session, "commit", ambiguous_commit)
    with pytest.raises(RuntimeError, match="acknowledgement lost"):
        post_with_session("/api/v1/food-labels", {"name": "Committed dish", "image_token": token}, cookies)
    monkeypatch.setattr(Session, "commit", original_commit)
    with meal_database() as db:
        label = db.scalar(select(FoodLabel).where(FoodLabel.name == "Committed dish"))
        assert label is not None and (tmp_path / label.image_path).is_file()

def test_create_food_label_returns_published_image_url(meal_database, tmp_path, monkeypatch):
    import app.meal_planning_api as api
    from app.food_images import save_temporary

    cookies = authenticate(meal_database)
    monkeypatch.setattr(api, "DATA_ROOT", tmp_path)
    with meal_database() as db:
        session = db.scalar(select(UserSession).where(UserSession.token_digest == digest_token(cookies[SESSION_COOKIE])))
        token = save_temporary(tmp_path, session.id, b"prepared-webp")
    response = post_with_session("/api/v1/food-labels", {"name":"Image dish", "image_token":token}, cookies)
    assert response.status_code == 201
    assert response.json()["image_url"].startswith(f"/food-labels/{response.json()['id']}/image?v=")

def test_replacing_image_changes_urls_across_catalog_and_planning(meal_database, tmp_path, monkeypatch):
    import app.meal_planning_api as api
    from app.food_images import save_temporary

    root = tmp_path / "cache-version-data"
    monkeypatch.setattr(api, "DATA_ROOT", root)
    cookies = authenticate(meal_database)
    with meal_database() as db:
        session = db.scalar(select(UserSession).where(UserSession.token_digest == digest_token(cookies[SESSION_COOKIE])))
        first = save_temporary(root, session.id, b"first image")
        second = save_temporary(root, session.id, b"second image")
    created = post_with_session("/api/v1/food-labels", {"name": "Versioned", "image_token": first}, cookies)
    assert created.status_code == 201
    label = created.json()
    old_url = label["image_url"]
    with meal_database() as db:
        db.add(MealAssignment(date=date(2026, 11, 2), slot="lunch", label_id=UUID(label["id"])))
        db.commit()
    updated = api_patch(f"/api/v1/food-labels/{label['id']}", payload={"name": "Versioned", "image_token": second}, cookies=cookies, csrf_token=cookies["csrf_token"])
    assert updated.status_code == 200
    new_url = updated.json()["image_url"]
    assert new_url != old_url
    listing = api_get("/api/v1/food-labels", cookies=cookies).json()["labels"]
    assert next(item for item in listing if item["id"] == label["id"])["image_url"] == new_url
    planning = api_get("/api/v1/meal-planning", params={"start_date": "2026-11-02", "end_date": "2026-11-02"}, cookies=cookies).json()
    assert planning["assignments"][0]["label"]["image_url"] == new_url
    preview = post_with_session("/api/v1/meal-planning/preview", {"action": "assign", "start_date": "2026-11-02", "slot": "lunch", "label_id": label["id"], "repeat": None}, cookies).json()
    assert preview["dates"][0]["current_label"]["image_url"] == new_url
    assert preview["dates"][0]["resulting_label"]["image_url"] == new_url
    removed = api_patch(f"/api/v1/food-labels/{label['id']}", payload={"name": "Versioned", "remove_image": True}, cookies=cookies, csrf_token=cookies["csrf_token"])
    assert removed.json()["image_url"] is None
