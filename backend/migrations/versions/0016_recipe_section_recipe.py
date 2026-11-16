"""Asocia las nuevas secciones de compra con su receta de origen."""
from alembic import op
import sqlalchemy as sa

revision = "0016_recipe_section_recipe"
down_revision = "0015_shopping_quantity_text"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Añade una referencia opcional y conserva las secciones existentes."""
    with op.batch_alter_table("recipe_shopping_sections") as tabla:
        tabla.add_column(sa.Column("recipe_id", sa.Uuid(), nullable=True))
        tabla.create_foreign_key("fk_recipe_shopping_sections_recipe", "recipes", ["recipe_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    """Elimina la referencia a la receta original."""
    with op.batch_alter_table("recipe_shopping_sections") as tabla:
        tabla.drop_constraint("fk_recipe_shopping_sections_recipe", type_="foreignkey")
        tabla.drop_column("recipe_id")
