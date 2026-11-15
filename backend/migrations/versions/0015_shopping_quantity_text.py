"""Añade texto libre opcional a las cantidades de compra."""
from alembic import op
import sqlalchemy as sa

revision = "0015_shopping_quantity_text"
down_revision = "0014_category_image"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Conserva las cantidades existentes y permite asociar texto libre."""
    op.add_column("shopping_list_items", sa.Column("quantity_text", sa.Text(), nullable=True))


def downgrade() -> None:
    """Elimina el texto libre; sus valores no pueden recuperarse tras la reversión."""
    op.drop_column("shopping_list_items", "quantity_text")
