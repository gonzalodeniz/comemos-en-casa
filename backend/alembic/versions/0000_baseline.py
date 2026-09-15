"""Record the historical SQL migrations as Alembic's starting point.

Existing databases that already applied ``backend/migrations/versions`` are
bootstrapped with ``alembic stamp 0000_baseline``. The SQL files remain the
historical migration record and are intentionally not replayed by Alembic.
"""

revision = "0000_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create no schema objects: historical SQL is the baseline."""


def downgrade() -> None:
    """Remove no schema objects: the historical baseline is irreversible."""
