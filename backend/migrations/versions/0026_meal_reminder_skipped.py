"""Conserva la configuración de los recordatorios omitidos al programarlos."""
from alembic import op
import sqlalchemy as sa

# Identifica la revisión y su posición en la cadena de migraciones.
revision = "0026_meal_reminder_skipped"
down_revision = "0025_notification_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Añade el estado sin cambiar los recordatorios existentes."""
    op.add_column("meal_assignments", sa.Column("reminder_skipped", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    """Retira la marca sin dejar avisos omitidos disponibles para envío."""
    op.execute("UPDATE meal_assignments SET reminder_days = NULL, reminder_time = NULL, reminder_message = NULL WHERE reminder_skipped")
    op.drop_column("meal_assignments", "reminder_skipped")
