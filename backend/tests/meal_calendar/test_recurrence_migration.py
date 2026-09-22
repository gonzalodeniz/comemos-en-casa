from __future__ import annotations

from pathlib import Path
import subprocess


VERSIONS = Path(__file__).parents[2] / "migrations" / "versions"
MIGRATION = VERSIONS / "0007_meal_calendar_recurrence.sql"
README = MIGRATION.parents[1] / "README.md"


def test_recurrence_migration_declares_one_shared_rule_without_occurrence_storage() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "CREATE TABLE meal_recurrence_rules" in sql
    assert "id uuid PRIMARY KEY" in sql
    assert "calendar_key text NOT NULL REFERENCES meal_calendars (calendar_key)" in sql
    assert "initial_date date NOT NULL" in sql
    assert "meal_slot text NOT NULL CHECK (meal_slot IN ('lunch', 'dinner'))" in sql
    assert "free_text text NOT NULL" in sql
    assert "interval_weeks smallint NOT NULL CHECK (interval_weeks IN (1, 2, 3, 4))" in sql
    assert "recipe_id" not in sql
    assert "occurrence" not in sql.lower()
    assert "meal_recurrence_rules_calendar_initial_idx" in sql
    assert "(calendar_key, initial_date)" in sql


def test_recurrence_migration_is_documented_after_the_existing_calendar_versions() -> None:
    notes = README.read_text(encoding="utf-8")

    assert "0007_meal_calendar_recurrence.sql" in notes
    assert "0001" in notes and "0006" in notes
    assert "no end date" in notes or "indefinite" in notes
    assert "not materialized" in notes


def test_recurrence_migration_enforces_shared_rule_shape_and_allows_coexisting_rules() -> None:
    migration_sql = "\n".join(
        (VERSIONS / name).read_text(encoding="utf-8")
        for name in ("0001_meal_calendar_foundation.sql", "0007_meal_calendar_recurrence.sql")
    )
    script = f"""\
BEGIN;
CREATE SCHEMA meal_calendar_recurrence_test;
SET LOCAL search_path TO meal_calendar_recurrence_test;
{migration_sql}
INSERT INTO meal_recurrence_rules
    (id, calendar_key, initial_date, meal_slot, free_text, interval_weeks)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'shared', '2026-09-16', 'lunch', 'Sopa', 1),
    ('00000000-0000-0000-0000-000000000002', 'shared', '2026-09-16', 'lunch', 'Fruta', 2);
DO $$
BEGIN
    BEGIN
        INSERT INTO meal_recurrence_rules
            (id, calendar_key, initial_date, meal_slot, free_text, interval_weeks)
        VALUES ('00000000-0000-0000-0000-000000000003', 'shared', '2026-09-16', 'lunch', 'Sopa', 0);
        RAISE EXCEPTION 'accepted unsupported recurrence interval';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;
    BEGIN
        INSERT INTO meal_recurrence_rules
            (id, calendar_key, initial_date, meal_slot, free_text, interval_weeks)
        VALUES ('00000000-0000-0000-0000-000000000004', 'shared', '2026-09-16', 'breakfast', 'Sopa', 1);
        RAISE EXCEPTION 'accepted unsupported meal slot';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;
    BEGIN
        INSERT INTO meal_recurrence_rules
            (id, calendar_key, initial_date, meal_slot, free_text, interval_weeks)
        VALUES ('00000000-0000-0000-0000-000000000005', 'shared', '2026-09-16', 'lunch', ' Sopa', 1);
        RAISE EXCEPTION 'accepted unnormalized free text';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;
    BEGIN
        INSERT INTO meal_recurrence_rules
            (id, calendar_key, initial_date, meal_slot, free_text, interval_weeks)
        VALUES ('00000000-0000-0000-0000-000000000006', 'shared', '2026-09-16', 'lunch', '', 1);
        RAISE EXCEPTION 'accepted empty free text';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;
END
$$;
DO $$
BEGIN
    BEGIN
        INSERT INTO meal_recurrence_rules
            (id, calendar_key, initial_date, meal_slot, free_text, interval_weeks)
        VALUES ('00000000-0000-0000-0000-000000000007', 'private', '2026-09-16', 'lunch', 'Sopa', 1);
        RAISE EXCEPTION 'accepted a non-shared calendar key';
    EXCEPTION WHEN foreign_key_violation THEN
        NULL;
    END;
END
$$;
SELECT count(*) FROM meal_recurrence_rules;
SELECT count(*) FROM pg_indexes
    WHERE schemaname = 'meal_calendar_recurrence_test'
      AND indexname = 'meal_recurrence_rules_calendar_initial_idx';
SELECT count(*) FROM pg_tables
    WHERE schemaname = 'meal_calendar_recurrence_test'
      AND tablename = 'meal_recurrence_occurrences';
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
    assert completed.stdout.splitlines() == ["2", "1", "0"]
