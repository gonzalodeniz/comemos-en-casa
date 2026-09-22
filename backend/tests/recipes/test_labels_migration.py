from __future__ import annotations

from pathlib import Path
import re

import pytest


MIGRATIONS_DIRECTORY = Path(__file__).parents[2] / "migrations" / "versions"


def _labels_migration() -> Path:
    for migration in sorted(MIGRATIONS_DIRECTORY.glob("*.sql")):
        sql = migration.read_text(encoding="utf-8").lower()
        if "recipe_labels" in sql and "recipe_label_assignments" in sql:
            return migration
    pytest.fail("The recipe labels migration has not been added yet")


def test_labels_migration_defines_global_labels_and_cascading_assignments() -> None:
    sql = _labels_migration().read_text(encoding="utf-8")

    labels_table = re.search(
        r"CREATE TABLE recipe_labels \((?P<columns>.*?)\n\);",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )
    assignments_table = re.search(
        r"CREATE TABLE recipe_label_assignments \((?P<columns>.*?)\n\);",
        sql,
        flags=re.DOTALL | re.IGNORECASE,
    )

    assert labels_table is not None
    assert assignments_table is not None
    assert re.search(r"\bid\s+uuid\s+PRIMARY KEY\b", labels_table.group("columns"), re.IGNORECASE)
    assert re.search(r"\bname\s+text\s+NOT NULL\b", labels_table.group("columns"), re.IGNORECASE)
    assert re.search(r"\bcolor\s+text\s+NOT NULL\b", labels_table.group("columns"), re.IGNORECASE)
    assert re.search(r"\bname\s+text\s+NOT NULL\s+UNIQUE\b", labels_table.group("columns"), re.IGNORECASE)
    assert re.search(
        r"recipe_id\s+uuid\s+NOT NULL\s+REFERENCES\s+recipes\s*\(\s*id\s*\)\s+ON DELETE CASCADE",
        assignments_table.group("columns"),
        re.IGNORECASE,
    )
    assert re.search(
        r"label_id\s+uuid\s+NOT NULL\s+REFERENCES\s+recipe_labels\s*\(\s*id\s*\)\s+ON DELETE CASCADE",
        assignments_table.group("columns"),
        re.IGNORECASE,
    )
    assert "PRIMARY KEY (recipe_id, label_id)" in assignments_table.group("columns")


def test_labels_migration_has_indexes_for_name_and_assignment_lookups() -> None:
    sql = _labels_migration().read_text(encoding="utf-8").lower()

    assert "recipe_labels" in sql
    assert "recipe_label_assignments" in sql
    assert "recipe_label_assignments_label_recipe_idx" in sql
    assert re.search(r"create\s+(?:unique\s+)?index\s+.*recipe_labels.*name", sql)
