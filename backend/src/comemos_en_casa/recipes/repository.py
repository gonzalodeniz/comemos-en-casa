"""Direct Psycopg repositories for public recipe catalogue and management data."""

from typing import Any
from uuid import UUID

from .schemas import (
    Ingredient,
    ManagedRecipe,
    ManagedRecipeListItem,
    PreparationStep,
    Recipe,
    RecipeListItem,
    RecipeValidationError,
    normalize_title_search,
)


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
                (recipe.id, recipe.title, recipe.image_url, recipe.detail, normalize_title_search(recipe.title)),
            )

    def update_foundation(self, recipe: Recipe) -> bool:
        """Update foundation fields and search key while leaving the UUID unchanged."""
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE recipes
                SET title = %s, image_url = %s, detail = %s, title_search_key = %s
                WHERE id = %s
                RETURNING id
                """,
                (recipe.title, recipe.image_url, recipe.detail, normalize_title_search(recipe.title), recipe.id),
            )
            return cursor.fetchone() is not None

    def find_public_by_id(self, recipe_id: UUID) -> Recipe | None:
        """Return the current public foundation value for an existing UUID."""
        if not isinstance(recipe_id, UUID):
            raise RecipeValidationError("recipe id must be a UUID")
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT id, title, image_url, detail FROM recipes WHERE id = %s", (recipe_id,))
            row = cursor.fetchone()
        return None if row is None else Recipe.restore(id=row[0], title=row[1], image_url=row[2], detail=row[3])

    def search_public_by_title(self, query: str, limit: int = 50) -> list[RecipeListItem]:
        """Return a deterministically ordered page using literal title containment."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
            raise RecipeValidationError("limit must be an integer from 1 to 50")
        normalized_query = normalize_title_search(query)
        with self._connection.cursor() as cursor:
            if normalized_query:
                cursor.execute(
                    """
                    SELECT id, title, image_url FROM recipes
                    WHERE title_search_key LIKE '%%' || %s || '%%' ESCAPE '\\'
                    ORDER BY title_search_key, id LIMIT %s
                    """,
                    (self._escape_like(normalized_query), limit),
                )
            else:
                cursor.execute("SELECT id, title, image_url FROM recipes ORDER BY title_search_key, id LIMIT %s", (limit,))
            rows = cursor.fetchall()
        return [RecipeListItem(id=row[0], title=row[1], image_url=row[2]) for row in rows]

    @staticmethod
    def _escape_like(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class RecipeManagementRepository(RecipeCatalogueRepository):
    """Persist ingredients and steps in their normalized, ordered relations."""

    def create_management(self, recipe: Recipe, ingredients: list[Ingredient], steps: list[PreparationStep], status: str) -> None:
        self.insert(recipe)
        with self._connection.cursor() as cursor:
            cursor.execute("UPDATE recipes SET status = %s WHERE id = %s", (status, recipe.id))
            self._replace_components(cursor, recipe.id, ingredients, steps)

    def update_management(self, recipe: Recipe, ingredients: list[Ingredient], steps: list[PreparationStep]) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE recipes SET title = %s, image_url = %s, detail = %s, title_search_key = %s
                WHERE id = %s RETURNING id
                """,
                (recipe.title, recipe.image_url, recipe.detail, normalize_title_search(recipe.title), recipe.id),
            )
            if cursor.fetchone() is None:
                return False
            self._replace_components(cursor, recipe.id, ingredients, steps)
        return True

    def search_management_by_title(self, query: str, limit: int = 50) -> list[ManagedRecipeListItem]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
            raise RecipeValidationError("limit must be an integer from 1 to 50")
        normalized_query = normalize_title_search(query)
        with self._connection.cursor() as cursor:
            if normalized_query:
                cursor.execute(
                    """
                    SELECT id, title, image_url, status FROM recipes
                    WHERE title_search_key LIKE '%%' || %s || '%%' ESCAPE '\\'
                    ORDER BY title_search_key, id LIMIT %s
                    """,
                    (self._escape_like(normalized_query), limit),
                )
            else:
                cursor.execute(
                    "SELECT id, title, image_url, status FROM recipes ORDER BY title_search_key, id LIMIT %s", (limit,)
                )
            rows = cursor.fetchall()
        return [ManagedRecipeListItem(id=row[0], title=row[1], image_url=row[2], status=row[3]) for row in rows]

    def find_management_by_id(self, recipe_id: UUID) -> ManagedRecipe | None:
        if not isinstance(recipe_id, UUID):
            raise RecipeValidationError("recipe id must be a UUID")
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT id, title, image_url, detail, status FROM recipes WHERE id = %s", (recipe_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            cursor.execute(
                "SELECT name, quantity FROM recipe_ingredients WHERE recipe_id = %s ORDER BY position", (recipe_id,)
            )
            ingredients = tuple(Ingredient(name=item[0], quantity=item[1]) for item in cursor.fetchall())
            cursor.execute(
                "SELECT instruction FROM recipe_preparation_steps WHERE recipe_id = %s ORDER BY position", (recipe_id,)
            )
            steps = tuple(PreparationStep(instruction=item[0]) for item in cursor.fetchall())
        return ManagedRecipe(
            recipe=Recipe.restore(id=row[0], title=row[1], image_url=row[2], detail=row[3]),
            status=row[4], ingredients=ingredients, steps=steps
        )

    def set_status(self, recipe_id: UUID, status: str) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute("UPDATE recipes SET status = %s WHERE id = %s RETURNING id", (status, recipe_id))
            return cursor.fetchone() is not None

    def set_image_url(self, recipe_id: UUID, image_url: str) -> bool:
        from .schemas import normalize_image_url

        normalized_url = normalize_image_url(image_url)
        with self._connection.cursor() as cursor:
            cursor.execute("UPDATE recipes SET image_url = %s WHERE id = %s RETURNING id", (normalized_url, recipe_id))
            return cursor.fetchone() is not None

    def delete(self, recipe_id: UUID) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute("DELETE FROM recipes WHERE id = %s RETURNING id", (recipe_id,))
            return cursor.fetchone() is not None

    @staticmethod
    def _replace_components(cursor: Any, recipe_id: UUID, ingredients: list[Ingredient], steps: list[PreparationStep]) -> None:
        cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = %s", (recipe_id,))
        cursor.execute("DELETE FROM recipe_preparation_steps WHERE recipe_id = %s", (recipe_id,))
        if ingredients:
            cursor.executemany(
                "INSERT INTO recipe_ingredients (recipe_id, position, name, quantity) VALUES (%s, %s, %s, %s)",
                [(recipe_id, position, item.name, item.quantity) for position, item in enumerate(ingredients, start=1)],
            )
        if steps:
            cursor.executemany(
                "INSERT INTO recipe_preparation_steps (recipe_id, position, instruction) VALUES (%s, %s, %s)",
                [(recipe_id, position, item.instruction) for position, item in enumerate(steps, start=1)],
            )
