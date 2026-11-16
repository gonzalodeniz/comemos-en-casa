"""Añade categorías habituales al catálogo compartido de compra."""
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision = "0017_shopping_default_categories"
down_revision = "0016_recipe_section_recipe"
branch_labels = None
depends_on = None


_CATEGORIAS = (
    ("20000000-0000-4000-8000-000000000001", "Lácteos y huevos"),
    ("20000000-0000-4000-8000-000000000002", "Carne y aves"),
    ("20000000-0000-4000-8000-000000000003", "Pescado y marisco"),
    ("20000000-0000-4000-8000-000000000004", "Panadería"),
    ("20000000-0000-4000-8000-000000000005", "Pasta"),
    ("20000000-0000-4000-8000-000000000006", "Despensa"),
    ("20000000-0000-4000-8000-000000000007", "Limpieza"),
    ("20000000-0000-4000-8000-000000000008", "Higiene"),
    ("20000000-0000-4000-8000-000000000009", "Snacks y dulces"),
)


def upgrade() -> None:
    """Añade solo las categorías que aún no existen por nombre."""
    categorias = sa.table(
        "shopping_categories",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String(100)),
    )
    conexion = op.get_bind()
    for categoria_id, nombre in _CATEGORIAS:
        existe = conexion.scalar(
            sa.select(sa.exists().where(categorias.c.name == nombre))
        )
        if not existe:
            conexion.execute(
                categorias.insert().values(id=UUID(categoria_id), name=nombre)
            )


def downgrade() -> None:
    """Retira las categorías añadidas que todavía no contienen productos."""
    categorias = sa.table(
        "shopping_categories",
        sa.column("id", sa.Uuid()),
    )
    productos = sa.table(
        "shopping_products",
        sa.column("category_id", sa.Uuid()),
    )
    op.execute(
        categorias.delete().where(
            categorias.c.id.in_([UUID(categoria_id) for categoria_id, _ in _CATEGORIAS])
        ).where(
            ~sa.exists().where(productos.c.category_id == categorias.c.id)
        )
    )
