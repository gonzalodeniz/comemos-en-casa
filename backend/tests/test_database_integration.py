"""Comprueba invariantes de autenticación en PostgreSQL.

Las pruebas de concurrencia requieren una base aislada y solo se ejecutan cuando se habilita explícitamente la integración.
"""

import os
import subprocess
import sys
import threading
from collections import Counter
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.database import database_url
from app.models import LoginAttemptBucket, LoginAttemptEvent, PasswordResetToken, User, UserSession
from app.auth import allow_password_reset_request, increment_failure_bucket, password_reset_rate_keys
from app.security import digest_rate_limit_key, digest_token


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires an isolated PostgreSQL instance and an applied migration",
)
def test_database_is_ready_and_baseline_is_applied():
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
    assert "0004_password_reset_rate_scopes (head)" in migration.stdout


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
