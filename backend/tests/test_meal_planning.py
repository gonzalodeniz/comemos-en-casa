import asyncio
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from app.auth import SESSION_COOKIE
from app.database import get_database_session
from app.main import app
from app.models import (
    Base,
    FoodLabel,
    MealAssignment,
    User,
    UserSession,
)
from app.security import digest_token


def test_managed_image_rejects_absolute_traversal_and_symlinks(tmp_path, monkeypatch):
    import app.meal_planning_api as api

    monkeypatch.setattr(api, "DATA_ROOT", tmp_path)
    folder = tmp_path / "comidas"
    folder.mkdir()
    name = "a" * 32 + ".webp"
    image = folder / name
    image.write_bytes(b"image")
    assert api._managed_food_image_path(f"comidas/{name}") == image
    assert api._managed_food_image_path(str(image)) is None
    assert api._managed_food_image_path(f"comidas/../comidas/{name}") is None
    image.unlink()
    image.symlink_to(tmp_path / "outside")
    assert api._managed_food_image_path(f"comidas/{name}") is None


def test_cleanup_failure_does_not_raise(tmp_path, monkeypatch, caplog):
    import app.meal_planning_api as api
    from pathlib import Path

    monkeypatch.setattr(api, "DATA_ROOT", tmp_path)
    (tmp_path / "comidas").mkdir()
    def fail_unlink(self, *args, **kwargs):
        raise PermissionError("denied")
    monkeypatch.setattr(Path, "unlink", fail_unlink)
    api._remove_food_image("comidas/" + "a" * 32 + ".webp")
    assert "food_image_cleanup_failed" in caplog.text


@pytest.fixture
def meal_database(monkeypatch, tmp_path):
    import app.meal_planning_api as api
    monkeypatch.setattr(api, "DATA_ROOT", tmp_path / "image-data")
    monkeypatch.setenv("AUTH_RATE_LIMIT_HMAC_KEY", "22" * 32)
    engine = create_engine(
        f"sqlite+pysqlite:///{tmp_path / 'meal-planning.sqlite'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    async def database_session():
        with factory() as session:
            yield session

    app.dependency_overrides[get_database_session] = database_session
    try:
        yield factory
    finally:
        app.dependency_overrides.pop(get_database_session, None)
        engine.dispose()


def test_orphan_inspection_is_advisory_and_preserves_files(meal_database, tmp_path):
    import os
    from app.food_images import ORPHAN_GRACE_SECONDS, inspect_possible_orphans

    folder = tmp_path / "comidas"
    folder.mkdir()
    active, orphan, fresh = [folder / (character * 32 + ".webp") for character in "abc"]
    for image in (active, orphan, fresh):
        image.write_bytes(b"image")
    now = 2_000_000.0
    for image in (active, orphan):
        os.utime(image, (now - ORPHAN_GRACE_SECONDS - 1,) * 2)
    os.utime(fresh, (now,) * 2)
    with meal_database() as db:
        db.add(FoodLabel(code="active-image", name="Active", image_path=f"comidas/{active.name}"))
        db.commit()
        assert inspect_possible_orphans(tmp_path, db, now=now) == [f"comidas/{orphan.name}"]
    assert all(image.exists() for image in (active, orphan, fresh))


def test_reconciliation_deletes_only_old_unreferenced_files(meal_database, tmp_path):
    import os
    from app.food_images import ORPHAN_GRACE_SECONDS, reconcile_orphans

    folder = tmp_path / "comidas"
    folder.mkdir()
    active, orphan, fresh = [folder / (character * 32 + ".webp") for character in "abc"]
    now = 2_000_000.0
    for image in (active, orphan, fresh):
        image.write_bytes(b"image")
    for image in (active, orphan):
        os.utime(image, (now - ORPHAN_GRACE_SECONDS - 1,) * 2)
    os.utime(fresh, (now,) * 2)
    with meal_database() as db:
        db.add(FoodLabel(code="protected", name="Protected", image_path=f"comidas/{active.name}"))
        db.commit()
    assert reconcile_orphans(tmp_path, meal_database, now=now) == [f"comidas/{orphan.name}"]
    assert active.exists() and fresh.exists() and not orphan.exists()
    assert reconcile_orphans(tmp_path, meal_database, now=now) == []


def test_reconciliation_waits_for_publication_commit(meal_database, tmp_path):
    import os
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from app.food_images import ORPHAN_GRACE_SECONDS, publication_lock, reconcile_orphans

    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    now = 2_000_000.0
    os.utime(image, (now - ORPHAN_GRACE_SECONDS - 1,) * 2)
    started = threading.Event()
    def reconcile():
        started.set()
        return reconcile_orphans(tmp_path, meal_database, now=now)
    with ThreadPoolExecutor() as executor:
        with publication_lock(tmp_path):
            future = executor.submit(reconcile)
            assert started.wait(5)
            with meal_database() as db:
                db.add(FoodLabel(code="in-flight", name="In flight", image_path=f"comidas/{image.name}"))
                db.commit()
        assert future.result(timeout=5) == []
    assert image.exists()


def test_async_publication_lock_keeps_event_loop_responsive(tmp_path):
    from app.food_images import async_publication_lock, publication_lock

    async def check():
        entered = asyncio.Event()
        async def waiter():
            async with async_publication_lock(tmp_path):
                entered.set()
        with publication_lock(tmp_path):
            task = asyncio.create_task(waiter())
            await asyncio.sleep(0.12)
            assert not entered.is_set()
        await asyncio.wait_for(task, 2)
        assert entered.is_set()
    asyncio.run(check())


def test_manual_reconciliation_requires_explicit_confirmation(meal_database, tmp_path, monkeypatch):
    import os
    import sys
    import app.database as database
    from app.food_images import main

    monkeypatch.setenv("APP_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(database, "SessionFactory", meal_database)
    monkeypatch.setattr(sys, "argv", ["food_images"])
    with pytest.raises(SystemExit):
        main()
    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    os.utime(image, (1, 1))
    monkeypatch.setattr(sys, "argv", ["food_images", "--confirm-coordinated-storage"])
    main()
    assert not image.exists()


def test_app_lifespan_does_not_schedule_orphan_reconciliation():
    import ast
    import inspect
    import textwrap
    import app.main as main_module

    for function in (main_module.lifespan, main_module._cleanup_food_image_temporaries):
        tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        assert "reconcile_orphans" not in names


def test_reconciliation_database_failure_preserves_files(tmp_path):
    from app.food_images import reconcile_orphans
    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    def broken_factory():
        raise RuntimeError("database unavailable")
    with pytest.raises(RuntimeError, match="database unavailable"):
        reconcile_orphans(tmp_path, broken_factory)
    assert image.exists()


def test_reconciliation_rejects_symlinked_directory(tmp_path):
    from app.food_images import reconcile_orphans
    outside = tmp_path / "outside"
    outside.mkdir()
    image = outside / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    (tmp_path / "comidas").symlink_to(outside, target_is_directory=True)
    class EmptyDatabase:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def scalars(self, _query): return iter(())
    with pytest.raises(OSError):
        reconcile_orphans(tmp_path, EmptyDatabase)
    assert image.exists()


def test_reconciliation_propagates_unlink_failure(meal_database, tmp_path, monkeypatch):
    import os
    from app.food_images import reconcile_orphans
    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    os.utime(image, (1, 1))
    def fail(*args, **kwargs):
        raise PermissionError("unlink denied")
    monkeypatch.setattr(os, "unlink", fail)
    with pytest.raises(PermissionError, match="unlink denied"):
        reconcile_orphans(tmp_path, meal_database, now=2_000_000)
    assert image.exists()


def test_orphan_inspection_fails_closed_on_database_failure(tmp_path):
    from app.food_images import inspect_possible_orphans

    class BrokenDatabase:
        def scalars(self, _query):
            raise RuntimeError("database unavailable")

    with pytest.raises(RuntimeError, match="database unavailable"):
        inspect_possible_orphans(tmp_path, BrokenDatabase())


def test_orphan_inspection_rejects_symlinked_storage(tmp_path):
    from app.food_images import inspect_possible_orphans

    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "comidas").symlink_to(outside, target_is_directory=True)

    class EmptyDatabase:
        def scalars(self, _query):
            return iter(())

    with pytest.raises(OSError, match="Unsafe image storage"):
        inspect_possible_orphans(tmp_path, EmptyDatabase())


def test_orphan_inspection_propagates_file_metadata_errors(tmp_path, monkeypatch):
    from pathlib import Path
    from app.food_images import inspect_possible_orphans

    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    original_lstat = Path.lstat

    def fail_image_lstat(path):
        if path == image:
            raise PermissionError("metadata unavailable")
        return original_lstat(path)

    class EmptyDatabase:
        def scalars(self, _query):
            return iter(())

    monkeypatch.setattr(Path, "lstat", fail_image_lstat)
    with pytest.raises(PermissionError, match="metadata unavailable"):
        inspect_possible_orphans(tmp_path, EmptyDatabase())
    assert image.read_bytes() == b"image"


def test_orphan_inspection_never_deletes_publication_after_snapshot(meal_database, tmp_path):
    import os
    from concurrent.futures import ThreadPoolExecutor
    from app.food_images import ORPHAN_GRACE_SECONDS, inspect_possible_orphans

    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    now = 2_000_000.0
    os.utime(image, (now - ORPHAN_GRACE_SECONDS - 1,) * 2)

    def commit_reference():
        with meal_database() as writer:
            writer.add(FoodLabel(code="concurrent-image", name="Concurrent", image_path=f"comidas/{image.name}"))
            writer.commit()

    with meal_database() as reader, ThreadPoolExecutor(max_workers=1) as executor:
        class ConcurrentPublication:
            def scalars(self, query):
                snapshot = list(reader.scalars(query))
                executor.submit(commit_reference).result(timeout=5)
                return iter(snapshot)

        assert inspect_possible_orphans(tmp_path, ConcurrentPublication(), now=now) == [f"comidas/{image.name}"]
    assert image.exists()  # A stale candidate is never treated as deletion authority.


def api_get(path: str, *, params=None, cookies=None):
    async def send_request():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            if cookies:
                client.cookies.update(cookies)
            return await client.get(path, params=params)

    return asyncio.run(send_request())


def api_post(path: str, *, payload: dict, cookies=None, csrf_token=None, origin=True):
    async def send_request():
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            if cookies:
                client.cookies.update(cookies)
            headers = {}
            if origin:
                headers["Origin"] = "http://localhost:5173"
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token
            return await client.post(path, json=payload, headers=headers)

    return asyncio.run(send_request())


def api_patch(path: str, *, payload: dict, cookies=None, csrf_token=None):
    async def send_request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            if cookies:
                client.cookies.update(cookies)
            return await client.patch(path, json=payload, headers={"Origin":"http://localhost:5173", "X-CSRF-Token":csrf_token or ""})
    return asyncio.run(send_request())


def authenticate(factory, *, active: bool = True) -> dict[str, str]:
    token = f"session-{uuid4().hex}"
    csrf_token = f"csrf-{uuid4().hex}"
    now = datetime.now(timezone.utc)
    with factory() as db:
        email = f"{uuid4().hex}@example.test"
        user = User(
            name="Meal planning user",
            email=email,
            email_canonical=email,
            password_hash="test-only-placeholder",
            is_active=active,
        )
        db.add(user)
        db.flush()
        db.add(
            UserSession(
                user_id=user.id,
                token_digest=digest_token(token),
                csrf_token_digest=digest_token(csrf_token),
                created_at=now,
                last_seen_at=now,
                idle_expires_at=now + timedelta(minutes=30),
                absolute_expires_at=now + timedelta(hours=8),
            )
        )
        db.commit()
    return {SESSION_COOKIE: token, "csrf_token": csrf_token}


def seed_labels(factory) -> tuple[FoodLabel, FoodLabel]:
    with factory() as db:
        labels = [
            FoodLabel(code="pescado", name="Pescado"),
            FoodLabel(code="arroz", name="Arroz"),
        ]
        db.add_all(labels)
        db.commit()
        return labels[0], labels[1]


def post_with_session(path, payload, cookies, **kwargs):
    return api_post(
        path,
        payload=payload,
        cookies=cookies,
        csrf_token=cookies.get("csrf_token"),
        **kwargs,
    )


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
