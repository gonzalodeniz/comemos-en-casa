from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT = Path(__file__).parents[2]


def test_alembic_is_configured_from_the_repository_root() -> None:
    config = Config(str(ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(config)

    assert Path(script.dir) == ROOT / "backend" / "alembic"
    assert script.get_current_head() == "0000_baseline"


def test_baseline_is_the_only_alembic_revision_and_has_no_schema_operations() -> None:
    config = Config(str(ROOT / "alembic.ini"))
    script = ScriptDirectory.from_config(config)
    baseline = script.get_revision("0000_baseline")
    source = (ROOT / "backend" / "alembic" / "versions" / "0000_baseline.py").read_text(
        encoding="utf-8"
    )

    assert baseline is not None
    assert baseline.down_revision is None
    assert [revision.revision for revision in script.walk_revisions()] == ["0000_baseline"]
    assert "alembic stamp 0000_baseline" in source
    assert "op." not in source


def test_historical_sql_migrations_are_not_rewritten_as_alembic_revisions() -> None:
    historical_versions = ROOT / "backend" / "migrations" / "versions"
    alembic_versions = ROOT / "backend" / "alembic" / "versions"

    assert sorted(path.name for path in historical_versions.glob("*.sql")) == [
        "0001_meal_calendar_foundation.sql",
        "0002_recipe_catalogue_foundation.sql",
        "0003_meal_calendar_recipe_fk.sql",
        "0004_authentication.sql",
        "0005_recipe_management.sql",
        "0006_collections_favorites.sql",
    ]
    assert sorted(path.name for path in alembic_versions.glob("*.py")) == ["0000_baseline.py"]
