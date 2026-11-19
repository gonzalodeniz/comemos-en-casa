"""Crea el catálogo inicial de trucos de cocina."""
from uuid import UUID
from alembic import op
import sqlalchemy as sa

revision = "0023_kitchen_tips"
down_revision = "0022_category_name_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crea el catálogo y registra los dos trucos iniciales."""
    op.create_table(
        "kitchen_tips",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.bulk_insert(
        sa.table("kitchen_tips", sa.column("id", sa.Uuid()), sa.column("title", sa.String()), sa.column("content", sa.Text())),
        [
            {"id": UUID("c50cc89a-14d6-4570-b0f0-f26f40eb2ca0"), "title": "Limpiar lechuga con Thermomix", "content": "Separa las hojas y colócalas en el vaso. Cúbrelas con agua sin superar la capacidad máxima indicada para tu modelo. Programa 10 segundos a velocidad 4, giro inverso. Escurre y aclara las hojas con agua limpia; sécalas antes de servir o guardar. Revisa el manual de tu modelo y no fuerces el aparato si las hojas se atascan."},
            {"id": UUID("c50cc89a-14d6-4570-b0f0-f26f40eb2ca1"), "title": "Limpiar una sartén de aluminio", "content": "Deja que la sartén se enfríe y lávala con agua templada, detergente suave y una esponja no abrasiva. Para restos adheridos, déjala en remojo unos minutos y retíralos suavemente. Evita estropajos metálicos, productos cáusticos y lavavajillas si el fabricante no lo recomienda; seca bien para reducir marcas de agua."},
        ],
    )


def downgrade() -> None:
    """Elimina el catálogo de trucos."""
    op.drop_table("kitchen_tips")
