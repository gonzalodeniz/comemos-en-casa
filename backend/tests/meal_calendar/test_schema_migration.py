from __future__ import annotations

from pathlib import Path
import subprocess


MIGRATION = (
    Path(__file__).parents[2]
    / "migrations"
    / "versions"
    / "0001_meal_calendar_foundation.sql"
)


def test_foundation_migration_creates_the_shared_singleton_and_core_tables() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "CREATE TABLE meal_calendars" in sql
    assert "CHECK (calendar_key = 'shared')" in sql
    assert "INSERT INTO meal_calendars (calendar_key) VALUES ('shared')" in sql
    assert "CREATE TABLE meal_assignments" in sql
    assert "CREATE TABLE meal_calendar_rate_limits" in sql


def test_foundation_migration_allows_duplicate_cells_and_enforces_assignment_shapes() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "UNIQUE (calendar_key, meal_date, meal_slot" not in sql
    assert "meal_slot IN ('lunch', 'dinner')" in sql
    assert "assignment_kind IN ('recipe', 'free_text')" in sql
    assert "assignment_kind = 'recipe' AND free_text IS NULL" in sql
    assert "assignment_kind = 'free_text'" in sql
    assert "free_text = btrim(free_text)" in sql
    assert "char_length(free_text) BETWEEN 1 AND 100" in sql


def test_foundation_migration_indexes_week_cells_recipes_and_rate_limit_cleanup() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "meal_assignments_week_cell_idx" in sql
    assert "(calendar_key, meal_date, meal_slot)" in sql
    assert "meal_assignments_recipe_idx" in sql
    assert "WHERE recipe_id IS NOT NULL" in sql
    assert "meal_calendar_rate_limits_cleanup_idx" in sql
    assert "operation_class IN ('read', 'write')" in sql


def test_recipe_foreign_key_is_safely_deferred_until_the_catalogue_exists() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    migration_notes = MIGRATION.parents[1] / "README.md"

    assert "recipe_id uuid NULL" in sql
    assert "REFERENCES recipes" not in sql
    assert "ON DELETE SET NULL" in migration_notes.read_text(encoding="utf-8")


def test_foundation_migration_applies_to_an_isolated_postgresql_transaction() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    script = f"""\
BEGIN;
CREATE SCHEMA meal_calendar_test;
SET LOCAL search_path TO meal_calendar_test;
{sql}
DO $$
BEGIN
    BEGIN
        INSERT INTO meal_calendars (calendar_key) VALUES ('not-shared');
        RAISE EXCEPTION 'meal_calendars accepted a non-shared key';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;
    BEGIN
        INSERT INTO meal_assignments
            (id, calendar_key, meal_date, meal_slot, assignment_kind, recipe_id, free_text)
        VALUES
            ('00000000-0000-0000-0000-000000000003', 'shared', '2025-06-02', 'lunch', 'free_text',
             '00000000-0000-0000-0000-000000000004', 'not allowed');
        RAISE EXCEPTION 'meal_assignments accepted an invalid free-text shape';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;
END
$$;
INSERT INTO meal_assignments
    (id, calendar_key, meal_date, meal_slot, assignment_kind, free_text)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'shared', '2025-06-02', 'lunch', 'free_text', 'Sopa'),
    ('00000000-0000-0000-0000-000000000002', 'shared', '2025-06-02', 'lunch', 'free_text', 'Sopa');
INSERT INTO meal_calendar_rate_limits
    (client_ip, window_start, operation_class, request_count)
VALUES ('127.0.0.1', '2025-06-02T12:00:00Z', 'read', 1);
SELECT count(*) FROM meal_assignments;
SELECT count(*) FROM pg_constraint
    WHERE conrelid = 'meal_assignments'::regclass
      AND contype = 'f'
      AND pg_get_constraintdef(oid) LIKE '%recipe_id%';
SELECT count(*) FROM pg_indexes
    WHERE schemaname = 'meal_calendar_test'
      AND indexname IN (
          'meal_assignments_week_cell_idx',
          'meal_assignments_recipe_idx',
          'meal_calendar_rate_limits_cleanup_idx'
      );
SELECT request_count FROM meal_calendar_rate_limits;
ROLLBACK;
"""

    completed = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "--quiet",
            "--tuples-only",
            "--no-align",
            "--set",
            "ON_ERROR_STOP=1",
            "-U",
            "comemos",
            "-d",
            "comemos_en_casa",
        ],
        input=script,
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.splitlines() == ["2", "0", "3", "1"]
