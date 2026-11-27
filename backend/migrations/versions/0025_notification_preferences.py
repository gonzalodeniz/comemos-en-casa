"""Conserva las preferencias de canales de recordatorios por usuario."""
from alembic import op
import sqlalchemy as sa

revision = "0025_notification_preferences"
down_revision = "0024_meal_reminders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Mantiene el correo activo y el canal móvil desactivado inicialmente."""
    op.add_column("users", sa.Column("recordatorios_correo", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("recordatorios_push", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_table("push_subscriptions", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("endpoint", sa.String(2048), nullable=False, unique=True), sa.Column("p256dh", sa.String(256), nullable=False), sa.Column("auth", sa.String(256), nullable=False))
    op.create_index("ix_push_subscriptions_user_id", "push_subscriptions", ["user_id"])


def downgrade() -> None:
    """Retira las preferencias de canales de recordatorios."""
    op.drop_table("push_subscriptions")
    op.drop_column("users", "recordatorios_push")
    op.drop_column("users", "recordatorios_correo")
