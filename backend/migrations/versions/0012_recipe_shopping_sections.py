"""Crea secciones independientes para recetas en la lista de compra."""
from alembic import op
import sqlalchemy as sa

revision = "0012_recipe_shopping_sections"
down_revision = "0011_shopping_item_purchased"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crea la tabla de secciones de recetas con su nombre copiado."""
    op.create_table(
        "recipe_shopping_sections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "recipe_shopping_ingredients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("purchased", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.ForeignKeyConstraint(
            ["section_id"], ["recipe_shopping_sections.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Elimina las secciones de recetas de la lista de compra."""
    op.drop_table("recipe_shopping_ingredients")
    op.drop_table("recipe_shopping_sections")
