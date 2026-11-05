"""Añade el estado de compra a los elementos de la lista."""
from alembic import op
import sqlalchemy as sa

revision = "0011_shopping_item_purchased"
down_revision = "0010_shopping_list_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Añade el estado comprado, inicialmente falso, a cada elemento."""
    op.add_column(
        "shopping_list_items",
        sa.Column("purchased", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    """Elimina el estado de compra de los elementos."""
    op.drop_column("shopping_list_items", "purchased")
