"""Define las entidades persistentes de la aplicación.

Las restricciones e índices respaldan invariantes de cuentas, planificación, recuperación de contraseñas y limitación de intentos.
"""

from datetime import date, datetime
from uuid import UUID, uuid4
import unicodedata

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email_canonical", name="uq_users_email_canonical"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    email_canonical: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        default=True, server_default="true", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_user_revoked", "user_id", "revoked_at"),
        Index("ix_user_sessions_idle_expires_at", "idle_expires_at"),
        Index("ix_user_sessions_absolute_expires_at", "absolute_expires_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_digest: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    csrf_token_digest: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    idle_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    absolute_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("ix_password_reset_tokens_user_expires", "user_id", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_digest: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LoginAttemptBucket(Base):
    __tablename__ = "login_attempt_buckets"
    __table_args__ = (
        UniqueConstraint("scope", "key_digest", name="uq_login_attempt_bucket_key"),
        CheckConstraint(
            "scope IN ('ip', 'account_ip', 'reset_ip', 'reset_account')",
            name="ck_login_attempt_bucket_scope",
        ),
        CheckConstraint("failure_count >= 0", name="ck_login_attempt_failure_count"),
        Index("ix_login_attempt_buckets_blocked_until", "blocked_until"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)
    key_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    window_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LoginAttemptEvent(Base):
    __tablename__ = "login_attempt_events"
    __table_args__ = (
        CheckConstraint(
            "scope IN ('ip', 'account_ip', 'reset_ip', 'reset_account')",
            name="ck_login_attempt_event_scope",
        ),
        Index(
            "ix_login_attempt_events_scope_key_time",
            "scope",
            "key_digest",
            "attempted_at",
        ),
        Index("ix_login_attempt_events_attempted_at", "attempted_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)
    key_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FoodLabel(Base):
    __tablename__ = "food_labels"
    __table_args__ = (
        UniqueConstraint("code", name="uq_food_labels_code"),
        UniqueConstraint("name_canonical", name="uq_food_labels_name_canonical"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_canonical: Mapped[str] = mapped_column(
        Text, nullable=False,
        default=lambda context: unicodedata.normalize(
            "NFC", context.get_current_parameters()["name"].strip()
        ).casefold(),
    )
    image_path: Mapped[str | None] = mapped_column(String(255))


class MealAssignment(Base):
    __tablename__ = "meal_assignments"
    __table_args__ = (
        UniqueConstraint("date", "slot", name="uq_meal_assignments_date_slot"),
        CheckConstraint(
            "slot IN ('lunch', 'dinner')",
            name="ck_meal_assignments_slot",
        ),
        Index("ix_meal_assignments_label_id", "label_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    slot: Mapped[str] = mapped_column(String(16), nullable=False)
    label_id: Mapped[UUID] = mapped_column(
        ForeignKey("food_labels.id", ondelete="RESTRICT"), nullable=False
    )
