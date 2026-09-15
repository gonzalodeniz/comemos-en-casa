from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import re
import sys
from typing import Any, Iterator
from uuid import UUID

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.recipes.repository import RecipeCatalogueRepository
from comemos_en_casa.recipes.schemas import Recipe, RecipeListItem, RecipeValidationError


MIGRATION_0001 = (
    Path(__file__).parents[2]
    / "migrations"
    / "versions"
    / "0001_meal_calendar_foundation.sql"
)
MIGRATION = (
    Path(__file__).parents[2]
    / "migrations"
    / "versions"
    / "0002_recipe_catalogue_foundation.sql"
)
MIGRATION_NOTES = MIGRATION.parents[1] / "README.md"


def test_catalogue_migration_creates_the_recipe_identity_and_foundation_fields() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    recipes_table = re.search(
        r"CREATE TABLE recipes \((?P<columns>.*?)\n\);",
        sql,
        flags=re.DOTALL,
    )

    assert recipes_table is not None
    assert re.search(r"\bid\s+uuid\s+PRIMARY KEY\b", recipes_table.group("columns"))
    for column in ("title", "image_url", "detail", "title_search_key"):
        assert re.search(rf"\b{column}\s+text\s+NOT NULL\b", recipes_table.group("columns"))


def test_catalogue_migration_has_no_calendar_table_dependency() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "meal_assignments" not in sql
    assert "meal_calendars" not in sql
    assert "meal_calendar_rate_limits" not in sql


def test_migration_notes_record_catalogue_ownership_before_calendar_integration() -> None:
    migration_notes = MIGRATION_NOTES.read_text(encoding="utf-8").lower()

    assert "0002_recipe_catalogue_foundation.sql" in migration_notes
    assert "catalogue" in migration_notes
    assert re.search(r"0002_recipe_catalogue_foundation\.sql.*before.*calendar", migration_notes)
    assert "meal_assignments.recipe_id" in migration_notes
    assert "on delete set null" in migration_notes


RECIPE_ID = UUID("12345678-1234-5678-1234-567812345678")


def _open_postgres_connection() -> Any:
    psycopg = pytest.importorskip("psycopg")
    connection = psycopg.connect(
        host="localhost",
        port=5433,
        dbname="comemos_en_casa",
        user="comemos",
        password="comemos_dev_password",
    )
    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA recipe_catalogue_test")
        cursor.execute("SET LOCAL search_path TO recipe_catalogue_test, public")
    return connection


@pytest.fixture
def postgres_catalogue_connection() -> Iterator[Any]:
    """Apply the catalogue migration in a rolled-back schema on the Compose database."""
    connection = _open_postgres_connection()
    try:
        connection.execute(MIGRATION.read_text(encoding="utf-8"))
        yield connection
    finally:
        connection.rollback()
        connection.close()


@pytest.fixture
def postgres_calendar_catalogue_connection() -> Iterator[Any]:
    """Apply the calendar foundation followed by the catalogue migration."""
    connection = _open_postgres_connection()
    try:
        connection.execute(MIGRATION_0001.read_text(encoding="utf-8"))
        connection.execute(MIGRATION.read_text(encoding="utf-8"))
        yield connection
    finally:
        connection.rollback()
        connection.close()


@contextmanager
def expects_check_violation(connection: Any) -> Iterator[None]:
    from psycopg.errors import CheckViolation

    with pytest.raises(CheckViolation):
        with connection.transaction():
            yield


class RecordingCursor:
    def __init__(self, *, one: tuple[object, ...] | None = None, many: list[tuple[object, ...]] | None = None) -> None:
        self.one = one
        self.many = many or []
        self.calls: list[tuple[str, tuple[object, ...] | None]] = []

    def __enter__(self) -> "RecordingCursor":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        self.calls.append((query, params))

    def fetchone(self) -> tuple[object, ...] | None:
        return self.one

    def fetchall(self) -> list[tuple[object, ...]]:
        return self.many


class RecordingConnection:
    def __init__(self, cursor: RecordingCursor) -> None:
        self.recording_cursor = cursor
        self.cursor_calls = 0
        self.commit_calls = 0

    def cursor(self) -> RecordingCursor:
        self.cursor_calls += 1
        return self.recording_cursor

    def commit(self) -> None:
        self.commit_calls += 1


def make_recipe() -> Recipe:
    return Recipe.restore(
        id=RECIPE_ID,
        title="Tortilla Española",
        image_url="https://example.test/tortilla.jpg",
        detail="Potato omelette",
    )


def test_insert_binds_recipe_values_and_leaves_transaction_to_caller() -> None:
    connection = RecordingConnection(RecordingCursor())

    RecipeCatalogueRepository(connection).insert(make_recipe())

    query, params = connection.recording_cursor.calls[0]
    assert "INSERT INTO recipes" in query
    assert "%s" in query
    assert params == (
        RECIPE_ID,
        "Tortilla Española",
        "https://example.test/tortilla.jpg",
        "Potato omelette",
        "tortilla espanola",
    )
    assert connection.commit_calls == 0


def test_update_preserves_identity_and_reports_whether_a_recipe_exists() -> None:
    cursor = RecordingCursor(one=(RECIPE_ID,))
    repository = RecipeCatalogueRepository(RecordingConnection(cursor))

    assert repository.update_foundation(make_recipe()) is True

    query, params = cursor.calls[0]
    assert "UPDATE recipes" in query
    assert "SET id" not in query
    assert "RETURNING id" in query
    assert params[-1] == RECIPE_ID


def test_find_public_by_id_returns_current_foundation_or_none() -> None:
    cursor = RecordingCursor(
        one=(RECIPE_ID, "Current title", "https://example.test/current.jpg", "Current detail")
    )
    repository = RecipeCatalogueRepository(RecordingConnection(cursor))

    assert repository.find_public_by_id(RECIPE_ID) == Recipe(
        id=RECIPE_ID,
        title="Current title",
        image_url="https://example.test/current.jpg",
        detail="Current detail",
    )
    assert cursor.calls[0][1] == (RECIPE_ID,)

    assert RecipeCatalogueRepository(RecordingConnection(RecordingCursor())).find_public_by_id(RECIPE_ID) is None


def test_search_uses_literal_wildcards_and_deterministic_ordering() -> None:
    cursor = RecordingCursor(many=[(RECIPE_ID, "100% Sopa", "https://example.test/sopa.jpg")])
    repository = RecipeCatalogueRepository(RecordingConnection(cursor))

    results = repository.search_public_by_title("100%_\\\\ sopa", limit=7)

    query, params = cursor.calls[0]
    assert "LIKE '%%' || %s || '%%'" in query
    assert "ESCAPE" in query
    assert "ORDER BY title_search_key, id" in query
    assert params == (r"100\%\_\\\\ sopa", 7)
    assert results[0].id == RECIPE_ID
    assert results[0].title == "100% Sopa"


def test_empty_search_omits_the_pattern_and_returns_the_first_ordered_page() -> None:
    cursor = RecordingCursor(many=[(RECIPE_ID, "Sopa", "https://example.test/sopa.jpg")])

    results = RecipeCatalogueRepository(RecordingConnection(cursor)).search_public_by_title("  \t", limit=1)

    query, params = cursor.calls[0]
    assert "WHERE title_search_key" not in query
    assert "ORDER BY title_search_key, id" in query
    assert params == (1,)
    assert results == [
        RecipeListItem(
            id=RECIPE_ID,
            title="Sopa",
            image_url="https://example.test/sopa.jpg",
        )
    ]


@pytest.mark.parametrize("limit", [0, 51, "10", True])
def test_search_rejects_limits_outside_the_public_contract(limit: object) -> None:
    repository = RecipeCatalogueRepository(RecordingConnection(RecordingCursor()))

    with pytest.raises(RecipeValidationError, match="limit"):
        repository.search_public_by_title("sopa", limit=limit)  # type: ignore[arg-type]


@pytest.mark.parametrize("query", [None, 0, False])
def test_search_rejects_non_string_queries_before_opening_a_cursor(query: object) -> None:
    connection = RecordingConnection(RecordingCursor())

    with pytest.raises(RecipeValidationError, match="title search query"):
        RecipeCatalogueRepository(connection).search_public_by_title(query)  # type: ignore[arg-type]

    assert connection.cursor_calls == 0


def test_catalogue_migration_applies_in_isolation_with_constraints_and_trigram_index(
    postgres_catalogue_connection: Any,
) -> None:
    connection = postgres_catalogue_connection

    columns = connection.execute(
        """
        SELECT attname
        FROM pg_attribute
        WHERE attrelid = 'recipes'::regclass AND attnum > 0 AND NOT attisdropped
        ORDER BY attnum
        """
    ).fetchall()
    index_definition = connection.execute(
        """
        SELECT indexdef
        FROM pg_indexes
        WHERE schemaname = current_schema() AND indexname = 'recipes_title_search_idx'
        """
    ).fetchone()

    assert columns == [
        ("id",),
        ("title",),
        ("image_url",),
        ("detail",),
        ("title_search_key",),
    ]
    assert index_definition is not None
    assert "USING gin" in index_definition[0]
    assert "gin_trgm_ops" in index_definition[0]

    with expects_check_violation(connection):
        connection.execute(
            """
            INSERT INTO recipes (id, title, image_url, detail, title_search_key)
            VALUES ('00000000-0000-0000-0000-000000000001', '', 'https://example.test/a.jpg', 'Detail', '')
            """
        )


def test_psycopg_repository_round_trip_search_and_calendar_fk_compatibility(
    postgres_calendar_catalogue_connection: Any,
) -> None:
    connection = postgres_calendar_catalogue_connection
    repository = RecipeCatalogueRepository(connection)
    recipes = [
        Recipe.restore(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            title="100% Sopa",
            image_url="https://example.test/percent.jpg",
            detail="Percent",
        ),
        Recipe.restore(
            id=UUID("00000000-0000-0000-0000-000000000002"),
            title="100X Sopa",
            image_url="https://example.test/x.jpg",
            detail="X",
        ),
        Recipe.restore(
            id=UUID("00000000-0000-0000-0000-000000000003"),
            title="A_ Sopa",
            image_url="https://example.test/underscore.jpg",
            detail="Underscore",
        ),
        Recipe.restore(
            id=UUID("00000000-0000-0000-0000-000000000004"),
            title="AB Sopa",
            image_url="https://example.test/ab.jpg",
            detail="Letters",
        ),
        Recipe.restore(
            id=UUID("00000000-0000-0000-0000-000000000005"),
            title=r"Camino\Sopa",
            image_url="https://example.test/backslash.jpg",
            detail="Backslash",
        ),
        Recipe.restore(
            id=UUID("00000000-0000-0000-0000-000000000006"),
            title="Árbol",
            image_url="https://example.test/accent.jpg",
            detail="Accent",
        ),
        Recipe.restore(
            id=UUID("00000000-0000-0000-0000-000000000007"),
            title="arbol",
            image_url="https://example.test/plain.jpg",
            detail="Plain",
        ),
    ]

    for recipe in recipes:
        repository.insert(recipe)

    from psycopg.pq import TransactionStatus

    assert connection.info.transaction_status is TransactionStatus.INTRANS
    assert [item.title for item in repository.search_public_by_title("100%", limit=50)] == ["100% Sopa"]
    assert [item.title for item in repository.search_public_by_title("A_", limit=50)] == ["A_ Sopa"]
    assert [item.title for item in repository.search_public_by_title(r"Camino\Sopa", limit=50)] == [
        r"Camino\Sopa"
    ]
    assert [item.id for item in repository.search_public_by_title("arbol", limit=50)] == [
        recipes[5].id,
        recipes[6].id,
    ]
    assert [item.title for item in repository.search_public_by_title("sopa", limit=2)] == [
        "100% Sopa",
        "100X Sopa",
    ]

    updated = Recipe.update_foundation(
        id=recipes[0].id,
        title="Sopa actualizada",
        image_url="https://example.test/updated.jpg",
        detail="Updated",
    )
    missing = Recipe.update_foundation(
        id=UUID("00000000-0000-0000-0000-000000000099"),
        title="Missing",
        image_url="https://example.test/missing.jpg",
        detail="Missing",
    )
    assert repository.update_foundation(updated) is True
    assert repository.update_foundation(missing) is False
    assert repository.find_public_by_id(recipes[0].id) == updated

    connection.execute(
        """
        ALTER TABLE meal_assignments
        ADD CONSTRAINT meal_assignments_recipe_id_fkey
        FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE SET NULL
        """
    )
    connection.execute(
        """
        INSERT INTO meal_assignments (
            id, calendar_key, meal_date, meal_slot, assignment_kind, recipe_id
        )
        VALUES (%s, 'shared', DATE '2026-01-01', 'dinner', 'recipe', %s)
        """,
        (UUID("00000000-0000-0000-0000-000000000010"), updated.id),
    )
    connection.execute("DELETE FROM recipes WHERE id = %s", (updated.id,))

    assert connection.execute("SELECT recipe_id FROM meal_assignments").fetchone() == (None,)
