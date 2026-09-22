"""Direct Psycopg persistence for private recipe favorites and collections."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from .schemas import Collection, RecipeSummary


class CollectionsRepository:
    """Execute owner-scoped collection SQL through a caller-owned connection."""

    _COLLECTION_SELECT = """
        SELECT
            collections.id,
            collections.name,
            recipes.id,
            recipes.title,
            recipes.image_url
        FROM recipe_collections AS collections
        LEFT JOIN collection_recipes AS memberships ON memberships.collection_id = collections.id
        LEFT JOIN recipes AS recipes ON recipes.id = memberships.recipe_id
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def recipe_exists(self, recipe_id: UUID) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT id FROM recipes WHERE id = %s", (recipe_id,))
            return cursor.fetchone() is not None

    def list_favorites(self, user_id: UUID) -> list[RecipeSummary]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT recipes.id, recipes.title, recipes.image_url
                FROM recipe_favorites AS favorites
                JOIN recipes AS recipes ON recipes.id = favorites.recipe_id
                WHERE favorites.user_id = %s
                ORDER BY favorites.created_at DESC, favorites.recipe_id
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
        return [self._recipe_summary(row) for row in rows]

    def add_favorite(self, user_id: UUID, recipe_id: UUID) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO recipe_favorites (user_id, recipe_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, recipe_id) DO NOTHING
                """,
                (user_id, recipe_id),
            )

    def remove_favorite(self, user_id: UUID, recipe_id: UUID) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute("DELETE FROM recipe_favorites WHERE user_id = %s AND recipe_id = %s", (user_id, recipe_id))

    def list_collections(self, user_id: UUID) -> list[Collection]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                self._COLLECTION_SELECT
                + """
                WHERE collections.user_id = %s
                ORDER BY collections.created_at DESC, collections.id, memberships.created_at, recipes.id
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
        return self._collections(rows)

    def find_collection(self, user_id: UUID, collection_id: UUID) -> Collection | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                self._COLLECTION_SELECT
                + """
                WHERE collections.user_id = %s AND collections.id = %s
                ORDER BY memberships.created_at, recipes.id
                """,
                (user_id, collection_id),
            )
            rows = cursor.fetchall()
        collections = self._collections(rows)
        return collections[0] if collections else None

    def create_collection(self, user_id: UUID, collection: Collection) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO recipe_collections (id, user_id, name) VALUES (%s, %s, %s)",
                (collection.id, user_id, collection.name),
            )

    def update_collection(self, user_id: UUID, collection: Collection) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE recipe_collections
                SET name = %s, updated_at = now()
                WHERE id = %s AND user_id = %s
                RETURNING id
                """,
                (collection.name, collection.id, user_id),
            )
            return cursor.fetchone() is not None

    def delete_collection(self, user_id: UUID, collection_id: UUID) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM recipe_collections WHERE id = %s AND user_id = %s RETURNING id",
                (collection_id, user_id),
            )
            return cursor.fetchone() is not None

    def add_recipe_to_collection(self, user_id: UUID, collection_id: UUID, recipe_id: UUID) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO collection_recipes (collection_id, recipe_id)
                SELECT id, %s FROM recipe_collections
                WHERE id = %s AND user_id = %s
                ON CONFLICT (collection_id, recipe_id) DO NOTHING
                RETURNING collection_id
                """,
                (recipe_id, collection_id, user_id),
            )
            if cursor.fetchone() is not None:
                return True
        return self.find_collection(user_id, collection_id) is not None

    def remove_recipe_from_collection(self, user_id: UUID, collection_id: UUID, recipe_id: UUID) -> bool:
        if self.find_collection(user_id, collection_id) is None:
            return False
        with self._connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM collection_recipes WHERE collection_id = %s AND recipe_id = %s",
                (collection_id, recipe_id),
            )
        return True

    @staticmethod
    def _recipe_summary(row: tuple[Any, ...]) -> RecipeSummary:
        return RecipeSummary(id=row[0], title=row[1], image_url=row[2])

    @classmethod
    def _collections(cls, rows: list[tuple[Any, ...]]) -> list[Collection]:
        collections: dict[UUID, tuple[str, list[RecipeSummary]]] = {}
        for row in rows:
            collection_id, name = row[0], row[1]
            if collection_id not in collections:
                collections[collection_id] = (name, [])
            if row[2] is not None:
                collections[collection_id][1].append(cls._recipe_summary(row[2:]))
        return [Collection(id=collection_id, name=name, recipes=tuple(recipes)) for collection_id, (name, recipes) in collections.items()]
