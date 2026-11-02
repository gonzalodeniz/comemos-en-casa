import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import SESSION_COOKIE
from app.database import get_database_session
from app.main import app
from app.models import Base, FoodLabel, User, UserSession
from app.security import digest_token


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
