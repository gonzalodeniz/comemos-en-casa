"""Añade una imagen opcional a los productos de compra."""
from alembic import op
import sqlalchemy as sa

revision = "0013_product_image"
down_revision = "0012_recipe_shopping_sections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Añade la ruta opcional sin modificar los productos existentes."""
    op.add_column("shopping_products", sa.Column("image_path", sa.String(255), nullable=True))


def downgrade() -> None:
    """Elimina la ruta de imagen de los productos."""
    op.drop_column("shopping_products", "image_path")
