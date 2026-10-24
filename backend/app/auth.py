"""Autentica usuarios y administra sus sesiones.

Agrupa los flujos de acceso, administración y recuperación de cuentas, aplicando controles CSRF, límites de intentos y coordinación de operaciones concurrentes.
"""

import logging
import threading
import asyncio
import hmac
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from email_validator import EmailNotValidError

from app.database import get_database_session
from app.models import (
    LoginAttemptBucket,
    LoginAttemptEvent,
    PasswordResetToken,
    User,
    UserSession,
)
from app.mailer import send_password_reset_email
from app.security import (
    canonicalize_email,
    digest_rate_limit_key,
    digest_token,
    generate_token,
    hash_password,
    verify_password,
)
from app.settings import allowed_origins, public_app_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["authentication"])

SESSION_COOKIE = "session"
CSRF_COOKIE = "csrf_token"
SESSION_IDLE_TIMEOUT = timedelta(minutes=30)
SESSION_ABSOLUTE_TIMEOUT = timedelta(hours=8)
LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_LOCK_DURATION = timedelta(minutes=15)
LOGIN_FAILURE_LIMIT = 5
RESET_WINDOW = timedelta(hours=1)
RESET_ACCOUNT_LIMIT = 3
RESET_IP_LIMIT = 10
INITIAL_REGISTRATION_LOCK = 1128481601
USER_LIFECYCLE_LOCK = 1128481602
_initial_registration_lock = threading.Lock()
_user_lifecycle_lock = threading.Lock()


class UserCredentials(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def normalize_nonblank_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be blank")
        return normalized


class LoginCredentials(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=4096)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    email: str | None = Field(default=None, min_length=3, max_length=320)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_nonblank_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be blank")
        return normalized


class PasswordUpdate(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)
    current_password: str | None = Field(default=None, min_length=1, max_length=128)


class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=1, max_length=320)


class PasswordResetConfirmation(BaseModel):
    token: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


@dataclass(frozen=True)
class ActiveSession:
    user: User
    session: UserSession


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def require_allowed_origin(request: Request) -> None:
    origin = request.headers.get("origin", "").rstrip("/")
    if not origin or origin not in allowed_origins():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request origin is not allowed",
        )


def require_csrf(request: Request, active_session: ActiveSession) -> None:
    require_allowed_origin(request)
    cookie_token = request.cookies.get(CSRF_COOKIE, "")
    header_token = request.headers.get("x-csrf-token", "")
    if (
        not cookie_token
        or not header_token
        or not hmac.compare_digest(cookie_token, header_token)
        or not hmac.compare_digest(
            digest_token(cookie_token), active_session.session.csrf_token_digest
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )


async def get_active_session(
    request: Request,
    db: Session = Depends(get_database_session),
) -> ActiveSession:
    # Revoca sesiones caducadas o de cuentas inactivas antes de aceptar la petición.
    token = request.cookies.get(SESSION_COOKIE, "")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        active_session = db.scalar(
            select(UserSession).where(UserSession.token_digest == digest_token(token))
        )
        if active_session is None or active_session.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        now = utc_now()
        if (
            as_utc(active_session.idle_expires_at) <= now
            or as_utc(active_session.absolute_expires_at) <= now
        ):
            active_session.revoked_at = now
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        user = db.get(User, active_session.user_id)
        if user is None or not user.is_active:
            active_session.revoked_at = now
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        active_session.last_seen_at = now
        active_session.idle_expires_at = min(
            now + SESSION_IDLE_TIMEOUT,
            as_utc(active_session.absolute_expires_at),
        )
        db.commit()
        return ActiveSession(user=user, session=active_session)
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("session_lookup_failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from error


def public_user(user: User) -> dict[str, str]:
    return {"id": str(user.id), "name": user.name, "email": user.email}


def revoke_user_sessions(db: Session, user_id: UUID, now: datetime) -> None:
    db.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )


def deliver_reset_email_safely(recipient: str, reset_url: str) -> None:
    try:
        send_password_reset_email(recipient, reset_url)
    except Exception:
        logger.warning("password_reset_delivery_failed")


@asynccontextmanager
async def lock_user_lifecycle(db: Session):
    # Serializa cambios de cuentas entre procesos en PostgreSQL y entre hilos en SQLite.
    if db.get_bind().dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": USER_LIFECYCLE_LOCK},
        )
        yield
        return

    await asyncio.to_thread(_user_lifecycle_lock.acquire)
    try:
        yield
    finally:
        _user_lifecycle_lock.release()


def client_ip(request: Request) -> str:
    if request.client is None:
        return "unknown"
    return request.client.host


def rate_limit_digests(email_key: str, ip: str) -> tuple[tuple[str, str], tuple[str, str]]:
    return (
        ("account_ip", digest_rate_limit_key(f"account_ip:{email_key}:{ip}")),
        ("ip", digest_rate_limit_key(f"ip:{ip}")),
    )


def is_rate_limited(
    db: Session, keys: tuple[tuple[str, str], tuple[str, str]], now: datetime
) -> bool:
    rows = db.scalars(
        select(LoginAttemptBucket).where(
            or_(
                (LoginAttemptBucket.scope == keys[0][0])
                & (LoginAttemptBucket.key_digest == keys[0][1]),
                (LoginAttemptBucket.scope == keys[1][0])
                & (LoginAttemptBucket.key_digest == keys[1][1]),
            )
        )
    )
    return any(row.blocked_until and as_utc(row.blocked_until) > now for row in rows)


def increment_failure_bucket(
    db: Session, scope: str, key_digest: str, now: datetime
) -> None:
    # Calcula el umbral con eventos recientes, no con una ventana fija que pueda reiniciarse al fallar.
    bucket = lock_attempt_bucket(db, scope, key_digest, now)
    cutoff = now - LOGIN_WINDOW
    db.add(LoginAttemptEvent(scope=scope, key_digest=key_digest, attempted_at=now))
    db.flush()
    rolling_events = select(func.count()).select_from(LoginAttemptEvent).where(
        LoginAttemptEvent.scope == scope,
        LoginAttemptEvent.key_digest == key_digest,
        LoginAttemptEvent.attempted_at >= cutoff,
    )
    failure_count = int(db.scalar(rolling_events) or 0)
    first_event = db.scalar(
        select(func.min(LoginAttemptEvent.attempted_at)).where(
            LoginAttemptEvent.scope == scope,
            LoginAttemptEvent.key_digest == key_digest,
            LoginAttemptEvent.attempted_at >= cutoff,
        )
    )
    bucket.window_started_at = first_event or now
    bucket.failure_count = failure_count
    if not bucket.blocked_until or as_utc(bucket.blocked_until) <= now:
        bucket.blocked_until = (
            now + LOGIN_LOCK_DURATION
            if failure_count >= LOGIN_FAILURE_LIMIT
            else None
        )
    bucket.updated_at = now


def lock_attempt_bucket(
    db: Session, scope: str, key_digest: str, now: datetime
) -> LoginAttemptBucket:
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        insert = postgres_insert
    elif dialect == "sqlite":
        insert = sqlite_insert
    else:
        raise RuntimeError("Authentication rate limits require PostgreSQL")

    bucket_table = LoginAttemptBucket.__table__
    statement = insert(bucket_table).values(
        scope=scope,
        key_digest=key_digest,
        window_started_at=now,
        failure_count=0,
        blocked_until=None,
        updated_at=now,
    )
    db.execute(statement.on_conflict_do_nothing(
        index_elements=[bucket_table.c.scope, bucket_table.c.key_digest]
    ))
    bucket = db.scalar(
        select(LoginAttemptBucket)
        .where(
            LoginAttemptBucket.scope == scope,
            LoginAttemptBucket.key_digest == key_digest,
        )
        .with_for_update()
    )
    if bucket is None:
        raise RuntimeError("Failed to initialize login attempt bucket")
    return bucket


def record_failed_login(
    db: Session, keys: tuple[tuple[str, str], tuple[str, str]], now: datetime
) -> None:
    db.execute(
        delete(LoginAttemptEvent).where(
            LoginAttemptEvent.scope.in_(("ip", "account_ip")),
            LoginAttemptEvent.attempted_at < now - LOGIN_WINDOW
        )
    )
    for scope, key_digest in keys:
        increment_failure_bucket(db, scope, key_digest, now)
    db.commit()


def password_reset_rate_keys(email_key: str, ip: str) -> tuple[tuple[str, str, int], ...]:
    return (
        (
            "reset_account",
            digest_rate_limit_key(f"reset_account:{email_key}"),
            RESET_ACCOUNT_LIMIT,
        ),
        ("reset_ip", digest_rate_limit_key(f"reset_ip:{ip}"), RESET_IP_LIMIT),
    )


def allow_password_reset_request(
    db: Session,
    keys: tuple[tuple[str, str, int], ...],
    now: datetime,
) -> bool:
    # Aplica cuotas independientes por cuenta e IP antes de crear tokens o enviar correo.
    cutoff = now - RESET_WINDOW
    db.execute(
        delete(LoginAttemptEvent).where(
            LoginAttemptEvent.scope.in_(("reset_account", "reset_ip")),
            LoginAttemptEvent.attempted_at < cutoff,
        )
    )
    buckets = [lock_attempt_bucket(db, scope, key_digest, now) for scope, key_digest, _ in keys]
    counts = [
        int(
            db.scalar(
                select(func.count())
                .select_from(LoginAttemptEvent)
                .where(
                    LoginAttemptEvent.scope == scope,
                    LoginAttemptEvent.key_digest == key_digest,
                    LoginAttemptEvent.attempted_at >= cutoff,
                )
            )
            or 0
        )
        for scope, key_digest, _ in keys
    ]
    if any(count >= limit for count, (_, _, limit) in zip(counts, keys, strict=True)):
        db.rollback()
        return False

    for scope, key_digest, _ in keys:
        db.add(LoginAttemptEvent(scope=scope, key_digest=key_digest, attempted_at=now))
    db.flush()
    for (scope, key_digest, _), bucket, count in zip(keys, buckets, counts, strict=True):
        bucket.failure_count = count + 1
        bucket.window_started_at = db.scalar(
            select(func.min(LoginAttemptEvent.attempted_at)).where(
                LoginAttemptEvent.scope == scope,
                LoginAttemptEvent.key_digest == key_digest,
                LoginAttemptEvent.attempted_at >= cutoff,
            )
        ) or now
        bucket.updated_at = now
    db.commit()
    return True


async def create_user(db: Session, credentials: UserCredentials) -> User:
    try:
        original_email, canonical_email = canonicalize_email(credentials.email)
    except EmailNotValidError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A valid email address is required",
        ) from error

    user = User(
        name=credentials.name.strip(),
        email=original_email,
        email_canonical=canonical_email,
        password_hash=await asyncio.to_thread(hash_password, credentials.password),
    )
    db.add(user)
    return user


def issue_session(
    db: Session,
    user: User,
    request: Request,
    response: Response,
) -> None:
    now = utc_now()
    session_token = generate_token()
    csrf_token = generate_token()
    db.add(
        UserSession(
            user_id=user.id,
            token_digest=digest_token(session_token),
            csrf_token_digest=digest_token(csrf_token),
            created_at=now,
            last_seen_at=now,
            idle_expires_at=now + SESSION_IDLE_TIMEOUT,
            absolute_expires_at=now + SESSION_ABSOLUTE_TIMEOUT,
        )
    )
    db.commit()
    secure = request.url.scheme == "https"
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        httponly=False,
        secure=secure,
        samesite="lax",
        path="/",
    )


@asynccontextmanager
async def lock_first_registration(db: Session):
    if db.get_bind().dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": INITIAL_REGISTRATION_LOCK},
        )
        yield
        return

    await asyncio.to_thread(_initial_registration_lock.acquire)
    try:
        yield
    finally:
        _initial_registration_lock.release()


@router.get("/auth/bootstrap")
async def bootstrap(db: Session = Depends(get_database_session)) -> dict[str, bool]:
    count = db.scalar(select(func.count()).select_from(User))
    return {"initial_account_required": count == 0}


@router.post("/auth/register-initial", status_code=status.HTTP_201_CREATED)
async def register_initial(
    credentials: UserCredentials,
    request: Request,
    response: Response,
    db: Session = Depends(get_database_session),
) -> dict[str, dict[str, str]]:
    require_allowed_origin(request)
    try:
        async with lock_first_registration(db):
            count = db.scalar(select(func.count()).select_from(User))
            if count:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Initial registration is closed",
                )
            user = await create_user(db, credentials)
            db.commit()
            db.refresh(user)
            response.headers["Cache-Control"] = "no-store"
            return {"user": public_user(user)}
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account cannot be created",
        ) from error
    except HTTPException:
        db.rollback()
        raise


@router.post("/auth/login")
async def login(
    credentials: LoginCredentials,
    request: Request,
    response: Response,
    db: Session = Depends(get_database_session),
) -> dict[str, dict[str, str]]:
    # Mantiene errores indistinguibles y verifica una contraseña ficticia si la cuenta no existe.
    require_allowed_origin(request)
    try:
        _, email_key = canonicalize_email(credentials.email)
    except Exception:
        email_key = credentials.email.strip().casefold()

    ip = client_ip(request)
    try:
        keys = rate_limit_digests(email_key, ip)
        now = utc_now()
        if is_rate_limited(db, keys, now):
            logger.warning("login_denied_by_rate_limit")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        user = db.scalar(select(User).where(User.email_canonical == email_key))
        usable_hash = user.password_hash if user and user.is_active else None
        if len(credentials.password) > 128:
            await asyncio.to_thread(verify_password, None, credentials.password)
            valid_password = False
        else:
            valid_password = await asyncio.to_thread(
                verify_password, usable_hash, credentials.password
            )

        if user is None or not user.is_active or not valid_password:
            record_failed_login(db, keys, now)
            logger.warning("login_failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        issue_session(db, user, request, response)
        response.headers["Cache-Control"] = "no-store"
        return {"user": public_user(user)}
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("login_storage_failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from error
    except RuntimeError as error:
        db.rollback()
        logger.error("login_rate_limit_configuration_failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from error


@router.get("/auth/session")
async def current_session(
    request: Request,
    response: Response,
    active_session: ActiveSession = Depends(get_active_session),
) -> dict[str, object]:
    csrf_token = request.cookies.get(CSRF_COOKIE, "")
    if digest_token(csrf_token) != active_session.session.csrf_token_digest:
        csrf_token = ""
    response.headers["Cache-Control"] = "no-store"
    return {"user": public_user(active_session.user), "csrf_token": csrf_token}


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> Response:
    require_csrf(request, active_session)
    active_session.session.revoked_at = utc_now()
    db.commit()
    secure = request.url.scheme == "https"
    response.delete_cookie(SESSION_COOKIE, path="/", secure=secure, httponly=True, samesite="lax")
    response.delete_cookie(CSRF_COOKIE, path="/", secure=secure, httponly=False, samesite="lax")
    response.headers["Cache-Control"] = "no-store"
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def register_family_member(
    credentials: UserCredentials,
    request: Request,
    response: Response,
    active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, dict[str, str]]:
    require_csrf(request, active_session)
    try:
        user = await create_user(db, credentials)
        db.commit()
        db.refresh(user)
        response.headers["Cache-Control"] = "no-store"
        return {"user": public_user(user)}
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account cannot be created",
        ) from error


@router.get("/users")
async def list_users(
    active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, list[dict[str, str | bool]]]:
    users = db.scalars(select(User).order_by(User.name, User.email_canonical)).all()
    return {"users": [public_user(user) | {"is_active": user.is_active} for user in users]}


@router.get("/users/{user_id}")
async def get_user(
    user_id: UUID,
    active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, dict[str, object]]:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"user": public_user(user) | {"is_active": user.is_active}}


@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    changes: UserUpdate,
    request: Request,
    active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, dict[str, object]]:
    # El bloqueo de ciclo de vida serializa el recuento y el cambio para conservar una cuenta activa.
    require_csrf(request, active_session)
    if not changes.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="At least one user field must be provided",
        )

    try:
        async with lock_user_lifecycle(db):
            user = db.get(User, user_id)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            if changes.is_active is False:
                if user.id == active_session.user.id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="You cannot deactivate your own account",
                    )
                if user.is_active:
                    active_count = db.scalar(
                        select(func.count()).select_from(User).where(User.is_active.is_(True))
                    )
                    if active_count <= 1:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="The last active account cannot be deactivated",
                        )
                    user.is_active = False
                    revoke_user_sessions(db, user.id, utc_now())
            elif changes.is_active is True:
                user.is_active = True

            if changes.name is not None:
                user.name = changes.name
            if changes.email is not None:
                try:
                    original_email, canonical_email = canonicalize_email(changes.email)
                except EmailNotValidError as error:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="A valid email address is required",
                    ) from error
                user.email = original_email
                user.email_canonical = canonical_email

            user.updated_at = utc_now()
            db.commit()
            db.refresh(user)
            return {"user": public_user(user) | {"is_active": user.is_active}}
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already in use",
        ) from error
    except HTTPException:
        db.rollback()
        raise


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    request: Request,
    response: Response,
    active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> Response:
    # Serializa la comprobación de última cuenta con el borrado y revoca sesiones antes de eliminar.
    require_csrf(request, active_session)
    try:
        async with lock_user_lifecycle(db):
            user = db.get(User, user_id)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )
            if user.is_active:
                active_count = db.scalar(
                    select(func.count()).select_from(User).where(User.is_active.is_(True))
                )
                if active_count <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="The last active account cannot be deleted",
                    )
            revoke_user_sessions(db, user.id, utc_now())
            db.delete(user)
            db.commit()
    except HTTPException:
        db.rollback()
        raise

    if user.id == active_session.user.id:
        secure = request.url.scheme == "https"
        response.delete_cookie(SESSION_COOKIE, path="/", secure=secure, httponly=True, samesite="lax")
        response.delete_cookie(CSRF_COOKIE, path="/", secure=secure, httponly=False, samesite="lax")
    response.headers["Cache-Control"] = "no-store"
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/users/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_password(
    user_id: UUID,
    credentials: PasswordUpdate,
    request: Request,
    response: Response,
    active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> Response:
    # Exige la contraseña actual al titular; cualquier cambio invalida las sesiones previas del usuario.
    require_csrf(request, active_session)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    changing_own_password = user.id == active_session.user.id
    if changing_own_password:
        if credentials.current_password is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Current password is required",
            )
        current_password_matches = await asyncio.to_thread(
            verify_password, user.password_hash, credentials.current_password
        )
        if not current_password_matches:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

    user.password_hash = await asyncio.to_thread(hash_password, credentials.new_password)
    user.updated_at = utc_now()
    revoke_user_sessions(db, user.id, user.updated_at)
    db.commit()
    if changing_own_password:
        secure = request.url.scheme == "https"
        response.delete_cookie(SESSION_COOKIE, path="/", secure=secure, httponly=True, samesite="lax")
        response.delete_cookie(CSRF_COOKIE, path="/", secure=secure, httponly=False, samesite="lax")
    response.headers["Cache-Control"] = "no-store"
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/password-resets", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    credentials: PasswordResetRequest,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database_session),
) -> dict[str, str]:
    # Devuelve siempre el mismo mensaje para no revelar si el correo está registrado.
    require_allowed_origin(request)
    generic_message = "If the account exists, reset instructions will be sent."
    response.headers["Cache-Control"] = "no-store"
    try:
        app_url = public_app_url()
    except RuntimeError as error:
        logger.error("password_reset_public_url_not_configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset is temporarily unavailable",
        ) from error

    try:
        _, email_key = canonicalize_email(credentials.email)
        user = db.scalar(select(User).where(User.email_canonical == email_key))
    except EmailNotValidError:
        email_key = credentials.email.strip().casefold()
        user = None

    keys = password_reset_rate_keys(email_key, client_ip(request))
    try:
        allowed = allow_password_reset_request(db, keys, utc_now())
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("password_reset_limit_storage_failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset is temporarily unavailable",
        ) from error
    except RuntimeError as error:
        db.rollback()
        logger.error("password_reset_limit_configuration_failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset is temporarily unavailable",
        ) from error

    if allowed and user is not None and user.is_active:
        token = generate_token()
        now = utc_now()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_digest=digest_token(token),
                created_at=now,
                expires_at=now + timedelta(minutes=30),
            )
        )
        db.commit()
        background_tasks.add_task(
            deliver_reset_email_safely,
            user.email,
            f"{app_url}/?reset_token={quote(token)}",
        )
    return {"message": generic_message}


@router.post("/password-resets/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    confirmation: PasswordResetConfirmation,
    request: Request,
    response: Response,
    db: Session = Depends(get_database_session),
) -> Response:
    # Solo acepta tokens no usados y aún vigentes; el bloqueo y la transacción evitan su consumo concurrente.
    # El mismo commit marca el token como usado, cambia la contraseña y revoca las sesiones.
    require_allowed_origin(request)
    now = utc_now()
    try:
        reset_token = db.scalar(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token_digest == digest_token(confirmation.token),
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
            .with_for_update()
        )
        if reset_token is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset link is invalid or expired",
            )
        user = db.scalar(
            select(User).where(User.id == reset_token.user_id).with_for_update()
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset link is invalid or expired",
            )
        reset_token.used_at = now
        user.password_hash = await asyncio.to_thread(
            hash_password, confirmation.new_password
        )
        user.updated_at = now
        revoke_user_sessions(db, user.id, now)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("password_reset_confirmation_storage_failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset is temporarily unavailable",
        ) from error

    response.headers["Cache-Control"] = "no-store"
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
