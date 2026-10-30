"""Comprueba invariantes de autenticación en PostgreSQL.

Las pruebas de concurrencia requieren una base aislada y solo se ejecutan cuando se habilita explícitamente la integración.
"""

import os
import subprocess
import sys
import threading
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, delete, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.database import database_url
from app.models import (
    FoodLabel,
    LoginAttemptBucket,
    LoginAttemptEvent,
    MealAssignment,
    PasswordResetToken,
    User,
    UserSession,
)
from app.auth import allow_password_reset_request, increment_failure_bucket, password_reset_rate_keys
from app.security import digest_rate_limit_key, digest_token


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires an isolated PostgreSQL instance and an applied migration",
)
def test_database_is_ready_and_latest_migration_is_applied():
    with TestClient(app) as client:
        response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    migration = subprocess.run(
        [sys.executable, "-m", "alembic", "current"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert migration.returncode == 0, migration.stderr
    assert "0006_food_catalog_images (head)" in migration.stdout


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL database with migrations applied",
)
def test_auth_schema_and_concurrent_email_uniqueness():
    engine = create_engine(database_url(), pool_pre_ping=True)
    canonical_email = f"migration-{uuid4().hex}@example.test"
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    try:
        inspector = inspect(engine)
        assert {
            "users",
            "user_sessions",
            "password_reset_tokens",
            "login_attempt_buckets",
            "login_attempt_events",
            "food_labels",
            "meal_assignments",
        }.issubset(inspector.get_table_names())

        def insert_user() -> None:
            with Session(engine) as session:
                session.add(
                    User(
                        name="Integration user",
                        email=canonical_email,
                        email_canonical=canonical_email,
                        password_hash="integration-only-placeholder",
                    )
                )
                barrier.wait(timeout=10)
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    outcomes.append("duplicate")
                else:
                    outcomes.append("created")

        workers = [threading.Thread(target=insert_user) for _ in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=15)
            assert not worker.is_alive()

        assert Counter(outcomes) == Counter({"created": 1, "duplicate": 1})
    finally:
        with engine.begin() as connection:
            connection.execute(
                delete(User.__table__).where(
                    User.__table__.c.email_canonical == canonical_email
                )
            )
        engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL database with migrations applied",
)
def test_meal_planning_migration_seeds_exact_default_catalog():
    engine = create_engine(database_url(), pool_pre_ping=True)
    expected = [
        ("arroz", "Arroz"),
        ("carne", "Carne"),
        ("cerdo", "Cerdo"),
        ("ensalada", "Ensalada"),
        ("garbanzos", "Garbanzos"),
        ("huevos", "Huevos"),
        ("judias", "Judías"),
        ("legumbres", "Legumbres"),
        ("lentejas", "Lentejas"),
        ("marisco", "Marisco"),
        ("pasta", "Pasta"),
        ("pescado", "Pescado"),
        ("pizza", "Pizza"),
        ("pollo", "Pollo"),
        ("sardinas", "Sardinas"),
        ("sopa", "Sopa"),
        ("ternera", "Ternera"),
        ("verduras", "Verduras"),
    ]
    try:
        with Session(engine) as session:
            labels = session.query(FoodLabel).order_by(FoodLabel.code).all()
            assert [(label.code, label.name) for label in labels] == expected
            assert len({label.id for label in labels}) == 18
            expected_ids = {
                "arroz": 15,
                "carne": 8,
                "cerdo": 11,
                "ensalada": 13,
                "garbanzos": 2,
                "huevos": 16,
                "judias": 4,
                "legumbres": 1,
                "lentejas": 3,
                "marisco": 7,
                "pasta": 14,
                "pescado": 5,
                "pizza": 18,
                "pollo": 9,
                "sardinas": 6,
                "sopa": 17,
                "ternera": 10,
                "verduras": 12,
            }
            assert {
                label.code: str(label.id) for label in labels
            } == {
                code: f"10000000-0000-4000-8000-{index:012d}"
                for code, index in expected_ids.items()
            }
            assert MealAssignment.__tablename__ == "meal_assignments"
    finally:
        engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL database with migrations applied",
)
def test_concurrent_initial_registration_creates_exactly_one_account():
    # La barrera fuerza a ambas peticiones a competir por el primer alta.
    email = f"bootstrap-{uuid4().hex}@example.test"
    barrier = threading.Barrier(2)
    outcomes: list[int] = []

    def register() -> None:
        client = TestClient(app)
        barrier.wait(timeout=10)
        response = client.post(
            "/api/v1/auth/register-initial",
            headers={"Origin": "http://localhost:5173"},
            json={"name": "Bootstrap user", "email": email, "password": "a valid password"},
        )
        outcomes.append(response.status_code)

    workers = [threading.Thread(target=register) for _ in range(2)]
    try:
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=30)
            assert not worker.is_alive()
        assert Counter(outcomes) == Counter({201: 1, 409: 1})
    finally:
        engine = create_engine(database_url(), pool_pre_ping=True)
        with engine.begin() as connection:
            user_ids = select(User.__table__.c.id).where(
                User.__table__.c.email == email
            )
            connection.execute(
                delete(UserSession.__table__).where(
                    UserSession.__table__.c.user_id.in_(user_ids)
                )
            )
            connection.execute(delete(User.__table__).where(User.__table__.c.email == email))
        engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires an isolated PostgreSQL instance and an applied migration",
)
def test_login_failure_bucket_increments_atomically_across_sessions():
    # Cada hilo usa una sesión distinta para comprobar la atomicidad real de la base.
    engine = create_engine(database_url(), pool_pre_ping=True)
    digest = digest_rate_limit_key(f"integration:{uuid4().hex}")
    now = datetime.now(timezone.utc)
    barrier = threading.Barrier(8)
    errors: list[Exception] = []

    def increment() -> None:
        try:
            with Session(engine) as session:
                barrier.wait(timeout=10)
                increment_failure_bucket(session, "ip", digest, now)
                session.commit()
        except Exception as error:
            errors.append(error)

    try:
        workers = [threading.Thread(target=increment) for _ in range(8)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=20)
            assert not worker.is_alive()
        assert not errors
        with Session(engine) as session:
            bucket = session.query(LoginAttemptBucket).filter_by(key_digest=digest).one()
            assert bucket.failure_count == 8
            assert bucket.blocked_until is not None
            assert (
                session.query(LoginAttemptEvent)
                .filter_by(key_digest=digest, scope="ip")
                .count()
                == 8
            )
    finally:
        with engine.begin() as connection:
            connection.execute(
                delete(LoginAttemptBucket.__table__).where(
                    LoginAttemptBucket.__table__.c.key_digest == digest
                )
            )
            connection.execute(
                delete(LoginAttemptEvent.__table__).where(
                    LoginAttemptEvent.__table__.c.key_digest == digest
                )
            )
        engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL instance with migrations applied",
)
def test_concurrent_deactivation_never_removes_all_active_accounts():
    engine = create_engine(database_url(), pool_pre_ping=True)
    suffix = uuid4().hex
    users = [
        User(
            name=f"Lifecycle {index}",
            email=f"lifecycle-{index}-{suffix}@example.test",
            email_canonical=f"lifecycle-{index}-{suffix}@example.test",
            password_hash="integration-only-placeholder",
        )
        for index in range(2)
    ]
    session_tokens = [f"session-{uuid4().hex}" for _ in users]
    csrf_tokens = [f"csrf-{uuid4().hex}" for _ in users]
    outcomes: list[int] = []
    barrier = threading.Barrier(2)

    with Session(engine) as session:
        session.add_all(users)
        session.flush()
        now = datetime.now(timezone.utc)
        session.add_all(
            [
                UserSession(
                    user_id=user.id,
                    token_digest=digest_token(session_tokens[index]),
                    csrf_token_digest=digest_token(csrf_tokens[index]),
                    created_at=now,
                    last_seen_at=now,
                    idle_expires_at=now + timedelta(minutes=30),
                    absolute_expires_at=now + timedelta(hours=8),
                )
                for index, user in enumerate(users)
            ]
        )
        session.commit()
        user_ids = [user.id for user in users]

    def deactivate(actor: int) -> None:
        client = TestClient(app)
        client.cookies.set("session", session_tokens[actor])
        client.cookies.set("csrf_token", csrf_tokens[actor])
        barrier.wait(timeout=10)
        response = client.patch(
            f"/api/v1/users/{user_ids[1 - actor]}",
            headers={
                "Origin": "http://localhost:5173",
                "X-CSRF-Token": csrf_tokens[actor],
            },
            json={"is_active": False},
        )
        outcomes.append(response.status_code)

    workers = [threading.Thread(target=deactivate, args=(actor,)) for actor in range(2)]
    try:
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=30)
            assert not worker.is_alive()
        assert outcomes.count(200) == 1
        assert all(code in {200, 401, 409} for code in outcomes)
        with Session(engine) as session:
            assert session.query(User).filter(User.is_active.is_(True)).count() == 1
    finally:
        with engine.begin() as connection:
            connection.execute(
                delete(PasswordResetToken.__table__).where(
                    PasswordResetToken.__table__.c.user_id.in_(user_ids)
                )
            )
            connection.execute(
                delete(UserSession.__table__).where(UserSession.__table__.c.user_id.in_(user_ids))
            )
            connection.execute(delete(User.__table__).where(User.__table__.c.id.in_(user_ids)))
        engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL instance with migrations applied",
)
def test_password_reset_limits_are_atomic_per_account_and_ip():
    engine = create_engine(database_url(), pool_pre_ping=True)
    now = datetime.now(timezone.utc)

    def run_attempt(email: str, ip: str, barrier: threading.Barrier, result: list[bool]) -> None:
        with Session(engine) as session:
            barrier.wait(timeout=10)
            result.append(
                allow_password_reset_request(
                    session, password_reset_rate_keys(email, ip), now
                )
            )

    try:
        account_results: list[bool] = []
        account_barrier = threading.Barrier(8)
        account_workers = [
            threading.Thread(
                target=run_attempt,
                args=("same-account@example.test", "203.0.113.40", account_barrier, account_results),
            )
            for _ in range(8)
        ]
        for worker in account_workers:
            worker.start()
        for worker in account_workers:
            worker.join(timeout=20)
            assert not worker.is_alive()
        assert sum(account_results) == 3

        ip_results: list[bool] = []
        ip_barrier = threading.Barrier(12)
        ip_workers = [
            threading.Thread(
                target=run_attempt,
                args=(f"account-{index}@example.test", "203.0.113.41", ip_barrier, ip_results),
            )
            for index in range(12)
        ]
        for worker in ip_workers:
            worker.start()
        for worker in ip_workers:
            worker.join(timeout=30)
            assert not worker.is_alive()
        assert sum(ip_results) == 10
    finally:
        with engine.begin() as connection:
            connection.execute(
                delete(LoginAttemptEvent.__table__).where(
                    LoginAttemptEvent.__table__.c.scope.in_(("reset_account", "reset_ip"))
                )
            )
            connection.execute(
                delete(LoginAttemptBucket.__table__).where(
                    LoginAttemptBucket.__table__.c.scope.in_(("reset_account", "reset_ip"))
                )
            )
        engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL instance with migrations applied",
)
def test_password_reset_token_can_be_consumed_only_once_concurrently():
    engine = create_engine(database_url(), pool_pre_ping=True)
    suffix = uuid4().hex
    email = f"reset-once-{suffix}@example.test"
    token = f"reset-{uuid4().hex}"
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        user = User(
            name="Reset account",
            email=email,
            email_canonical=email,
            password_hash="integration-only-placeholder",
        )
        session.add(user)
        session.flush()
        user_id = user.id
        session.add(
            PasswordResetToken(
                user_id=user.id,
                token_digest=digest_token(token),
                created_at=now,
                expires_at=now + timedelta(minutes=30),
            )
        )
        session.commit()

    barrier = threading.Barrier(2)
    outcomes: list[int] = []

    def consume() -> None:
        client = TestClient(app)
        barrier.wait(timeout=10)
        response = client.post(
            "/api/v1/password-resets/confirm",
            headers={"Origin": "http://localhost:5173"},
            json={"token": token, "new_password": "recovered password"},
        )
        outcomes.append(response.status_code)

    workers = [threading.Thread(target=consume) for _ in range(2)]
    try:
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(timeout=30)
            assert not worker.is_alive()
        assert Counter(outcomes) == Counter({204: 1, 400: 1})
        with Session(engine) as session:
            record = session.query(PasswordResetToken).filter_by(user_id=user_id).one()
            assert record.used_at is not None
    finally:
        with engine.begin() as connection:
            connection.execute(
                delete(PasswordResetToken.__table__).where(
                    PasswordResetToken.__table__.c.user_id == user_id
                )
            )
            connection.execute(delete(User.__table__).where(User.__table__.c.id == user_id))
        engine.dispose()


def _unique_meal_date() -> date:
    # Spread synthetic dates over centuries to avoid overlap with other test rows.
    return date(2100, 1, 1) + timedelta(days=uuid4().int % 100_000)


class MealIntegrationCleanup:
    def __init__(self, engine):
        self.engine = engine
        self.user_ids: set[UUID] = set()
        self.assignment_ids: set[UUID] = set()
        self.trigger_names: set[str] = set()
        self.function_names: set[str] = set()
        self.lock = threading.Lock()

    def track_user(self, user_id: UUID) -> None:
        with self.lock:
            self.user_ids.add(user_id)

    def track_assignment(self, assignment_id: UUID) -> None:
        with self.lock:
            self.assignment_ids.add(assignment_id)

    def track_trigger(self, trigger_name: str, function_name: str) -> None:
        with self.lock:
            self.trigger_names.add(trigger_name)
            self.function_names.add(function_name)

    def assignment_ids_for_operation(self, operation: dict[str, object]) -> set[UUID]:
        start = date.fromisoformat(operation["start_date"])
        repeat = operation.get("repeat")
        dates = [start]
        if repeat is not None:
            interval = repeat["interval_weeks"] * 7
            end = date.fromisoformat(repeat["end_date"])
            dates = []
            occurrence = start
            while occurrence <= end:
                dates.append(occurrence)
                occurrence += timedelta(days=interval)
        with Session(self.engine) as session:
            assignment_ids = set(session.scalars(
                select(MealAssignment.id).where(
                    MealAssignment.date.in_(dates),
                    MealAssignment.slot == operation["slot"],
                )
            ).all())
        return assignment_ids

    def cleanup(self) -> None:
        with self.lock:
            user_ids = set(self.user_ids)
            assignment_ids = set(self.assignment_ids)
            trigger_names = set(self.trigger_names)
            function_names = set(self.function_names)
        with self.engine.begin() as connection:
            for trigger_name in trigger_names:
                connection.execute(
                    text(f"DROP TRIGGER IF EXISTS {trigger_name} ON meal_assignments")
                )
            for function_name in function_names:
                connection.execute(text(f"DROP FUNCTION IF EXISTS {function_name}()"))
            if assignment_ids:
                connection.execute(
                    delete(MealAssignment.__table__).where(
                        MealAssignment.__table__.c.id.in_(assignment_ids)
                    )
                )
            if user_ids:
                connection.execute(
                    delete(UserSession.__table__).where(
                        UserSession.__table__.c.user_id.in_(user_ids)
                    )
                )
                connection.execute(
                    delete(User.__table__).where(User.__table__.c.id.in_(user_ids))
                )
        with self.lock:
            self.user_ids.difference_update(user_ids)
            self.assignment_ids.difference_update(assignment_ids)
            self.trigger_names.difference_update(trigger_names)
            self.function_names.difference_update(function_names)


@pytest.fixture
def meal_integration_cleanup(request):
    engine = create_engine(database_url(), pool_pre_ping=True)
    cleanup = MealIntegrationCleanup(engine)

    def finalize() -> None:
        try:
            cleanup.cleanup()
        finally:
            engine.dispose()

    request.addfinalizer(finalize)
    return cleanup


def _assert_meal_slots_empty(engine, dates: list[date], slots: tuple[str, ...]) -> None:
    with Session(engine) as session:
        existing = session.scalars(
            select(MealAssignment.id).where(
                MealAssignment.date.in_(dates), MealAssignment.slot.in_(slots)
            )
        ).all()
    assert not existing, "synthetic meal dates/slots must be empty before this test writes"


def _create_meal_user(
    cleanup: MealIntegrationCleanup, suffix: str
) -> tuple[UUID, str, str]:
    engine = cleanup.engine
    session_token = f"meal-session-{uuid4().hex}"
    csrf_token = f"meal-csrf-{uuid4().hex}"
    email = f"meal-{suffix}-{uuid4().hex}@example.test"
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        user = User(
            name=f"Meal integration {suffix}",
            email=email,
            email_canonical=email,
            password_hash="integration-only-placeholder",
        )
        session.add(user)
        session.flush()
        user_id = user.id
        cleanup.track_user(user_id)
        session.add(
            UserSession(
                user_id=user_id,
                token_digest=digest_token(session_token),
                csrf_token_digest=digest_token(csrf_token),
                created_at=now,
                last_seen_at=now,
                idle_expires_at=now + timedelta(minutes=30),
                absolute_expires_at=now + timedelta(hours=8),
            )
        )
        session.commit()
        return user_id, session_token, csrf_token


def _meal_api_post(
    path: str,
    payload: dict[str, object],
    session_token: str,
    csrf_token: str,
    cleanup: MealIntegrationCleanup | None = None,
):
    operation_write = cleanup is not None and path == "/api/v1/meal-planning/operations"
    before_ids = cleanup.assignment_ids_for_operation(payload) if operation_write else set()
    with TestClient(app) as client:
        client.cookies.set("session", session_token)
        client.cookies.set("csrf_token", csrf_token)
        try:
            response = client.post(
                path,
                headers={
                    "Origin": "http://localhost:5173",
                    "X-CSRF-Token": csrf_token,
                },
                json=payload,
            )
        finally:
            if operation_write:
                after_ids = cleanup.assignment_ids_for_operation(payload)
                for assignment_id in after_ids - before_ids:
                    cleanup.track_assignment(assignment_id)
    return response


def _meal_operation(
    action: str,
    start_date: date,
    slot: str,
    label_id,
    *,
    repeat: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "action": action,
        "start_date": start_date.isoformat(),
        "slot": slot,
        "label_id": str(label_id),
        "repeat": repeat,
    }


def _preview_meal_operation(
    operation: dict[str, object], session_token: str, csrf_token: str
) -> dict[str, object]:
    response = _meal_api_post(
        "/api/v1/meal-planning/preview", operation, session_token, csrf_token
    )
    assert response.status_code == 200, response.text
    return response.json()


def _apply_meal_operation(
    operation: dict[str, object],
    preview_token: str,
    session_token: str,
    csrf_token: str,
    *,
    confirmed: bool = False,
    cleanup: MealIntegrationCleanup | None = None,
):
    return _meal_api_post(
        "/api/v1/meal-planning/operations",
        {
            **operation,
            "confirmed": confirmed,
            "preview_token": preview_token,
        },
        session_token,
        csrf_token,
        cleanup,
    )


def _run_concurrent_requests(requests):
    barrier = threading.Barrier(len(requests))
    responses: list[object | None] = [None] * len(requests)
    errors: list[Exception] = []

    def run(index: int) -> None:
        try:
            barrier.wait(timeout=10)
            responses[index] = requests[index]()
        except Exception as error:
            errors.append(error)

    workers = [threading.Thread(target=run, args=(index,)) for index in range(len(requests))]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=30)
    assert not [worker.name for worker in workers if worker.is_alive()]
    assert not errors
    return responses


def _retry_refreshed_meal_operation(
    response,
    operation: dict[str, object],
    session_token: str,
    csrf_token: str,
    cleanup: MealIntegrationCleanup,
):
    assert response.status_code == 409, response.text
    fresh_preview = response.json()["detail"]["preview"]
    retry = _apply_meal_operation(
        operation,
        fresh_preview["preview_token"],
        session_token,
        csrf_token,
        confirmed=True,
        cleanup=cleanup,
    )
    assert retry.status_code == 200, retry.text
    return fresh_preview


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL database with migrations applied",
)
def test_concurrent_assignments_to_initially_empty_slot_require_fresh_confirmation(
    meal_integration_cleanup,
):
    cleanup = meal_integration_cleanup
    engine = cleanup.engine
    start = _unique_meal_date()
    slot = "lunch"
    # Use a fresh synthetic user so authentication and writes are scoped to this test.
    user_id, session_token, csrf_token = _create_meal_user(cleanup, "empty-slot")
    _assert_meal_slots_empty(engine, [start], (slot,))
    with Session(engine) as session:
        labels = {
            label.code: label.id
            for label in session.scalars(
                select(FoodLabel).where(FoodLabel.code.in_(("arroz", "pescado")))
            ).all()
        }
    assert set(labels) == {"arroz", "pescado"}
    operations = [
        _meal_operation("assign", start, slot, labels[code])
        for code in ("arroz", "pescado")
    ]
    previews = [
        _preview_meal_operation(operation, session_token, csrf_token)
        for operation in operations
    ]

    try:
        responses = _run_concurrent_requests(
            [
                lambda index=index: _apply_meal_operation(
                    operations[index],
                    previews[index]["preview_token"],
                    session_token,
                    csrf_token,
                    cleanup=cleanup,
                )
                for index in range(2)
            ]
        )
        assert sorted(response.status_code for response in responses) == [200, 409]
        winner_index = next(
            index for index, response in enumerate(responses) if response.status_code == 200
        )
        stale_index = 1 - winner_index
        _retry_refreshed_meal_operation(
            responses[stale_index], operations[stale_index], session_token, csrf_token, cleanup
        )
        with Session(engine) as session:
            rows = session.scalars(
                select(MealAssignment).where(
                    MealAssignment.date == start, MealAssignment.slot == slot
                )
            ).all()
            assert len(rows) == 1
            # The retried operation is the last confirmed write and must prevail.
            assert rows[0].label_id == labels[("arroz", "pescado")[stale_index]]
    finally:
        cleanup.cleanup()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL database with migrations applied",
)
def test_concurrent_assign_and_exact_delete_never_removes_replacement(
    meal_integration_cleanup,
):
    cleanup = meal_integration_cleanup
    engine = cleanup.engine
    start = _unique_meal_date()
    actor_id, session_token, csrf_token = _create_meal_user(cleanup, "assign-delete")
    _assert_meal_slots_empty(engine, [start], ("dinner",))
    with Session(engine) as session:
        labels = {
            label.code: label.id
            for label in session.scalars(
                select(FoodLabel).where(FoodLabel.code.in_(("arroz", "pescado")))
            ).all()
        }
        assignment = MealAssignment(date=start, slot="dinner", label_id=labels["arroz"])
        session.add(assignment)
        session.flush()
        cleanup.track_assignment(assignment.id)
        session.commit()
    assign = _meal_operation("assign", start, "dinner", labels["pescado"])
    delete_exact = _meal_operation("delete", start, "dinner", labels["arroz"])
    assign_preview = _preview_meal_operation(assign, session_token, csrf_token)
    delete_preview = _preview_meal_operation(delete_exact, session_token, csrf_token)
    assert assign_preview["requires_confirmation"] is True
    assert delete_preview["requires_confirmation"] is True

    try:
        responses = _run_concurrent_requests(
            [
                lambda: _apply_meal_operation(
                    assign,
                    assign_preview["preview_token"],
                    session_token,
                    csrf_token,
                    confirmed=True,
                    cleanup=cleanup,
                ),
                lambda: _apply_meal_operation(
                    delete_exact,
                    delete_preview["preview_token"],
                    session_token,
                    csrf_token,
                    confirmed=True,
                    cleanup=cleanup,
                ),
            ]
        )
        assert sorted(response.status_code for response in responses) == [200, 409]
        stale_index = next(
            index for index, response in enumerate(responses) if response.status_code == 409
        )
        stale_operation = (assign, delete_exact)[stale_index]
        _retry_refreshed_meal_operation(
            responses[stale_index], stale_operation, session_token, csrf_token, cleanup
        )
        with Session(engine) as session:
            row = session.scalar(
                select(MealAssignment).where(
                    MealAssignment.date == start, MealAssignment.slot == "dinner"
                )
            )
            # Exact deletion of the old label cannot erase the new replacement.
            assert row is not None
            assert row.label_id == labels["pescado"]
    finally:
        cleanup.cleanup()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL database with migrations applied",
)
def test_concurrent_overlapping_repeats_serialize_and_last_confirmed_batch_wins(
    meal_integration_cleanup,
):
    cleanup = meal_integration_cleanup
    engine = cleanup.engine
    first = _unique_meal_date()
    actor_id, session_token, csrf_token = _create_meal_user(cleanup, "overlap")
    _assert_meal_slots_empty(
        engine,
        [first + timedelta(days=offset) for offset in (0, 7, 14, 21)],
        ("lunch",),
    )
    with Session(engine) as session:
        labels = {
            label.code: label.id
            for label in session.scalars(
                select(FoodLabel).where(FoodLabel.code.in_(("arroz", "pescado")))
            ).all()
        }
    operations = [
        _meal_operation(
            "assign",
            first,
            "lunch",
            labels["arroz"],
            repeat={"interval_weeks": 1, "end_date": (first + timedelta(days=14)).isoformat()},
        ),
        _meal_operation(
            "assign",
            first + timedelta(days=7),
            "lunch",
            labels["pescado"],
            repeat={"interval_weeks": 1, "end_date": (first + timedelta(days=21)).isoformat()},
        ),
    ]
    previews = [
        _preview_meal_operation(operation, session_token, csrf_token)
        for operation in operations
    ]

    try:
        responses = _run_concurrent_requests(
            [
                lambda index=index: _apply_meal_operation(
                    operations[index],
                    previews[index]["preview_token"],
                    session_token,
                    csrf_token,
                    cleanup=cleanup,
                )
                for index in range(2)
            ]
        )
        assert sorted(response.status_code for response in responses) == [200, 409]
        winner_index = next(
            index for index, response in enumerate(responses) if response.status_code == 200
        )
        stale_index = 1 - winner_index
        _retry_refreshed_meal_operation(
            responses[stale_index], operations[stale_index], session_token, csrf_token, cleanup
        )
        expected: dict[date, object] = {}
        for operation_index in (winner_index, stale_index):
            operation = operations[operation_index]
            start_date = date.fromisoformat(operation["start_date"])
            end_date = date.fromisoformat(operation["repeat"]["end_date"])
            occurrence = start_date
            while occurrence <= end_date:
                expected[occurrence] = labels["arroz" if operation_index == 0 else "pescado"]
                occurrence += timedelta(days=7)
        with Session(engine) as session:
            rows = session.scalars(
                select(MealAssignment).where(
                    MealAssignment.date.in_(list(expected)),
                    MealAssignment.slot == "lunch",
                )
            ).all()
            assert {row.date: row.label_id for row in rows} == expected
    finally:
        cleanup.cleanup()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL database with migrations applied",
)
def test_concurrent_assignments_to_distinct_initially_empty_slots_are_preserved(
    meal_integration_cleanup,
):
    cleanup = meal_integration_cleanup
    engine = cleanup.engine
    start = _unique_meal_date()
    actor_id, session_token, csrf_token = _create_meal_user(cleanup, "empty-slots")
    _assert_meal_slots_empty(engine, [start], ("lunch", "dinner"))
    with Session(engine) as session:
        labels = {
            label.code: label.id
            for label in session.scalars(
                select(FoodLabel).where(FoodLabel.code.in_(("arroz", "pescado")))
            ).all()
        }
    operations = [
        _meal_operation("assign", start, slot, labels[code])
        for slot, code in (("lunch", "arroz"), ("dinner", "pescado"))
    ]
    previews = [
        _preview_meal_operation(operation, session_token, csrf_token)
        for operation in operations
    ]

    try:
        responses = _run_concurrent_requests(
            [
                lambda index=index: _apply_meal_operation(
                    operations[index],
                    previews[index]["preview_token"],
                    session_token,
                    csrf_token,
                    cleanup=cleanup,
                )
                for index in range(2)
            ]
        )
        assert [response.status_code for response in responses] == [200, 200]
        with Session(engine) as session:
            rows = session.scalars(
                select(MealAssignment).where(MealAssignment.date == start)
            ).all()
            assert {row.slot: row.label_id for row in rows} == {
                "lunch": labels["arroz"],
                "dinner": labels["pescado"],
            }
    finally:
        cleanup.cleanup()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL database with migrations applied",
)
def test_postgresql_repeated_operation_rolls_back_all_rows_on_mid_batch_failure(
    meal_integration_cleanup,
):
    cleanup = meal_integration_cleanup
    engine = cleanup.engine
    first = _unique_meal_date()
    failing_date = first + timedelta(days=7)
    actor_id, session_token, csrf_token = _create_meal_user(cleanup, "batch-rollback")
    _assert_meal_slots_empty(engine, [first, failing_date], ("lunch",))
    with Session(engine) as session:
        label_id = session.scalar(select(FoodLabel.id).where(FoodLabel.code == "arroz"))
        assert label_id is not None
    suffix = uuid4().hex
    function_name = f"fail_meal_batch_{suffix}"
    trigger_name = f"fail_meal_batch_trigger_{suffix}"
    cleanup.track_trigger(trigger_name, function_name)
    with engine.begin() as connection:
        connection.execute(
            text(
                f"""CREATE FUNCTION {function_name}() RETURNS trigger AS $$
                    BEGIN
                      IF NEW.date = DATE '{failing_date.isoformat()}' THEN
                        RAISE EXCEPTION 'synthetic meal batch failure';
                      END IF;
                      RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql"""
            )
        )
        connection.execute(
            text(
                f"CREATE TRIGGER {trigger_name} BEFORE INSERT ON meal_assignments "
                f"FOR EACH ROW EXECUTE FUNCTION {function_name}()"
            )
        )
    operation = _meal_operation(
        "assign",
        first,
        "lunch",
        label_id,
        repeat={"interval_weeks": 1, "end_date": failing_date.isoformat()},
    )
    preview = _preview_meal_operation(operation, session_token, csrf_token)

    try:
        response = _apply_meal_operation(
            operation,
            preview["preview_token"],
            session_token,
            csrf_token,
            cleanup=cleanup,
        )
        assert response.status_code == 503, response.text
        with Session(engine) as session:
            assert (
                session.scalar(
                    select(MealAssignment.id).where(
                        MealAssignment.date.in_((first, failing_date)),
                        MealAssignment.slot == "lunch",
                    )
                )
                is None
            )
    finally:
        cleanup.cleanup()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL database with migrations applied",
)
def test_postgresql_repeated_delete_removes_only_exact_label_occurrences(
    meal_integration_cleanup,
):
    cleanup = meal_integration_cleanup
    engine = cleanup.engine
    first = _unique_meal_date()
    dates = [first + timedelta(days=offset) for offset in (0, 7, 14)]
    actor_id, session_token, csrf_token = _create_meal_user(cleanup, "exact-delete")
    _assert_meal_slots_empty(engine, dates, ("dinner",))
    with Session(engine) as session:
        labels = {
            label.code: label.id
            for label in session.scalars(
                select(FoodLabel).where(FoodLabel.code.in_(("arroz", "pescado")))
            ).all()
        }
        assignments = [
            MealAssignment(date=dates[0], slot="dinner", label_id=labels["arroz"]),
            MealAssignment(date=dates[1], slot="dinner", label_id=labels["pescado"]),
            MealAssignment(date=dates[2], slot="dinner", label_id=labels["arroz"]),
        ]
        session.add_all(assignments)
        session.flush()
        for assignment in assignments:
            cleanup.track_assignment(assignment.id)
        session.commit()
    operation = _meal_operation(
        "delete",
        first,
        "dinner",
        labels["arroz"],
        repeat={"interval_weeks": 1, "end_date": dates[2].isoformat()},
    )
    preview = _preview_meal_operation(operation, session_token, csrf_token)

    try:
        response = _apply_meal_operation(
            operation,
            preview["preview_token"],
            session_token,
            csrf_token,
            confirmed=True,
            cleanup=cleanup,
        )
        assert response.status_code == 200, response.text
        assert response.json()["changed_dates"] == [dates[0].isoformat(), dates[2].isoformat()]
        with Session(engine) as session:
            rows = session.scalars(
                select(MealAssignment).where(
                    MealAssignment.date.in_(dates), MealAssignment.slot == "dinner"
                )
            ).all()
            assert [(row.date, row.label_id) for row in rows] == [(dates[1], labels["pescado"])]
    finally:
        cleanup.cleanup()


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires a fresh, isolated PostgreSQL database with migrations applied",
)
def test_deleting_hu001_user_preserves_shared_meal_assignments(meal_integration_cleanup):
    cleanup = meal_integration_cleanup
    engine = cleanup.engine
    start = _unique_meal_date()
    actor_id, actor_token, actor_csrf = _create_meal_user(cleanup, "shared-actor")
    target_id, _, _ = _create_meal_user(cleanup, "shared-target")
    _assert_meal_slots_empty(engine, [start], ("dinner",))
    with Session(engine) as session:
        label_id = session.scalar(select(FoodLabel.id).where(FoodLabel.code == "arroz"))
        assert label_id is not None
        assignment = MealAssignment(date=start, slot="dinner", label_id=label_id)
        session.add(assignment)
        session.flush()
        cleanup.track_assignment(assignment.id)
        session.commit()

    try:
        client = TestClient(app)
        client.cookies.set("session", actor_token)
        client.cookies.set("csrf_token", actor_csrf)
        response = client.delete(
            f"/api/v1/users/{target_id}",
            headers={"Origin": "http://localhost:5173", "X-CSRF-Token": actor_csrf},
        )
        assert response.status_code == 204, response.text
        with Session(engine) as session:
            assert session.get(User, target_id) is None
            assignment = session.scalar(
                select(MealAssignment).where(
                    MealAssignment.date == start, MealAssignment.slot == "dinner"
                )
            )
            assert assignment is not None
            assert assignment.label_id == label_id
    finally:
        cleanup.cleanup()
