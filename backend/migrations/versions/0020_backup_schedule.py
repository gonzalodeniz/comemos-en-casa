"""Persiste la frecuencia y el límite global de copias automáticas."""
from alembic import op
import sqlalchemy as sa

revision = "0020_backup_schedule"
down_revision = "0019_product_name_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crea la tabla singleton de configuración de copias."""
    op.create_table(
        "backup_schedule",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("frequency", sa.String(16), nullable=False),
        sa.Column("maximum", sa.Integer(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("id = 1", name="ck_backup_schedule_singleton"),
        sa.CheckConstraint("frequency IN ('daily', 'weekly')", name="ck_backup_schedule_frequency"),
        sa.CheckConstraint("maximum >= 1", name="ck_backup_schedule_maximum"),
    )


def downgrade() -> None:
    """Elimina la configuración global de copias automáticas."""
    op.drop_table("backup_schedule")
