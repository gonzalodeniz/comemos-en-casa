"""Añade observaciones opcionales a los productos de la lista de compra."""
from alembic import op
import sqlalchemy as sa

revision = "0018_shopping_item_observation"
down_revision = "0017_shopping_default_categories"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Permite guardar una nota independiente de la cantidad del producto."""
    op.add_column("shopping_list_items", sa.Column("observation", sa.Text(), nullable=True))


def downgrade() -> None:
    """Elimina la observación opcional de los productos de compra."""
    op.drop_column("shopping_list_items", "observation")
