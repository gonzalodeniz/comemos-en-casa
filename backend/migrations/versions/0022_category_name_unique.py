"""Impide nombres de categorías duplicados en el catálogo compartido."""
import unicodedata
import sqlalchemy as sa
from alembic import op

revision = "0022_category_name_unique"
down_revision = "0021_user_last_view"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Normaliza nombres existentes y detiene la migración ante colisiones."""
    conexion = op.get_bind()
    nombres = conexion.execute(sa.text("SELECT id, name FROM shopping_categories")).all()
    vistos = {}
    for identificador, nombre in nombres:
        clave = unicodedata.normalize("NFC", nombre.strip()).casefold()
        if clave in vistos:
            raise RuntimeError(f"Categorías con nombres duplicados: {vistos[clave]} y {identificador}")
        vistos[clave] = identificador
    op.add_column("shopping_categories", sa.Column("name_canonical", sa.Text(), nullable=True))
    for clave, identificador in vistos.items():
        conexion.execute(sa.text("UPDATE shopping_categories SET name_canonical=:clave WHERE id=:id"), {"clave": clave, "id": identificador})
    with op.batch_alter_table("shopping_categories") as tabla:
        tabla.alter_column("name_canonical", existing_type=sa.Text(), nullable=False)
        tabla.create_unique_constraint("uq_shopping_categories_name_canonical", ["name_canonical"])


def downgrade() -> None:
    """Retira la restricción y la columna normalizada."""
    with op.batch_alter_table("shopping_categories") as tabla:
        tabla.drop_constraint("uq_shopping_categories_name_canonical", type_="unique")
        tabla.drop_column("name_canonical")
