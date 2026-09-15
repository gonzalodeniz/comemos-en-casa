"""Calendar-facing adapter for the public recipe catalogue."""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from comemos_en_casa.recipes.repository import RecipeCatalogueRepository
from comemos_en_casa.recipes.schemas import Recipe, RecipeListItem, normalize_title_search


class CatalogueCursorError(ValueError):
    """Raised when a client cursor cannot safely continue a catalogue search."""


@dataclass(frozen=True)
class RecipeSearchPage:
    """A bounded public recipe page and an opaque continuation, when available."""

    recipes: list[RecipeListItem]
    next_cursor: str | None


class MealCalendarCatalogueAdapter:
    """Expose the catalogue's public reads in the calendar API vocabulary."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection
        self._catalogue = RecipeCatalogueRepository(connection)

    def find_public_recipe(self, recipe_id: UUID) -> Recipe | None:
        """Return one current public recipe without exposing catalogue write operations."""
        return self._catalogue.find_public_by_id(recipe_id)

    def search_public_recipes(
        self,
        query: str,
        *,
        limit: int,
        cursor: str | None = None,
    ) -> RecipeSearchPage:
        """Search public titles and continue deterministically after an opaque cursor."""
        normalized_query = normalize_title_search(query)
        if cursor is None:
            recipes = self._catalogue.search_public_by_title(query, limit=limit)
        else:
            cursor_query, title_key, recipe_id = self._decode_cursor(cursor)
            if cursor_query != normalized_query:
                raise CatalogueCursorError("cursor does not match the search query")
            recipes = self._search_after(normalized_query, title_key, recipe_id, limit)

        next_cursor = None
        if len(recipes) == limit:
            final_recipe = recipes[-1]
            next_cursor = self._encode_cursor(normalized_query, normalize_title_search(final_recipe.title), final_recipe.id)
        return RecipeSearchPage(recipes=recipes, next_cursor=next_cursor)

    def _search_after(
        self,
        normalized_query: str,
        title_key: str,
        recipe_id: UUID,
        limit: int,
    ) -> list[RecipeListItem]:
        with self._connection.cursor() as cursor:
            if normalized_query:
                cursor.execute(
                    """
                    SELECT id, title, image_url
                    FROM recipes
                    WHERE title_search_key LIKE '%%' || %s || '%%' ESCAPE '\\'
                      AND (title_search_key, id) > (%s, %s)
                    ORDER BY title_search_key, id
                    LIMIT %s
                    """,
                    (
                        RecipeCatalogueRepository._escape_like(normalized_query),
                        title_key,
                        recipe_id,
                        limit,
                    ),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, title, image_url
                    FROM recipes
                    WHERE (title_search_key, id) > (%s, %s)
                    ORDER BY title_search_key, id
                    LIMIT %s
                    """,
                    (title_key, recipe_id, limit),
                )
            rows = cursor.fetchall()
        return [RecipeListItem(id=row[0], title=row[1], image_url=row[2]) for row in rows]

    @staticmethod
    def _encode_cursor(query: str, title_key: str, recipe_id: UUID) -> str:
        payload = json.dumps(
            {"query": query, "titleKey": title_key, "id": str(recipe_id)},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str) -> tuple[str, str, UUID]:
        try:
            padded_cursor = cursor + ("=" * (-len(cursor) % 4))
            payload = json.loads(base64.urlsafe_b64decode(padded_cursor.encode("ascii")))
            query = payload["query"]
            title_key = payload["titleKey"]
            recipe_id = UUID(payload["id"])
        except (KeyError, TypeError, ValueError, UnicodeDecodeError, binascii.Error, json.JSONDecodeError) as error:
            raise CatalogueCursorError("cursor is invalid") from error
        if not isinstance(query, str) or not isinstance(title_key, str):
            raise CatalogueCursorError("cursor is invalid")
        return query, title_key, recipe_id
