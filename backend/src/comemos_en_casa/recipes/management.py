"""Recipe-management use cases shared by public HTTP routes."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol
from uuid import UUID, uuid4

from .schemas import (
    Ingredient,
    ManagedRecipe,
    PreparationStep,
    Recipe,
    normalize_labels,
)


class RecipeManagementError(ValueError):
    """Raised when a recipe-management value is invalid."""


class RecipeManagementWriter(Protocol):
    def create_management(
        self,
        recipe: Recipe,
        ingredients: list[Ingredient],
        steps: list[PreparationStep],
        *,
        labels: Sequence[str],
    ) -> None: ...

    def find_management_by_id(self, recipe_id: UUID) -> ManagedRecipe | None: ...


class RecipeManagementService:
    """Keep recipe lifecycle decisions outside transport and SQL concerns."""

    def __init__(self, repository: RecipeManagementWriter) -> None:
        self._repository = repository

    def create(
        self,
        *,
        title: str,
        detail: str,
        ingredients: list[Ingredient],
        steps: list[PreparationStep],
        labels: Sequence[str] = (),
        uuid_factory: Callable[[], UUID] = uuid4,
    ) -> ManagedRecipe:
        normalized_labels = normalize_labels(labels)
        recipe = Recipe.create(title=title, image_url="", detail=detail, uuid_factory=uuid_factory)
        self._repository.create_management(recipe, ingredients, steps, labels=normalized_labels)
        finder = getattr(self._repository, "find_management_by_id", None)
        stored = finder(recipe.id) if callable(finder) else None
        if stored is not None:
            return stored
        # This fallback keeps the use case useful with lightweight in-memory
        # repositories while production repositories return persisted label IDs.
        return ManagedRecipe(recipe=recipe, ingredients=tuple(ingredients), steps=tuple(steps), labels=tuple())


__all__ = ["RecipeManagementError", "RecipeManagementService"]
