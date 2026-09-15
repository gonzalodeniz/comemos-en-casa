"""Recipe-management use cases shared by authenticated HTTP routes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from uuid import UUID, uuid4

from .schemas import Ingredient, ManagedRecipe, PreparationStep, Recipe


class RecipeManagementError(ValueError):
    """Raised when a recipe-management lifecycle value is invalid."""


class RecipeManagementWriter(Protocol):
    def create_management(
        self, recipe: Recipe, ingredients: list[Ingredient], steps: list[PreparationStep], status: str
    ) -> None: ...


class RecipeManagementService:
    """Keep public recipe lifecycle decisions outside transport and SQL concerns."""

    PUBLIC_STATUSES = frozenset({"draft", "published"})

    def __init__(self, repository: RecipeManagementWriter) -> None:
        self._repository = repository

    @classmethod
    def validate_status(cls, status: object) -> str:
        if not isinstance(status, str) or status not in cls.PUBLIC_STATUSES:
            raise RecipeManagementError("El estado debe ser 'draft' o 'published'.")
        return status

    def create(
        self,
        *,
        title: str,
        detail: str,
        ingredients: list[Ingredient],
        steps: list[PreparationStep],
        uuid_factory: Callable[[], UUID] = uuid4,
    ) -> ManagedRecipe:
        recipe = Recipe.create(title=title, image_url="", detail=detail, uuid_factory=uuid_factory)
        status = "draft"
        self._repository.create_management(recipe, ingredients, steps, status)
        return ManagedRecipe(recipe=recipe, status=status, ingredients=tuple(ingredients), steps=tuple(steps))
