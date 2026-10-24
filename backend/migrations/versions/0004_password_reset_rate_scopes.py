"""Amplía los ámbitos de limitación de recuperación.

Actualiza las restricciones de ámbitos de limitación para incluir las solicitudes de restablecimiento.
Revisión: 0004_password_reset_rate_scopes. Anterior: 0003_login_attempt_events.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004_password_reset_rate_scopes"
down_revision: Union[str, None] = "0003_login_attempt_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Amplía la validación de ámbitos sin alterar los datos existentes.
    op.drop_constraint(
        "ck_login_attempt_bucket_scope", "login_attempt_buckets", type_="check"
    )
    op.create_check_constraint(
        "ck_login_attempt_bucket_scope",
        "login_attempt_buckets",
        "scope IN ('ip', 'account_ip', 'reset_ip', 'reset_account')",
    )
    op.drop_constraint(
        "ck_login_attempt_event_scope", "login_attempt_events", type_="check"
    )
    op.create_check_constraint(
        "ck_login_attempt_event_scope",
        "login_attempt_events",
        "scope IN ('ip', 'account_ip', 'reset_ip', 'reset_account')",
    )


def downgrade() -> None:
    # Restaura la restricción anterior; requiere que no queden ámbitos nuevos.
    op.execute(
        "DELETE FROM login_attempt_events WHERE scope IN ('reset_ip', 'reset_account')"
    )
    op.execute(
        "DELETE FROM login_attempt_buckets WHERE scope IN ('reset_ip', 'reset_account')"
    )
    op.drop_constraint(
        "ck_login_attempt_event_scope", "login_attempt_events", type_="check"
    )
    op.create_check_constraint(
        "ck_login_attempt_event_scope",
        "login_attempt_events",
        "scope IN ('ip', 'account_ip')",
    )
    op.drop_constraint(
        "ck_login_attempt_bucket_scope", "login_attempt_buckets", type_="check"
    )
    op.create_check_constraint(
        "ck_login_attempt_bucket_scope",
        "login_attempt_buckets",
        "scope IN ('ip', 'account_ip')",
    )
