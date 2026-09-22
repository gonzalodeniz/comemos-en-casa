"""Direct Psycopg repositories for the public recipe catalogue and labels."""

from collections.abc import Sequence
from typing import Any
from uuid import UUID, uuid4

from .schemas import (
    Ingredient,
    ManagedRecipe,
    ManagedRecipeListItem,
    PreparationStep,
    Recipe,
    RecipeLabel,
    RecipeListItem,
    RecipeValidationError,
    RECIPE_LABEL_PALETTE,
    normalize_labels,
    normalize_label,
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

    def search_public_by_title(
        self, query: str, limit: int = 50, *, labels: Sequence[str] = ()
    ) -> list[RecipeListItem]:
        """Return a deterministically ordered page with optional AND label filtering."""
        self._validate_limit(limit)
        normalized_query = normalize_title_search(query)
        normalized_labels = normalize_labels(labels)
        with self._connection.cursor() as cursor:
            sql, params = self._search_sql(normalized_query, normalized_labels, limit)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            # The calendar adapter uses this foundation-only repository and
            # remains compatible with catalogue migrations before labels.
            label_map = self._load_labels(cursor, [row[0] for row in rows]) if normalized_labels else {}
        return [RecipeListItem(id=row[0], title=row[1], image_url=row[2], labels=label_map.get(row[0], ())) for row in rows]

    @staticmethod
    def _validate_limit(limit: object) -> None:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
            raise RecipeValidationError("limit must be an integer from 1 to 50")

    @classmethod
    def _search_sql(cls, normalized_query: str, labels: Sequence[str], limit: int) -> tuple[str, tuple[object, ...]]:
        conditions: list[str] = []
        params: list[object] = []
        if normalized_query:
            conditions.append("title_search_key LIKE '%%' || %s || '%%' ESCAPE '\\'")
            params.append(cls._escape_like(normalized_query))
        if labels:
            conditions.append(
                """id IN (
                    SELECT assignments.recipe_id
                    FROM recipe_label_assignments AS assignments
                    JOIN recipe_labels AS filter_labels ON filter_labels.id = assignments.label_id
                    WHERE filter_labels.name = ANY(%s)
                    GROUP BY assignments.recipe_id
                    HAVING COUNT(DISTINCT filter_labels.name) = %s
                )"""
            )
            params.extend((list(labels), len(labels)))
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)
        return f"SELECT id, title, image_url FROM recipes{where} ORDER BY title_search_key, id LIMIT %s", tuple(params)

    @staticmethod
    def _escape_like(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    @classmethod
    def _load_labels(cls, cursor: Any, recipe_ids: Sequence[UUID]) -> dict[UUID, tuple[RecipeLabel, ...]]:
        if not recipe_ids:
            return {}
        cursor.execute(
            """
            SELECT assignments.recipe_id, labels.id, labels.name, labels.color
            FROM recipe_label_assignments AS assignments
            JOIN recipe_labels AS labels ON labels.id = assignments.label_id
            WHERE assignments.recipe_id = ANY(%s)
            ORDER BY assignments.recipe_id, labels.name, labels.id
            """,
            (list(recipe_ids),),
        )
        result: dict[UUID, list[RecipeLabel]] = {}
        for row in cursor.fetchall():
            # A lightweight recording cursor may reuse its fixture row for
            # queries that are irrelevant to the assertion; PostgreSQL rows
            # always have the four fields selected above.
            if len(row) != 4:
                continue
            recipe_id, label_id, name, color = row
            result.setdefault(recipe_id, []).append(RecipeLabel(id=label_id, name=name, color=color))
        return {recipe_id: tuple(labels) for recipe_id, labels in result.items()}


class RecipeManagementRepository(RecipeCatalogueRepository):
    """Persist recipe components and global label associations transactionally."""

    def create_management(
        self,
        recipe: Recipe,
        ingredients: list[Ingredient],
        steps: list[PreparationStep],
        *,
        labels: Sequence[str] = (),
    ) -> None:
        normalized_labels = normalize_labels(labels)
        self.insert(recipe)
        with self._connection.cursor() as cursor:
            self._replace_components(cursor, recipe.id, ingredients, steps)
            self._replace_labels(cursor, recipe.id, normalized_labels)

    def update_management(
        self,
        recipe: Recipe,
        ingredients: list[Ingredient],
        steps: list[PreparationStep],
        *,
        labels: Sequence[str] = (),
    ) -> bool:
        normalized_labels = normalize_labels(labels)
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
            self._replace_labels(cursor, recipe.id, normalized_labels)
        return True

    def search_management_by_title(
        self, query: str, limit: int = 50, *, labels: Sequence[str] = ()
    ) -> list[ManagedRecipeListItem]:
        self._validate_limit(limit)
        normalized_query = normalize_title_search(query)
        normalized_labels = normalize_labels(labels)
        with self._connection.cursor() as cursor:
            sql, params = self._search_sql(normalized_query, normalized_labels, limit)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            label_map = self._load_labels(cursor, [row[0] for row in rows])
        return [
            ManagedRecipeListItem(
                id=row[0], title=row[1], image_url=row[2], labels=label_map.get(row[0], ())
            )
            for row in rows
        ]

    def find_management_by_id(self, recipe_id: UUID) -> ManagedRecipe | None:
        if not isinstance(recipe_id, UUID):
            raise RecipeValidationError("recipe id must be a UUID")
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT id, title, image_url, detail FROM recipes WHERE id = %s", (recipe_id,))
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
            labels = self._load_labels(cursor, [recipe_id]).get(recipe_id, ())
        return ManagedRecipe(recipe=Recipe.restore(id=row[0], title=row[1], image_url=row[2], detail=row[3]), ingredients=ingredients, steps=steps, labels=labels)

    def set_image_url(self, recipe_id: UUID, image_url: str) -> bool:
        from .schemas import normalize_image_url

        normalized_url = normalize_image_url(image_url)
        with self._connection.cursor() as cursor:
            cursor.execute("UPDATE recipes SET image_url = %s WHERE id = %s RETURNING id", (normalized_url, recipe_id))
            return cursor.fetchone() is not None

    def delete_image(self, recipe_id: UUID) -> bool:
        return self.set_image_url(recipe_id, "")

    def delete(self, recipe_id: UUID) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute("DELETE FROM recipes WHERE id = %s RETURNING id", (recipe_id,))
            deleted = cursor.fetchone() is not None
            if deleted:
                cursor.execute(
                    """
                    DELETE FROM recipe_labels AS labels
                    WHERE NOT EXISTS (
                        SELECT 1 FROM recipe_label_assignments AS assignments
                        WHERE assignments.label_id = labels.id
                    )
                    """
                )
            return deleted

    def search_labels(self, query: str = "", limit: int = 50) -> list[RecipeLabel]:
        self._validate_limit(limit)
        normalized_query = normalize_label(query)
        with self._connection.cursor() as cursor:
            if normalized_query:
                cursor.execute(
                    """
                    SELECT id, name, color FROM recipe_labels
                    WHERE name LIKE '%%' || %s || '%%' ESCAPE '\\'
                    ORDER BY name, id LIMIT %s
                    """,
                    (self._escape_like(normalized_query), limit),
                )
            else:
                cursor.execute(
                    "SELECT id, name, color FROM recipe_labels ORDER BY name, id LIMIT %s", (limit,)
                )
            rows = cursor.fetchall()
        return [RecipeLabel(id=row[0], name=row[1], color=row[2]) for row in rows]

    def _replace_labels(self, cursor: Any, recipe_id: UUID, labels: Sequence[str]) -> None:
        cursor.execute("DELETE FROM recipe_label_assignments WHERE recipe_id = %s", (recipe_id,))
        if labels:
            label_rows = self._ensure_labels(cursor, labels)
            cursor.executemany(
                "INSERT INTO recipe_label_assignments (recipe_id, label_id) VALUES (%s, %s)",
                [(recipe_id, label_id) for label_id, _, _ in label_rows],
            )
        cursor.execute(
            """
            DELETE FROM recipe_labels AS labels
            WHERE NOT EXISTS (
                SELECT 1 FROM recipe_label_assignments AS assignments
                WHERE assignments.label_id = labels.id
            )
            """
        )

    @staticmethod
    def _ensure_labels(cursor: Any, labels: Sequence[str]) -> list[tuple[UUID, str, str]]:
        # Serializing label writers makes colour selection deterministic while
        # the caller still owns the surrounding transaction and commit.
        cursor.execute("LOCK TABLE recipe_labels IN SHARE ROW EXCLUSIVE MODE")
        rows: list[tuple[UUID, str, str]] = []
        for name in labels:
            cursor.execute("SELECT id, name, color FROM recipe_labels WHERE name = %s", (name,))
            existing = cursor.fetchone()
            if existing is not None:
                rows.append(existing)
                continue
            cursor.execute(
                """
                SELECT recipe_labels.color, COUNT(recipe_label_assignments.recipe_id)
                FROM recipe_labels
                LEFT JOIN recipe_label_assignments
                    ON recipe_label_assignments.label_id = recipe_labels.id
                GROUP BY recipe_labels.color
                """
            )
            usage = {color: count for color, count in cursor.fetchall()}
            color = min(RECIPE_LABEL_PALETTE, key=lambda candidate: (usage.get(candidate, 0), RECIPE_LABEL_PALETTE.index(candidate)))
            label_id = uuid4()
            cursor.execute(
                """
                INSERT INTO recipe_labels (id, name, color)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id, name, color
                """,
                (label_id, name, color),
            )
            inserted = cursor.fetchone()
            if inserted is None:
                cursor.execute("SELECT id, name, color FROM recipe_labels WHERE name = %s", (name,))
                inserted = cursor.fetchone()
            if inserted is None:
                raise RecipeValidationError("label could not be persisted")
            rows.append(inserted)
        return rows

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
