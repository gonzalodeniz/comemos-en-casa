"""Add normalized names and optional food-label images.

Revision ID: 0006_food_catalog_images
Revises: 0005_meal_planning
"""
from typing import Sequence, Union
import unicodedata

import sqlalchemy as sa
from alembic import op

revision: str = "0006_food_catalog_images"
down_revision: Union[str, None] = "0005_meal_planning"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, name FROM food_labels ORDER BY id")).all()
    seen: dict[str, str] = {}
    normalized = []
    for row_id, name in rows:
        canonical = unicodedata.normalize("NFC", name).strip().casefold()
        if canonical in seen:
            raise RuntimeError(f"Food-label name collision during migration: {seen[canonical]} and {row_id}")
        seen[canonical] = str(row_id)
        normalized.append((row_id, canonical))
    op.alter_column("food_labels", "name", type_=sa.String(100), existing_nullable=False)
    op.add_column("food_labels", sa.Column("name_canonical", sa.Text(), nullable=True))
    op.add_column("food_labels", sa.Column("image_path", sa.String(255), nullable=True))
    for row_id, canonical in normalized:
        bind.execute(sa.text("UPDATE food_labels SET name_canonical=:canonical WHERE id=:id"), {"canonical": canonical, "id": row_id})
    op.alter_column("food_labels", "name_canonical", nullable=False)
    op.create_unique_constraint("uq_food_labels_name_canonical", "food_labels", ["name_canonical"])


def downgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT 1 FROM food_labels WHERE length(name) > 80 LIMIT 1")).first():
        raise RuntimeError("Cannot downgrade: a food-label name exceeds 80 characters")
    op.drop_constraint("uq_food_labels_name_canonical", "food_labels", type_="unique")
    op.drop_column("food_labels", "image_path")
    op.drop_column("food_labels", "name_canonical")
    op.alter_column("food_labels", "name", type_=sa.String(80), existing_nullable=False)
