"""Añade el registro histórico de intentos de acceso.

Persiste cada intento con su ámbito y fecha para calcular ventanas móviles sin guardar identificadores en claro.
Revisión: 0003_login_attempt_events. Anterior: 0002_user_auth.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_login_attempt_events"
down_revision: Union[str, None] = "0002_user_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Añade el historial necesario para calcular intentos dentro de ventanas móviles.
    op.create_table(
        "login_attempt_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("key_digest", sa.String(length=64), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "scope IN ('ip', 'account_ip')", name="ck_login_attempt_event_scope"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_login_attempt_events"),
    )
    op.create_index(
        "ix_login_attempt_events_scope_key_time",
        "login_attempt_events",
        ["scope", "key_digest", "attempted_at"],
    )
    op.create_index(
        "ix_login_attempt_events_attempted_at",
        "login_attempt_events",
        ["attempted_at"],
    )


def downgrade() -> None:
    # Retira primero las estructuras del historial antes de eliminar la tabla.
    op.drop_index(
        "ix_login_attempt_events_scope_key_time", table_name="login_attempt_events"
    )
    op.drop_index(
        "ix_login_attempt_events_attempted_at", table_name="login_attempt_events"
    )
    op.drop_table("login_attempt_events")
