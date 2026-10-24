"""Verifica el esquema y la cadena de migraciones ORM.

Comprueba tablas, unicidad de correo, almacenamiento de resúmenes y orden de revisiones.
"""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import UniqueConstraint

from app.models import Base


def test_user_auth_tables_are_in_metadata():
    assert {
        "users",
        "user_sessions",
        "password_reset_tokens",
        "login_attempt_buckets",
        "login_attempt_events",
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


def test_auth_migration_follows_baseline():
    root = Path(__file__).resolve().parents[1]
    script = ScriptDirectory(dir=str(root / "migrations"))

    assert script.get_heads() == ["0004_password_reset_rate_scopes"]
    assert script.get_revision("0002_user_auth").down_revision == "0001_baseline"
    assert script.get_revision("0003_login_attempt_events").down_revision == "0002_user_auth"
    assert script.get_revision("0004_password_reset_rate_scopes").down_revision == "0003_login_attempt_events"
