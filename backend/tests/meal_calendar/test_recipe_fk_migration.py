from __future__ import annotations

from pathlib import Path
import subprocess


VERSIONS = Path(__file__).parents[2] / "migrations" / "versions"
MIGRATIONS = (
    VERSIONS / "0001_meal_calendar_foundation.sql",
    VERSIONS / "0002_recipe_catalogue_foundation.sql",
    VERSIONS / "0003_meal_calendar_recipe_fk.sql",
)


def test_recipe_foreign_key_migration_integrates_calendar_and_catalogue() -> None:
    migration_sql = "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS)
    script = f"""\
BEGIN;
CREATE SCHEMA meal_calendar_recipe_fk_test;
SET LOCAL search_path TO meal_calendar_recipe_fk_test, public;
{migration_sql}
INSERT INTO recipes (id, title, image_url, detail, title_search_key)
VALUES
    ('00000000-0000-0000-0000-000000000101', 'Sopa', 'https://example.test/sopa.jpg',
     'Sopa caliente', 'sopa');
INSERT INTO meal_assignments
    (id, calendar_key, meal_date, meal_slot, assignment_kind, recipe_id)
VALUES
    ('00000000-0000-0000-0000-000000000201', 'shared', '2025-06-02', 'lunch', 'recipe',
     '00000000-0000-0000-0000-000000000101'),
    ('00000000-0000-0000-0000-000000000202', 'shared', '2025-06-02', 'lunch', 'recipe',
     '00000000-0000-0000-0000-000000000101');
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'meal_calendar_recipe_fk_test'
          AND table_name = 'meal_assignments'
          AND column_name IN ('recipe_title', 'recipe_image_url', 'title', 'image_url')
    ) THEN
        RAISE EXCEPTION 'meal_assignments stores recipe title or image snapshots';
    END IF;
    BEGIN
        INSERT INTO meal_assignments
            (id, calendar_key, meal_date, meal_slot, assignment_kind, recipe_id)
        VALUES
            ('00000000-0000-0000-0000-000000000203', 'shared', '2025-06-03', 'dinner', 'recipe',
             '00000000-0000-0000-0000-000000000102');
        RAISE EXCEPTION 'meal_assignments accepted an unknown recipe';
    EXCEPTION WHEN foreign_key_violation THEN
        NULL;
    END;
END
$$;
SELECT count(*) FROM meal_assignments;
DELETE FROM recipes WHERE id = '00000000-0000-0000-0000-000000000101';
SELECT bool_and(recipe_id IS NULL) FROM meal_assignments;
SELECT count(*) FROM meal_assignments;
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
    assert completed.stdout.splitlines() == ["2", "t", "2"]
