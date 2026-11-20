"""Añade configuración de recordatorios a las comidas planificadas."""
from alembic import op
import sqlalchemy as sa

revision = "0024_meal_reminders"
down_revision = "0023_kitchen_tips"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Añade campos opcionales para avisos de cada asignación."""
    op.add_column("meal_assignments", sa.Column("reminder_days", sa.Integer(), nullable=True))
    op.add_column("meal_assignments", sa.Column("reminder_time", sa.String(length=5), nullable=True))
    op.add_column("meal_assignments", sa.Column("reminder_message", sa.Text(), nullable=True))
    op.add_column("meal_assignments", sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Retira la configuración de recordatorios."""
    op.drop_column("meal_assignments", "reminder_sent_at")
    op.drop_column("meal_assignments", "reminder_message")
    op.drop_column("meal_assignments", "reminder_time")
    op.drop_column("meal_assignments", "reminder_days")
