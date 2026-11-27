"""Verifica los flujos y controles de autenticación.

Cubre sesiones, protección CSRF, límites temporales, administración de usuarios y recuperación de contraseñas.
"""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.auth import (
    CSRF_COOKIE,
    SESSION_COOKIE,
    as_utc,
    allow_password_reset_request,
    is_rate_limited,
    password_reset_rate_keys,
    record_failed_login,
    utc_now,
)
from app.database import get_database_session
from app.main import app
from app.models import Base, LoginAttemptBucket, PasswordResetToken, User, UserSession
from app.security import digest_token, generate_token


@pytest.fixture
def auth_client(monkeypatch, tmp_path):
    monkeypatch.setenv("AUTH_RATE_LIMIT_HMAC_KEY", "11" * 32)
    monkeypatch.setenv("APP_PUBLIC_URL", "http://localhost:5173")
    engine = create_engine(
        f"sqlite+pysqlite:///{tmp_path / 'auth-test.sqlite'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    async def database_session():
        with factory() as session:
            yield session

    app.dependency_overrides[get_database_session] = database_session
    client = TestClient(app, client=("203.0.113.10", 45678))
    yield client, factory
    app.dependency_overrides.pop(get_database_session, None)
    engine.dispose()


def register(client, email="person@example.test", password="correct horse"):
    return client.post(
        "/api/v1/auth/register-initial",
        headers={"Origin": "http://localhost:5173"},
        json={"name": "Person", "email": email, "password": password},
    )


def login(client, email="person@example.test", password="correct horse"):
    return client.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:5173"},
        json={"email": email, "password": password},
    )


def test_last_view_is_restored_after_signing_in_again(auth_client):
    """Comprueba que una nueva sesión recupera la vista guardada del usuario."""
    client, _ = auth_client
    register(client)
    login(client)
    response = client.put(
        "/api/v1/auth/last-view",
        headers={"Origin": "http://localhost:5173", "X-CSRF-Token": client.cookies[CSRF_COOKIE]},
        json={"vista": "backups"},
    )
    assert response.status_code == 204
    client.cookies.clear()
    login(client)
    assert client.get("/api/v1/auth/session").json()["ultima_vista"] == "backups"


def test_last_view_is_independent_for_each_user(auth_client):
    """Comprueba que cada cuenta recupera su propia vista."""
    client, _ = auth_client
    authenticated_user(client)
    create_family_user(client)
    headers = {"Origin": "http://localhost:5173", "X-CSRF-Token": client.cookies[CSRF_COOKIE]}
    assert client.put("/api/v1/auth/last-view", headers=headers, json={"vista": "backups"}).status_code == 204
    client.cookies.clear()
    assert login(client, "other@example.test", "another secret").status_code == 200
    assert client.get("/api/v1/auth/session").json()["ultima_vista"] is None
    headers["X-CSRF-Token"] = client.cookies[CSRF_COOKIE]
    assert client.put("/api/v1/auth/last-view", headers=headers, json={"vista": "recipes"}).status_code == 204
    client.cookies.clear()
    assert login(client).status_code == 200
    assert client.get("/api/v1/auth/session").json()["ultima_vista"] == "backups"
    client.cookies.clear()
    assert login(client, "other@example.test", "another secret").status_code == 200
    assert client.get("/api/v1/auth/session").json()["ultima_vista"] == "recipes"


def test_last_view_update_requires_session_and_csrf(auth_client):
    """Impide modificar la vista sin sesión o sin protección CSRF."""
    client, _ = auth_client
    assert client.put("/api/v1/auth/last-view", json={"vista": "recipes"}).status_code == 401
    register(client)
    login(client)
    assert client.put("/api/v1/auth/last-view", headers={"Origin": "http://localhost:5173"}, json={"vista": "recipes"}).status_code == 403
    assert client.get("/api/v1/auth/session").json()["ultima_vista"] is None


def test_first_account_closes_bootstrap_without_automatic_login(auth_client):
    client, _ = auth_client
    assert client.get("/api/v1/auth/bootstrap").json() == {"initial_account_required": True}

    response = register(client)

    assert response.status_code == 201
    assert response.json()["user"]["email"] == "person@example.test"
    assert SESSION_COOKIE not in client.cookies
    assert client.get("/api/v1/auth/bootstrap").json() == {"initial_account_required": False}
    assert register(client, "second@example.test").status_code == 409


def test_login_sets_digest_backed_session_and_csrf_protects_logout(auth_client):
    client, factory = auth_client
    register(client)

    response = login(client)

    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "path=/" in cookie
    assert "domain=" not in cookie
    session_token = client.cookies[SESSION_COOKIE]
    csrf_token = client.cookies[CSRF_COOKIE]
    with factory() as db:
        stored = db.scalar(select(UserSession))
        assert stored.token_digest == digest_token(session_token)
        assert stored.token_digest != session_token
        assert stored.csrf_token_digest == digest_token(csrf_token)

    assert client.get("/api/v1/auth/session").status_code == 200
    blocked = client.post("/api/v1/auth/logout", headers={"Origin": "http://localhost:5173"})
    assert blocked.status_code == 403
    logout = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "http://localhost:5173", "X-CSRF-Token": csrf_token},
    )
    assert logout.status_code == 204
    assert client.get("/api/v1/auth/session").status_code == 401
    with factory() as db:
        assert db.scalar(select(UserSession)).revoked_at is not None


def test_login_requires_allowed_origin(auth_client):
    client, _ = auth_client
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": "https://attacker.example"},
        json={"email": "person@example.test", "password": "guess"},
    )
    assert response.status_code == 403


def test_failed_login_locks_account_ip_and_ip_wide_but_other_ip_can_login(auth_client):
    client, factory = auth_client
    register(client)
    # Private user creation is only available after the first account has logged in.
    login(client)
    csrf = client.cookies[CSRF_COOKIE]
    client.post(
        "/api/v1/users",
        headers={"Origin": "http://localhost:5173", "X-CSRF-Token": csrf},
        json={"name": "Other", "email": "other@example.test", "password": "another secret"},
    ).raise_for_status()

    for _ in range(5):
        failed = login(client, password="incorrect password")
        assert failed.status_code == 401
        assert failed.json() == {"detail": "Invalid email or password"}
    assert login(client, "other@example.test").status_code == 401

    other_ip = TestClient(app, client=("203.0.113.11", 45679))
    # Use the same fixture-backed database dependency and verify the account is not IP-locked.
    assert login(other_ip).status_code == 200
    with factory() as db:
        buckets = db.scalars(select(LoginAttemptBucket)).all()
        assert len(buckets) == 2
        assert {bucket.scope for bucket in buckets} == {"account_ip", "ip"}
        assert all(bucket.blocked_until is not None for bucket in buckets)


def test_login_lock_expires_after_fifteen_minutes(auth_client, monkeypatch):
    client, _ = auth_client
    clock = [utc_now()]
    monkeypatch.setattr("app.auth.utc_now", lambda: clock[0])
    register(client)
    for _ in range(5):
        assert login(client, password="wrong password").status_code == 401

    clock[0] += timedelta(minutes=15, seconds=1)
    assert login(client).status_code == 200


def test_idle_and_absolute_session_expiry_revoke_access(auth_client):
    client, factory = auth_client
    register(client)
    login(client)
    with factory() as db:
        session = db.scalar(select(UserSession))
        session.idle_expires_at = utc_now() - timedelta(seconds=1)
        db.commit()

    assert client.get("/api/v1/auth/session").status_code == 401
    with factory() as db:
        assert db.scalar(select(UserSession)).revoked_at is not None


def test_session_remains_valid_for_one_week_and_cookies_are_persistent(auth_client, monkeypatch):
    """Comprueba la duración semanal en el servidor y en ambas cookies."""
    client, _ = auth_client
    clock = [utc_now()]
    monkeypatch.setattr("app.auth.utc_now", lambda: clock[0])
    register(client)
    response = login(client)
    cookies = response.headers.get_list("set-cookie")
    assert len(cookies) == 2
    assert all("max-age=604800" in cookie.lower() for cookie in cookies)
    clock[0] += timedelta(days=7, seconds=-1)
    assert client.get("/api/v1/auth/session").status_code == 200
    clock[0] += timedelta(seconds=1)
    assert client.get("/api/v1/auth/session").status_code == 401


def test_password_limits_and_unicode_spaces_are_supported(auth_client):
    client, _ = auth_client
    for password in ("1234567", "x" * 129):
        response = register(client, password=password)
        assert response.status_code == 422
    response = register(client, password=" ñ space ")
    assert response.status_code == 201


def test_whitespace_only_account_name_is_rejected(auth_client):
    client, _ = auth_client
    response = client.post(
        "/api/v1/auth/register-initial",
        headers={"Origin": "http://localhost:5173"},
        json={"name": "    ", "email": "person@example.test", "password": "correct horse"},
    )
    assert response.status_code == 422
    assert client.get("/api/v1/auth/bootstrap").json() == {"initial_account_required": True}


def test_rolling_failure_counts_lock_both_scopes_and_expire(auth_client):
    _, factory = auth_client
    start = utc_now()
    account_key = ("account_ip", "a" * 64)
    ip_key = ("ip", "b" * 64)
    keys = (account_key, ip_key)
    failures = [
        start,
        start + timedelta(minutes=1),
        start + timedelta(minutes=2),
        start + timedelta(minutes=14),
        start + timedelta(minutes=14, seconds=59),
    ]

    for failure_time in failures:
        with factory() as db:
            record_failed_login(db, keys, failure_time)

    with factory() as db:
        assert is_rate_limited(db, keys, failures[-1])
        for scope, digest in keys:
            bucket = db.scalar(
                select(LoginAttemptBucket).where(
                    LoginAttemptBucket.scope == scope,
                    LoginAttemptBucket.key_digest == digest,
                )
            )
            assert bucket.failure_count == 5
            assert as_utc(bucket.blocked_until) == failures[-1] + timedelta(minutes=15)
        assert not is_rate_limited(db, keys, failures[-1] + timedelta(minutes=15))


def test_failure_exactly_at_fifteen_minute_boundary_counts(auth_client):
    _, factory = auth_client
    start = utc_now()
    keys = (("account_ip", "e" * 64), ("ip", "f" * 64))
    failures = [
        start,
        start + timedelta(minutes=1),
        start + timedelta(minutes=2),
        start + timedelta(minutes=14),
        start + timedelta(minutes=15),
    ]

    for failure_time in failures:
        with factory() as db:
            record_failed_login(db, keys, failure_time)

    with factory() as db:
        assert is_rate_limited(db, keys, failures[-1])


def test_rolling_window_excludes_attempt_just_outside_fifteen_minutes(auth_client):
    _, factory = auth_client
    start = utc_now()
    keys = (("account_ip", "c" * 64), ("ip", "d" * 64))
    failures = [
        start,
        start + timedelta(minutes=1, seconds=2),
        start + timedelta(minutes=2),
        start + timedelta(minutes=14),
        start + timedelta(minutes=15, seconds=1),
    ]

    for failure_time in failures:
        with factory() as db:
            record_failed_login(db, keys, failure_time)

    with factory() as db:
        assert not is_rate_limited(db, keys, failures[-1])
        for scope, digest in keys:
            bucket = db.scalar(
                select(LoginAttemptBucket).where(
                    LoginAttemptBucket.scope == scope,
                    LoginAttemptBucket.key_digest == digest,
                )
            )
            assert bucket.failure_count == 4
            assert bucket.blocked_until is None


def authenticated_user(client, email="person@example.test", password="correct horse"):
    assert register(client, email=email, password=password).status_code == 201
    response = login(client, email=email, password=password)
    assert response.status_code == 200
    return response.json()["user"]


def create_family_user(client, email="other@example.test", password="another secret"):
    csrf = client.cookies[CSRF_COOKIE]
    response = client.post(
        "/api/v1/users",
        headers={"Origin": "http://localhost:5173", "X-CSRF-Token": csrf},
        json={"name": "Other", "email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()["user"]


def test_public_push_key_requires_configured_server(auth_client, monkeypatch):
    """Entrega la clave pública solo cuando el servicio está configurado."""
    client, _ = auth_client
    authenticated_user(client)
    monkeypatch.delenv("PUSH_PUBLIC_KEY", raising=False)
    assert client.get("/api/v1/push/public-key").status_code == 503
    monkeypatch.setenv("PUSH_PUBLIC_KEY", "clave-publica")
    monkeypatch.delenv("PUSH_PRIVATE_KEY", raising=False)
    assert client.get("/api/v1/push/public-key").status_code == 503
    monkeypatch.setenv("PUSH_PRIVATE_KEY", "clave-privada")
    monkeypatch.setenv("PUSH_CONTACT", "mailto:admin@example.test")
    assert client.get("/api/v1/push/public-key").json() == {"public_key": "clave-publica"}


@pytest.mark.parametrize("endpoint", ["http://fcm.googleapis.com/fcm/send/x", "https://127.0.0.1/", "https://fcm.googleapis.com.evil.test/x", "https://user@fcm.googleapis.com/x", "https://evil.test/x"])
def test_push_subscription_rejects_untrusted_endpoints(auth_client, endpoint):
    """Impide registrar destinos arbitrarios para el envío desde el servidor."""
    client, _ = auth_client
    authenticated_user(client)
    headers = {"Origin": "http://localhost:5173", "X-CSRF-Token": client.cookies[CSRF_COOKIE]}
    assert client.post("/api/v1/push/subscriptions", headers=headers, json={"endpoint": endpoint, "keys": {"p256dh": "clave", "auth": "secreto"}}).status_code == 422


def test_push_test_sends_only_to_authenticated_user_devices(auth_client, monkeypatch):
    """Envía la prueba a los dispositivos propios sin notificar a otras cuentas."""
    from app.models import PushSubscription
    import app.auth as autenticacion

    client, factory = auth_client
    first = authenticated_user(client)
    other = create_family_user(client)
    with factory() as db:
        db.add_all([
            PushSubscription(user_id=UUID(first["id"]), endpoint="https://fcm.googleapis.com/fcm/send/propio", p256dh="p", auth="a"),
            PushSubscription(user_id=UUID(other["id"]), endpoint="https://fcm.googleapis.com/fcm/send/otro", p256dh="p", auth="a"),
        ])
        db.commit()
    envios = []
    monkeypatch.setattr(autenticacion, "enviar_push", lambda *args: envios.append(args), raising=False)
    assert client.post("/api/v1/push/test").status_code == 403
    headers = {"Origin": "http://localhost:5173", "X-CSRF-Token": client.cookies[CSRF_COOKIE]}
    response = client.post("/api/v1/push/test", headers=headers)
    assert response.status_code == 204
    assert [envio[0] for envio in envios] == ["https://fcm.googleapis.com/fcm/send/propio"]


def test_push_test_skips_expired_device_and_sends_to_valid_one(auth_client, monkeypatch):
    """Retira una suscripción caducada sin bloquear el envío al resto."""
    from types import SimpleNamespace
    from pywebpush import WebPushException
    from app.models import PushSubscription
    import app.auth as autenticacion

    client, factory = auth_client
    usuario = authenticated_user(client)
    urls = [f"https://fcm.googleapis.com/fcm/send/{sufijo}" for sufijo in ("caducada", "vigente")]
    with factory() as db:
        db.add_all([PushSubscription(user_id=UUID(usuario["id"]), endpoint=url, p256dh="p", auth="a") for url in urls])
        db.commit()
    envios = []

    def enviar(endpoint, *_args):
        """Simula el rechazo definitivo de una suscripción."""
        if endpoint == urls[0]:
            raise WebPushException("expired", response=SimpleNamespace(status_code=410))
        envios.append(endpoint)

    monkeypatch.setattr(autenticacion, "enviar_push", enviar)
    headers = {"Origin": "http://localhost:5173", "X-CSRF-Token": client.cookies[CSRF_COOKIE]}
    assert client.post("/api/v1/push/test", headers=headers).status_code == 204
    assert envios == [urls[1]]
    for url, esperado in zip(urls, (False, True)):
        assert client.post("/api/v1/push/subscriptions/status", headers=headers, json={"endpoint": url}).json() == {"active": esperado}


def test_push_test_reports_missing_subscription_or_delivery_failure(auth_client, monkeypatch):
    """No presenta como entregada una prueba sin dispositivos o con error."""
    from app.models import PushSubscription
    import app.auth as autenticacion

    client, factory = auth_client
    first = authenticated_user(client)
    headers = {"Origin": "http://localhost:5173", "X-CSRF-Token": client.cookies[CSRF_COOKIE]}
    assert client.post("/api/v1/push/test", headers=headers).status_code == 409
    with factory() as db:
        db.add(PushSubscription(user_id=UUID(first["id"]), endpoint="https://fcm.googleapis.com/fcm/send/propio", p256dh="p", auth="a"))
        db.commit()

    def falla(*_args):
        """Simula un error del servicio de notificaciones."""
        raise RuntimeError("delivery failed")

    monkeypatch.setattr(autenticacion, "enviar_push", falla)
    assert client.post("/api/v1/push/test", headers=headers).status_code == 503


def test_push_subscription_belongs_to_current_user_and_can_be_removed(auth_client):
    """Registra y elimina la suscripción del dispositivo para su propia cuenta."""
    client, factory = auth_client
    first = authenticated_user(client)
    headers = {"Origin": "http://localhost:5173", "X-CSRF-Token": client.cookies[CSRF_COOKIE]}
    suscripcion = {"endpoint": "https://fcm.googleapis.com/fcm/send/example", "keys": {"p256dh": "clave-publica", "auth": "secreto"}}
    assert client.post("/api/v1/push/subscriptions", headers=headers, json=suscripcion).status_code == 204
    from app.models import PushSubscription
    with factory() as db:
        guardada = db.scalar(select(PushSubscription))
        assert str(guardada.user_id) == first["id"]
        assert guardada.endpoint == suscripcion["endpoint"]
        assert guardada.p256dh == "clave-publica"
        assert guardada.auth == "secreto"
    assert client.request("DELETE", "/api/v1/push/subscriptions", headers=headers, json={"endpoint": suscripcion["endpoint"]}).status_code == 204
    with factory() as db:
        assert db.scalar(select(PushSubscription)) is None


def test_push_subscription_cannot_be_removed_by_another_user(auth_client):
    """Impide que otra cuenta elimine la suscripción del dispositivo."""
    client, factory = auth_client
    authenticated_user(client)
    create_family_user(client)
    headers = {"Origin": "http://localhost:5173", "X-CSRF-Token": client.cookies[CSRF_COOKIE]}
    endpoint = "https://fcm.googleapis.com/fcm/send/example"
    suscripcion = {"endpoint": endpoint, "keys": {"p256dh": "clave", "auth": "secreto"}}
    assert client.post("/api/v1/push/subscriptions", json=suscripcion).status_code == 403
    assert client.post("/api/v1/push/subscriptions", headers=headers, json=suscripcion).status_code == 204
    client.cookies.clear()
    assert login(client, "other@example.test", "another secret").status_code == 200
    headers["X-CSRF-Token"] = client.cookies[CSRF_COOKIE]
    assert client.request("DELETE", "/api/v1/push/subscriptions", headers=headers, json={"endpoint": endpoint}).status_code == 204
    from app.models import PushSubscription
    with factory() as db:
        assert db.scalar(select(PushSubscription)).endpoint == endpoint


def test_notification_channel_preferences_are_saved_per_user(auth_client):
    """Comprueba que las cuatro combinaciones se guardan por cuenta."""
    client, _ = auth_client
    first = authenticated_user(client)
    other = create_family_user(client)
    headers = {"Origin": "http://localhost:5173", "X-CSRF-Token": client.cookies[CSRF_COOKIE]}

    for correo, movil in [(True, False), (False, True), (True, True), (False, False)]:
        response = client.patch(
            f"/api/v1/users/{first['id']}", headers=headers,
            json={"recordatorios_correo": correo, "recordatorios_push": movil},
        )
        assert response.status_code == 200
        user = client.get(f"/api/v1/users/{first['id']}").json()["user"]
        assert (user["recordatorios_correo"], user["recordatorios_push"]) == (correo, movil)

    other_user = client.get(f"/api/v1/users/{other['id']}").json()["user"]
    assert (other_user["recordatorios_correo"], other_user["recordatorios_push"]) == (True, False)


def test_user_management_edits_profiles_and_rejects_duplicates(auth_client):
    client, _ = auth_client
    first = authenticated_user(client)
    other = create_family_user(client)
    csrf = client.cookies[CSRF_COOKIE]
    headers = {"Origin": "http://localhost:5173", "X-CSRF-Token": csrf}

    listing = client.get("/api/v1/users")
    assert listing.status_code == 200
    assert len(listing.json()["users"]) == 2
    assert all(user["is_active"] is True for user in listing.json()["users"])
    assert client.get(f"/api/v1/users/{other['id']}").status_code == 200
    changed = client.patch(
        f"/api/v1/users/{other['id']}",
        headers=headers,
        json={"name": "  Family member  "},
    )
    assert changed.status_code == 200
    assert changed.json()["user"]["name"] == "Family member"

    duplicate = client.patch(
        f"/api/v1/users/{other['id']}",
        headers=headers,
        json={"email": first["email"].upper()},
    )
    assert duplicate.status_code == 409
    self_deactivation = client.patch(
        f"/api/v1/users/{first['id']}",
        headers=headers,
        json={"is_active": False},
    )
    assert self_deactivation.status_code == 409


def test_deactivation_reactivation_deletion_and_last_active_guards(auth_client):
    client, factory = auth_client
    first = authenticated_user(client)
    other = create_family_user(client)
    other_client = TestClient(app)
    assert login(other_client, "other@example.test", "another secret").status_code == 200
    headers = {
        "Origin": "http://localhost:5173",
        "X-CSRF-Token": client.cookies[CSRF_COOKIE],
    }

    deactivated = client.patch(
        f"/api/v1/users/{other['id']}", headers=headers, json={"is_active": False}
    )
    assert deactivated.status_code == 200
    assert other_client.get("/api/v1/auth/session").status_code == 401
    with factory() as db:
        sessions = db.scalars(
            select(UserSession).where(UserSession.user_id == UUID(other["id"]))
        ).all()
        assert sessions and all(session.revoked_at is not None for session in sessions)

    reactivated = client.patch(
        f"/api/v1/users/{other['id']}", headers=headers, json={"is_active": True}
    )
    assert reactivated.status_code == 200
    assert other_client.get("/api/v1/auth/session").status_code == 401
    assert login(other_client, "other@example.test", "another secret").status_code == 200

    deleted = client.delete(f"/api/v1/users/{other['id']}", headers=headers)
    assert deleted.status_code == 204
    with factory() as db:
        assert db.get(User, UUID(other["id"])) is None
    last_active_delete = client.delete(f"/api/v1/users/{first['id']}", headers=headers)
    assert last_active_delete.status_code == 409


def test_password_change_self_and_other_revokes_sessions(auth_client):
    client, _ = auth_client
    first = authenticated_user(client)
    other = create_family_user(client)
    other_client = TestClient(app)
    assert login(other_client, "other@example.test", "another secret").status_code == 200
    headers = {
        "Origin": "http://localhost:5173",
        "X-CSRF-Token": client.cookies[CSRF_COOKIE],
    }

    own_path = f"/api/v1/users/{first['id']}/password"
    assert client.post(own_path, headers=headers, json={"new_password": "new password"}).status_code == 422
    assert client.post(
        own_path,
        headers=headers,
        json={"current_password": "wrong password", "new_password": "new password"},
    ).status_code == 400

    other_response = client.post(
        f"/api/v1/users/{other['id']}/password",
        headers=headers,
        json={"new_password": "changed other password"},
    )
    assert other_response.status_code == 204
    assert other_client.get("/api/v1/auth/session").status_code == 401
    assert login(other_client, "other@example.test", "changed other password").status_code == 200

    changed_self = client.post(
        own_path,
        headers=headers,
        json={"current_password": "correct horse", "new_password": "changed own password"},
    )
    assert changed_self.status_code == 204
    assert client.get("/api/v1/auth/session").status_code == 401
    assert login(client, password="changed own password").status_code == 200


def test_password_reset_is_generic_hashed_single_use_and_revokes_sessions(
    auth_client, monkeypatch
):
    client, factory = auth_client
    authenticated_user(client)
    sent = []
    monkeypatch.setattr(
        "app.auth.deliver_reset_email_safely",
        lambda recipient, url: sent.append((recipient, url)),
    )
    headers = {"Origin": "http://localhost:5173"}
    known = client.post(
        "/api/v1/password-resets", headers=headers, json={"email": "person@example.test"}
    )
    unknown = client.post(
        "/api/v1/password-resets", headers=headers, json={"email": "missing@example.test"}
    )
    invalid = client.post(
        "/api/v1/password-resets", headers=headers, json={"email": "not-an-email"}
    )
    assert known.status_code == unknown.status_code == invalid.status_code == 202
    assert known.json() == unknown.json() == invalid.json()
    assert len(sent) == 1
    assert sent[0][0] == "person@example.test"
    reset_token = parse_qs(urlparse(sent[0][1]).query)["reset_token"][0]
    with factory() as db:
        record = db.scalar(select(PasswordResetToken))
        assert record.token_digest == digest_token(reset_token)
        assert reset_token not in record.token_digest

    confirmed = client.post(
        "/api/v1/password-resets/confirm",
        headers=headers,
        json={"token": reset_token, "new_password": "recovered password"},
    )
    assert confirmed.status_code == 204
    assert client.get("/api/v1/auth/session").status_code == 401
    reused = client.post(
        "/api/v1/password-resets/confirm",
        headers=headers,
        json={"token": reset_token, "new_password": "another password"},
    )
    assert reused.status_code == 400
    assert login(client, password="recovered password").status_code == 200


def test_password_reset_request_limits_are_rolling_and_separate_by_scope(auth_client):
    _, factory = auth_client
    start = utc_now()
    account_email = "limited@example.test"
    shared_ip = "203.0.113.99"
    for offset in range(3):
        with factory() as db:
            assert allow_password_reset_request(
                db,
                password_reset_rate_keys(account_email, shared_ip),
                start + timedelta(seconds=offset),
            )
    with factory() as db:
        assert not allow_password_reset_request(
            db,
            password_reset_rate_keys(account_email, "203.0.113.100"),
            start + timedelta(seconds=4),
        )

    separate_ip = "203.0.113.101"
    for account_number in range(10):
        with factory() as db:
            assert allow_password_reset_request(
                db,
                password_reset_rate_keys(f"user{account_number}@example.test", separate_ip),
                start + timedelta(seconds=account_number),
            )
    with factory() as db:
        assert not allow_password_reset_request(
            db,
            password_reset_rate_keys("eleventh@example.test", separate_ip),
            start + timedelta(seconds=11),
        )

    with factory() as db:
        assert allow_password_reset_request(
            db,
            password_reset_rate_keys(account_email, shared_ip),
            start + timedelta(hours=1, seconds=1),
        )


def test_expired_password_reset_token_is_rejected(auth_client):
    client, factory = auth_client
    authenticated_user(client)
    token = generate_token()
    with factory() as db:
        user = db.scalar(select(User))
        now = utc_now()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_digest=digest_token(token),
                created_at=now - timedelta(minutes=31),
                expires_at=now - timedelta(seconds=1),
            )
        )
        db.commit()

    response = client.post(
        "/api/v1/password-resets/confirm",
        headers={"Origin": "http://localhost:5173"},
        json={"token": token, "new_password": "recovered password"},
    )
    assert response.status_code == 400
