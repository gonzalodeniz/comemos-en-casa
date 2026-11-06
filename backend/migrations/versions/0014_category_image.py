"""Añade una imagen opcional a las categorías de compra."""
from alembic import op
import sqlalchemy as sa

revision = "0014_category_image"
down_revision = "0013_product_image"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Añade la ruta opcional para categorías existentes."""
    op.add_column("shopping_categories", sa.Column("image_path", sa.String(255), nullable=True))


def downgrade() -> None:
    """Elimina la ruta de imagen de las categorías."""
    op.drop_column("shopping_categories", "image_path")
