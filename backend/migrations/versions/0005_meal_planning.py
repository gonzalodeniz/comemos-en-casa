"""Create shared meal-planning tables and seed default food labels.

Revision ID: 0005_meal_planning
Revises: 0004_password_reset_rate_scopes
"""

from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "0005_meal_planning"
down_revision: Union[str, None] = "0004_password_reset_rate_scopes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_LABELS = (
    ("10000000-0000-4000-8000-000000000001", "legumbres", "Legumbres"),
    ("10000000-0000-4000-8000-000000000002", "garbanzos", "Garbanzos"),
    ("10000000-0000-4000-8000-000000000003", "lentejas", "Lentejas"),
    ("10000000-0000-4000-8000-000000000004", "judias", "Judías"),
    ("10000000-0000-4000-8000-000000000005", "pescado", "Pescado"),
    ("10000000-0000-4000-8000-000000000006", "sardinas", "Sardinas"),
    ("10000000-0000-4000-8000-000000000007", "marisco", "Marisco"),
    ("10000000-0000-4000-8000-000000000008", "carne", "Carne"),
    ("10000000-0000-4000-8000-000000000009", "pollo", "Pollo"),
    ("10000000-0000-4000-8000-000000000010", "ternera", "Ternera"),
    ("10000000-0000-4000-8000-000000000011", "cerdo", "Cerdo"),
    ("10000000-0000-4000-8000-000000000012", "verduras", "Verduras"),
    ("10000000-0000-4000-8000-000000000013", "ensalada", "Ensalada"),
    ("10000000-0000-4000-8000-000000000014", "pasta", "Pasta"),
    ("10000000-0000-4000-8000-000000000015", "arroz", "Arroz"),
    ("10000000-0000-4000-8000-000000000016", "huevos", "Huevos"),
    ("10000000-0000-4000-8000-000000000017", "sopa", "Sopa"),
    ("10000000-0000-4000-8000-000000000018", "pizza", "Pizza"),
)


def upgrade() -> None:
    op.create_table(
        "food_labels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_food_labels_code"),
    )
    op.create_table(
        "meal_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("slot", sa.String(length=16), nullable=False),
        sa.Column("label_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "slot IN ('lunch', 'dinner')",
            name="ck_meal_assignments_slot",
        ),
        sa.ForeignKeyConstraint(
            ["label_id"], ["food_labels.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date", "slot", name="uq_meal_assignments_date_slot"),
    )
    op.create_index(
        "ix_meal_assignments_label_id", "meal_assignments", ["label_id"], unique=False
    )

    labels_table = sa.table(
        "food_labels",
        sa.column("id", sa.Uuid()),
        sa.column("code", sa.String(length=32)),
        sa.column("name", sa.String(length=80)),
    )
    op.bulk_insert(
        labels_table,
        [
            {"id": UUID(label_id), "code": code, "name": name}
            for label_id, code, name in _LABELS
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_meal_assignments_label_id", table_name="meal_assignments")
    op.drop_table("meal_assignments")
    op.drop_table("food_labels")
