from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sys
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.collections.repository import CollectionsRepository
from comemos_en_casa.collections.schemas import Collection


USER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
COLLECTION_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
RECIPE_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
MIGRATION = Path(__file__).parents[2] / "migrations" / "versions" / "0006_collections_favorites.sql"


class RecordingCursor:
    def __init__(self, rows: list[tuple[object, ...]] | None = None, row: tuple[object, ...] | None = None) -> None:
        self.rows = rows or []
        self.row = row
        self.calls: list[tuple[str, tuple[object, ...] | None]] = []

    def __enter__(self) -> "RecordingCursor":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        self.calls.append((query, params))

    def fetchall(self) -> list[tuple[object, ...]]:
        return self.rows

    def fetchone(self) -> tuple[object, ...] | None:
        return self.row


class RecordingConnection:
    def __init__(self, cursor: RecordingCursor) -> None:
        self.recording_cursor = cursor

    @contextmanager
    def cursor(self) -> RecordingCursor:
        yield self.recording_cursor


def test_migration_keeps_recipes_public_and_cascades_saved_reference_cleanup() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "CREATE TABLE recipe_favorites" in sql
    assert "CREATE TABLE recipe_collections" in sql
    assert "CREATE TABLE collection_recipes" in sql
    assert sql.count("REFERENCES recipes (id) ON DELETE CASCADE") == 2
    assert "REFERENCES users (id) ON DELETE CASCADE" in sql
    assert "status" not in sql


def test_list_favorites_returns_public_recipe_values_in_saved_order() -> None:
    cursor = RecordingCursor(rows=[(RECIPE_ID, "Sopa", "")])

    favorites = CollectionsRepository(RecordingConnection(cursor)).list_favorites(USER_ID)

    assert favorites[0].title == "Sopa"
    query, params = cursor.calls[0]
    assert "FROM recipe_favorites AS favorites" in query
    assert "JOIN recipes AS recipes" in query
    assert "status" not in query
    assert "WHERE favorites.user_id = %s" in query
    assert "ORDER BY favorites.created_at DESC, favorites.recipe_id" in query
    assert params == (USER_ID,)


def test_collection_reads_are_scoped_to_the_owner_and_include_public_recipes() -> None:
    cursor = RecordingCursor(
        rows=[
            (COLLECTION_ID, "Cenas", RECIPE_ID, "Sopa", ""),
            (COLLECTION_ID, "Cenas", None, None, None),
        ]
    )

    collection = CollectionsRepository(RecordingConnection(cursor)).find_collection(USER_ID, COLLECTION_ID)

    assert collection is not None
    assert collection.name == "Cenas"
    assert [recipe.id for recipe in collection.recipes] == [RECIPE_ID]
    query, params = cursor.calls[0]
    assert "WHERE collections.user_id = %s AND collections.id = %s" in query
    assert "status" not in query
    assert params == (USER_ID, COLLECTION_ID)


def test_collection_mutations_bind_the_owner_and_leave_transaction_to_the_caller() -> None:
    cursor = RecordingCursor(row=(COLLECTION_ID,))
    repository = CollectionsRepository(RecordingConnection(cursor))

    assert repository.update_collection(USER_ID, Collection(id=COLLECTION_ID, name="Nuevas")) is True
    assert repository.delete_collection(USER_ID, COLLECTION_ID) is True

    update_query, update_params = cursor.calls[0]
    delete_query, delete_params = cursor.calls[1]
    assert "WHERE id = %s AND user_id = %s" in update_query
    assert update_params == ("Nuevas", COLLECTION_ID, USER_ID)
    assert "WHERE id = %s AND user_id = %s" in delete_query
    assert delete_params == (COLLECTION_ID, USER_ID)
