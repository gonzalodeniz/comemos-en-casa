"""Direct Psycopg repository for the public recipe catalogue foundation."""

from typing import Any
from uuid import UUID

from .schemas import Recipe, RecipeListItem, RecipeValidationError, normalize_title_search


class RecipeCatalogueRepository:
    """Execute recipe SQL through a caller-owned connection and transaction."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def insert(self, recipe: Recipe) -> None:
        """Insert a normalized recipe without committing the caller's transaction."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO recipes (id, title, image_url, detail, title_search_key)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    recipe.id,
                    recipe.title,
                    recipe.image_url,
                    recipe.detail,
                    normalize_title_search(recipe.title),
                ),
            )

    def update_foundation(self, recipe: Recipe) -> bool:
        """Update foundation fields and search key while leaving the UUID unchanged."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE recipes
                SET title = %s,
                    image_url = %s,
                    detail = %s,
                    title_search_key = %s
                WHERE id = %s
                RETURNING id
                """,
                (
                    recipe.title,
                    recipe.image_url,
                    recipe.detail,
                    normalize_title_search(recipe.title),
                    recipe.id,
                ),
            )
            return cursor.fetchone() is not None

    def find_public_by_id(self, recipe_id: UUID) -> Recipe | None:
        """Return the current public foundation value for an existing UUID."""
        if not isinstance(recipe_id, UUID):
            raise RecipeValidationError("recipe id must be a UUID")

        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, image_url, detail
                FROM recipes
                WHERE id = %s
                """,
                (recipe_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None
        return Recipe.restore(id=row[0], title=row[1], image_url=row[2], detail=row[3])

    def search_public_by_title(self, query: str, limit: int = 50) -> list[RecipeListItem]:
        """Return a deterministically ordered page using literal title containment."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
            raise RecipeValidationError("limit must be an integer from 1 to 50")

        normalized_query = normalize_title_search(query)
        with self._connection.cursor() as cursor:
            if normalized_query:
                cursor.execute(
                    """
                    SELECT id, title, image_url
                    FROM recipes
                    WHERE title_search_key LIKE '%%' || %s || '%%' ESCAPE '\\'
                    ORDER BY title_search_key, id
                    LIMIT %s
                    """,
                    (self._escape_like(normalized_query), limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, title, image_url
                    FROM recipes
                    ORDER BY title_search_key, id
                    LIMIT %s
                    """,
                    (limit,),
                )
            rows = cursor.fetchall()

        return [RecipeListItem(id=row[0], title=row[1], image_url=row[2]) for row in rows]

    @staticmethod
    def _escape_like(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
