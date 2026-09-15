from __future__ import annotations

import importlib
from pathlib import Path
import sys
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.auth.models import User
from comemos_en_casa.recipes.schemas import Ingredient, ManagedRecipe, ManagedRecipeListItem, PreparationStep, Recipe


RECIPE_ID = UUID("12345678-1234-5678-1234-567812345678")
USER = User(RECIPE_ID, "subject", "persona@example.test", "Persona", None)


class RecipeRepository:
    stored = ManagedRecipe(
        recipe=Recipe(id=RECIPE_ID, title="Borrador público", image_url="", detail="Una receta visible."),
        status="draft",
        ingredients=(Ingredient(name="Tomate", quantity="2"),),
        steps=(PreparationStep(instruction="Cortar el tomate."),),
    )

    def __init__(self, _: object) -> None:
        pass

    def search_management_by_title(self, _: str, __: int) -> list[ManagedRecipeListItem]:
        recipe = self.stored
        return [ManagedRecipeListItem(recipe.recipe.id, recipe.recipe.title, recipe.recipe.image_url, recipe.status)]

    def find_management_by_id(self, recipe_id: UUID) -> ManagedRecipe | None:
        return self.stored if recipe_id == self.stored.recipe.id else None

    def create_management(self, recipe: Recipe, ingredients: list[Ingredient], steps: list[PreparationStep], status: str) -> None:
        type(self).stored = ManagedRecipe(recipe, status, tuple(ingredients), tuple(steps))

    def update_management(self, recipe: Recipe, ingredients: list[Ingredient], steps: list[PreparationStep]) -> bool:
        type(self).stored = ManagedRecipe(recipe, self.stored.status, tuple(ingredients), tuple(steps))
        return True

    def set_status(self, recipe_id: UUID, status: str) -> bool:
        if recipe_id != self.stored.recipe.id:
            return False
        type(self).stored = ManagedRecipe(self.stored.recipe, status, self.stored.ingredients, self.stored.steps)
        return True

    def set_image_url(self, recipe_id: UUID, image_url: str) -> bool:
        if recipe_id != self.stored.recipe.id:
            return False
        type(self).stored = ManagedRecipe(
            Recipe.update_foundation(id=recipe_id, title=self.stored.recipe.title, image_url=image_url, detail=self.stored.recipe.detail),
            self.stored.status,
            self.stored.ingredients,
            self.stored.steps,
        )
        return True

    def delete(self, recipe_id: UUID) -> bool:
        return recipe_id == self.stored.recipe.id


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db/app")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    sys.modules.pop("comemos_en_casa.app", None)
    app_module = importlib.import_module("comemos_en_casa.app")
    application = app_module.create_app()
    from comemos_en_casa.auth.api import current_user_dependency
    from comemos_en_casa.recipes import api

    RecipeRepository.stored = ManagedRecipe(
        recipe=Recipe(id=RECIPE_ID, title="Borrador público", image_url="", detail="Una receta visible."),
        status="draft",
        ingredients=(Ingredient(name="Tomate", quantity="2"),),
        steps=(PreparationStep(instruction="Cortar el tomate."),),
    )
    monkeypatch.setattr(api, "RecipeManagementRepository", RecipeRepository)
    application.dependency_overrides[app_module.get_connection] = lambda: object()
    application.dependency_overrides[current_user_dependency] = lambda: USER
    return TestClient(application)


def test_public_reads_include_drafts_and_spanish_field_labels(client: TestClient) -> None:
    listing = client.get("/api/v1/recipes")
    detail = client.get(f"/api/v1/recipes/{RECIPE_ID}")

    assert listing.status_code == detail.status_code == 200
    assert listing.json()["recetas"][0]["estado"] == "draft"
    assert detail.json()["titulo"] == "Borrador público"
    assert detail.json()["ingredientes"] == [{"nombre": "Tomate", "cantidad": "2"}]


def test_authenticated_create_publish_and_image_upload(client: TestClient) -> None:
    create = client.post(
        "/api/v1/recipes",
        json={"titulo": "Sopa", "detalle": "Hervir.", "ingredientes": [{"nombre": "Agua"}], "pasos": [{"instruccion": "Hervir agua."}]},
    )
    recipe_id = create.json()["id"]
    publish = client.post(f"/api/v1/recipes/{recipe_id}/publish")
    image = client.post(
        f"/api/v1/recipes/{recipe_id}/image",
        files={"file": ("sopa.png", b"\x89PNG\r\n\x1a\nimage-data", "image/png")},
    )

    assert create.status_code == 201
    assert create.json()["estado"] == "draft"
    assert publish.json()["estado"] == "published"
    assert image.status_code == 200
    assert image.json()["imagenUrl"].startswith("/media/recipes/")


def test_image_upload_rejects_non_image_content(client: TestClient) -> None:
    response = client.post(
        f"/api/v1/recipes/{RECIPE_ID}/image", files={"file": ("not-image.txt", b"not an image", "text/plain")}
    )

    assert response.status_code == 422
    assert response.json()["error"]["message"] == "La imagen debe ser JPEG, PNG o WebP."
