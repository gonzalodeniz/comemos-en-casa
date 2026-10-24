"""Crea las tablas persistentes de autenticación.

Define cuentas, sesiones y tokens de recuperación con restricciones para proteger unicidad y relaciones.
Revisión: 0002_user_auth. Anterior: 0001_baseline.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_user_auth"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crea las tablas base con UUID, claves únicas e índices para sesiones y tokens.
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("email_canonical", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email_canonical", name="uq_users_email_canonical"),
    )
    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_digest", sa.String(length=64), nullable=False),
        sa.Column("csrf_token_digest", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("idle_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_user_sessions_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_user_sessions"),
        sa.UniqueConstraint("token_digest", name="uq_user_sessions_token_digest"),
        sa.UniqueConstraint("csrf_token_digest", name="uq_user_sessions_csrf_token_digest"),
    )
    op.create_index("ix_user_sessions_user_revoked", "user_sessions", ["user_id", "revoked_at"])
    op.create_index("ix_user_sessions_idle_expires_at", "user_sessions", ["idle_expires_at"])
    op.create_index("ix_user_sessions_absolute_expires_at", "user_sessions", ["absolute_expires_at"])

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_digest", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_password_reset_tokens_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_password_reset_tokens"),
        sa.UniqueConstraint("token_digest", name="uq_password_reset_tokens_token_digest"),
    )
    op.create_index("ix_password_reset_tokens_user_expires", "password_reset_tokens", ["user_id", "expires_at"])

    op.create_table(
        "login_attempt_buckets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("key_digest", sa.String(length=64), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("scope IN ('ip', 'account_ip')", name="ck_login_attempt_bucket_scope"),
        sa.CheckConstraint("failure_count >= 0", name="ck_login_attempt_failure_count"),
        sa.PrimaryKeyConstraint("id", name="pk_login_attempt_buckets"),
        sa.UniqueConstraint("scope", "key_digest", name="uq_login_attempt_bucket_key"),
    )
    op.create_index("ix_login_attempt_buckets_blocked_until", "login_attempt_buckets", ["blocked_until"])


def downgrade() -> None:
    # Elimina las tablas en orden inverso para respetar las claves foráneas.
    op.drop_index("ix_login_attempt_buckets_blocked_until", table_name="login_attempt_buckets")
    op.drop_table("login_attempt_buckets")
    op.drop_index("ix_password_reset_tokens_user_expires", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_index("ix_user_sessions_absolute_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_idle_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_revoked", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_table("users")
