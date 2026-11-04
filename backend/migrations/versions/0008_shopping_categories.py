# Crea las categorías del catálogo compartido de compra.
"""Create shopping categories.

Revision ID: 0008_shopping_categories
Revises: 0007_recipes
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_shopping_categories"
down_revision = "0007_recipes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shopping_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("shopping_categories")
