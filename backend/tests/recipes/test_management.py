from __future__ import annotations

from pathlib import Path
import sys
from uuid import UUID

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.recipes.management import RecipeManagementError, RecipeManagementService
from comemos_en_casa.recipes.schemas import Ingredient, PreparationStep, Recipe


RECIPE_ID = UUID("12345678-1234-5678-1234-567812345678")


class Repository:
    def __init__(self) -> None:
        self.recipe: Recipe | None = None
        self.ingredients: list[Ingredient] = []
        self.steps: list[PreparationStep] = []
        self.status = "draft"

    def create_management(self, recipe: Recipe, ingredients: list[Ingredient], steps: list[PreparationStep], status: str) -> None:
        self.recipe = recipe
        self.ingredients = ingredients
        self.steps = steps
        self.status = status


def test_create_recipe_starts_as_a_public_draft_with_normalized_components() -> None:
    repository = Repository()
    created = RecipeManagementService(repository).create(
        title="  Sopa de verduras ",
        detail=" Cocinar y servir. ",
        ingredients=[Ingredient(name="  zanahoria ", quantity=" 2 ")],
        steps=[PreparationStep(instruction=" Cortar la zanahoria. ")],
        uuid_factory=lambda: RECIPE_ID,
    )

    assert created.recipe == Recipe(id=RECIPE_ID, title="Sopa de verduras", image_url="", detail="Cocinar y servir.")
    assert created.status == "draft"
    assert repository.ingredients == [Ingredient(name="zanahoria", quantity="2")]
    assert repository.steps == [PreparationStep(instruction="Cortar la zanahoria.")]


@pytest.mark.parametrize("status", ["private", "published ", ""])
def test_status_is_limited_to_public_draft_or_published_values(status: str) -> None:
    with pytest.raises(RecipeManagementError, match="estado"):
        RecipeManagementService(Repository()).validate_status(status)
