"""Crea los elementos persistidos de la lista de compra.

Revision ID: 0010_shopping_list_items
Revises: 0009_shopping_products
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_shopping_list_items"
down_revision = "0009_shopping_products"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crea la tabla para almacenar productos con cantidad y unidad."""
    op.create_table(
        "shopping_list_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=3), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"], ["shopping_products.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Elimina la tabla de elementos de la lista de compra."""
    op.drop_table("shopping_list_items")
