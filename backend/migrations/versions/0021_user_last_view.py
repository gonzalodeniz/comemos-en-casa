"""Añade al usuario la última vista abierta."""

from alembic import op
import sqlalchemy as sa

revision = "0021_user_last_view"
down_revision = "0020_backup_schedule"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Añade la vista opcional para las cuentas existentes y nuevas."""
    op.add_column("users", sa.Column("ultima_vista", sa.String(32), nullable=True))


def downgrade() -> None:
    """Elimina la vista guardada de cada usuario."""
    op.drop_column("users", "ultima_vista")
