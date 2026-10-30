"""Verifica el esquema y la cadena de migraciones ORM.

Comprueba tablas, unicidad de correo, almacenamiento de resúmenes y orden de revisiones.
"""

from pathlib import Path
from datetime import date

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import UniqueConstraint, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, FoodLabel, MealAssignment


def test_user_auth_tables_are_in_metadata():
    assert {
        "users",
        "user_sessions",
        "password_reset_tokens",
        "login_attempt_buckets",
        "login_attempt_events",
        "food_labels",
        "meal_assignments",
    }.issubset(Base.metadata.tables)


def test_user_email_canonical_form_is_unique():
    table = Base.metadata.tables["users"]
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("email_canonical",)
        for constraint in table.constraints
    )


def test_secret_tables_store_only_digests():
    expected = {
        "user_sessions": "token_digest",
        "password_reset_tokens": "token_digest",
        "login_attempt_buckets": "key_digest",
        "login_attempt_events": "key_digest",
    }
    for table_name, digest_column in expected.items():
        table = Base.metadata.tables[table_name]
        assert digest_column in table.columns
        assert "token" not in table.columns
        assert "raw_ip" not in table.columns


def test_food_catalog_migration_follows_meal_planning_and_auth_migrations():
    root = Path(__file__).resolve().parents[1]
    script = ScriptDirectory(dir=str(root / "migrations"))

    assert script.get_heads() == ["0006_food_catalog_images"]
    assert script.get_revision("0002_user_auth").down_revision == "0001_baseline"
    assert script.get_revision("0003_login_attempt_events").down_revision == "0002_user_auth"
    assert script.get_revision("0004_password_reset_rate_scopes").down_revision == "0003_login_attempt_events"
    assert script.get_revision("0005_meal_planning").down_revision == "0004_password_reset_rate_scopes"
    assert script.get_revision("0006_food_catalog_images").down_revision == "0005_meal_planning"


def test_meal_assignments_have_slot_check_and_unique_date_slot():
    from sqlalchemy import CheckConstraint, UniqueConstraint

    table = Base.metadata.tables["meal_assignments"]
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("date", "slot")
        for constraint in table.constraints
    )
    assert any(
        isinstance(constraint, CheckConstraint)
        and "slot" in str(constraint.sqltext)
        for constraint in table.constraints
    )
    assert {"date", "slot", "label_id"}.issubset(table.columns.keys())
    assert "user_id" not in table.columns
    assert {
        foreign_key.target_fullname for foreign_key in table.foreign_keys
    } == {"food_labels.id"}


def test_meal_assignment_slot_and_date_uniqueness_are_enforced():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            label = FoodLabel(code="pescado", name="Pescado")
            session.add(label)
            session.flush()
            session.add(
                MealAssignment(
                    date=date(2026, 11, 2), slot="lunch", label_id=label.id
                )
            )
            session.commit()

            session.add(
                MealAssignment(
                    date=date(2026, 11, 2), slot="lunch", label_id=label.id
                )
            )
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

            session.add(
                MealAssignment(
                    date=date(2026, 11, 2), slot="breakfast", label_id=label.id
                )
            )
            with pytest.raises(IntegrityError):
                session.commit()
    finally:
        engine.dispose()
