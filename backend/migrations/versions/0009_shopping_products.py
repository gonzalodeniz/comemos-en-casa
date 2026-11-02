"""Create products for the shared shopping catalog.

Revision ID: 0009_shopping_products
Revises: 0008_shopping_categories
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_shopping_products"
down_revision = "0008_shopping_categories"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shopping_products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"], ["shopping_categories.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("shopping_products")
