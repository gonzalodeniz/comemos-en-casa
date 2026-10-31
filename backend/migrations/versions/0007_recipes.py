"""Create recipes and food associations.

Revision ID: 0007_recipes
Revises: 0006_food_catalog_images
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0007_recipes"
down_revision: Union[str, None] = "0006_food_catalog_images"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table("recipes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("title_canonical", sa.Text(), nullable=False),
        sa.Column("image_path", sa.String(255), nullable=True),
        sa.Column("ingredients", sa.Text(), nullable=True),
        sa.Column("preparation", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title_canonical", name="uq_recipes_title_canonical"))
    op.create_table("recipe_food_labels",
        sa.Column("recipe_id", sa.Uuid(), nullable=False),
        sa.Column("food_label_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["food_label_id"], ["food_labels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("recipe_id", "food_label_id"))
    op.create_index("ix_recipe_food_labels_food", "recipe_food_labels", ["food_label_id"])

def downgrade() -> None:
    op.drop_index("ix_recipe_food_labels_food", table_name="recipe_food_labels")
    op.drop_table("recipe_food_labels")
    op.drop_table("recipes")
