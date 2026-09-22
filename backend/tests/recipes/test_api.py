from __future__ import annotations

import importlib
from collections.abc import Sequence
from pathlib import Path
import sys
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.recipes.schemas import (
    Ingredient,
    ManagedRecipe,
    ManagedRecipeListItem,
    PreparationStep,
    Recipe,
    RecipeLabel,
    normalize_labels,
)


RECIPE_ID = UUID("12345678-1234-5678-1234-567812345678")
RAPID_LABEL = RecipeLabel(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"), "rápido", "#1D4ED8")
VEGETARIAN_LABEL = RecipeLabel(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2"), "vegetariano", "#047857")
KNOWN_LABELS = {label.name: label for label in (RAPID_LABEL, VEGETARIAN_LABEL)}


def _recipe_labels(values: Sequence[str]) -> tuple[RecipeLabel, ...]:
    normalized = normalize_labels(values)
    return tuple(
        KNOWN_LABELS.get(
            name,
            RecipeLabel(uuid5(NAMESPACE_URL, f"comemos-en-casa/recipe-label/{name}"), name, "#1D4ED8"),
        )
        for name in normalized
    )


class RecipeRepository:
    stored = ManagedRecipe(
        recipe=Recipe(id=RECIPE_ID, title="Borrador público", image_url="", detail="Una receta visible."),
        ingredients=(Ingredient(name="Tomate", quantity="2"),),
        steps=(PreparationStep(instruction="Cortar el tomate."),),
        labels=(RAPID_LABEL,),
    )
    created: dict[UUID, ManagedRecipe] = {}

    def __init__(self, _: object) -> None:
        pass

    def _all_recipes(self) -> tuple[ManagedRecipe, ...]:
        return (self.stored, *self.created.values())

    def _find(self, recipe_id: UUID) -> ManagedRecipe | None:
        if recipe_id == self.stored.recipe.id:
            return self.stored
        return self.created.get(recipe_id)

    def _replace(self, recipe: ManagedRecipe) -> None:
        if recipe.recipe.id == self.stored.recipe.id:
            type(self).stored = recipe
        else:
            type(self).created[recipe.recipe.id] = recipe

    def search_management_by_title(
        self, _: str, limit: int, *, labels: Sequence[str] = ()
    ) -> list[ManagedRecipeListItem]:
        requested = set(normalize_labels(labels))
        return [
            ManagedRecipeListItem(
                recipe.recipe.id, recipe.recipe.title, recipe.recipe.image_url, recipe.labels
            )
            for recipe in self._all_recipes()
            if requested <= {label.name for label in recipe.labels}
        ][:limit]

    def find_management_by_id(self, recipe_id: UUID) -> ManagedRecipe | None:
        return self._find(recipe_id)

    def create_management(
        self,
        recipe: Recipe,
        ingredients: list[Ingredient],
        steps: list[PreparationStep],
        *,
        labels: Sequence[str] = (),
    ) -> None:
        type(self).created[recipe.id] = ManagedRecipe(
            recipe=recipe,
            ingredients=tuple(ingredients),
            steps=tuple(steps),
            labels=_recipe_labels(labels),
        )

    def update_management(
        self,
        recipe: Recipe,
        ingredients: list[Ingredient],
        steps: list[PreparationStep],
        *,
        labels: Sequence[str] = (),
    ) -> bool:
        if self._find(recipe.id) is None:
            return False
        self._replace(
            ManagedRecipe(
                recipe=recipe,
                ingredients=tuple(ingredients),
                steps=tuple(steps),
                labels=_recipe_labels(labels),
            )
        )
        return True

    def set_image_url(self, recipe_id: UUID, image_url: str) -> bool:
        existing = self._find(recipe_id)
        if existing is None:
            return False
        self._replace(
            ManagedRecipe(
                recipe=Recipe.update_foundation(
                    id=recipe_id,
                    title=existing.recipe.title,
                    image_url=image_url,
                    detail=existing.recipe.detail,
                ),
                ingredients=existing.ingredients,
                steps=existing.steps,
                labels=existing.labels,
            )
        )
        return True

    def delete_image(self, recipe_id: UUID) -> bool:
        return self.set_image_url(recipe_id, "")

    def search_labels(self, query: str = "", limit: int = 50) -> list[RecipeLabel]:
        normalized_query = query.strip().casefold()
        labels = {label.name: label for recipe in self._all_recipes() for label in recipe.labels}
        return [label for name, label in sorted(labels.items()) if normalized_query in name][:limit]

    def delete(self, recipe_id: UUID) -> bool:
        return self._find(recipe_id) is not None


def _reset_repository() -> None:
    RecipeRepository.stored = ManagedRecipe(
        recipe=Recipe(id=RECIPE_ID, title="Borrador público", image_url="", detail="Una receta visible."),
        ingredients=(Ingredient(name="Tomate", quantity="2"),),
        steps=(PreparationStep(instruction="Cortar el tomate."),),
        labels=(RAPID_LABEL,),
    )
    RecipeRepository.created = {}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db/app")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    sys.modules.pop("comemos_en_casa.app", None)
    app_module = importlib.import_module("comemos_en_casa.app")
    application = app_module.create_app()
    from comemos_en_casa.recipes import api

    _reset_repository()
    monkeypatch.setattr(api, "RecipeManagementRepository", RecipeRepository)
    application.dependency_overrides[app_module.get_connection] = lambda: object()
    return TestClient(application)


@pytest.fixture
def anonymous_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db/app")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    sys.modules.pop("comemos_en_casa.app", None)
    app_module = importlib.import_module("comemos_en_casa.app")
    application = app_module.create_app()
    from comemos_en_casa.recipes import api

    _reset_repository()
    monkeypatch.setattr(api, "RecipeManagementRepository", RecipeRepository)
    application.dependency_overrides[app_module.get_connection] = lambda: object()
    return TestClient(application)


def test_public_reads_have_labels_and_no_editorial_status(client: TestClient) -> None:
    listing = client.get("/api/v1/recipes")
    detail = client.get(f"/api/v1/recipes/{RECIPE_ID}")

    assert listing.status_code == detail.status_code == 200
    assert "estado" not in listing.json()["recetas"][0]
    assert "estado" not in detail.json()
    assert detail.json()["titulo"] == "Borrador público"
    assert detail.json()["ingredientes"] == [{"nombre": "Tomate", "cantidad": "2"}]
    assert all(set(label) == {"id", "name", "color"} for label in detail.json()["labels"])


def test_recipe_write_contract_normalizes_labels_and_returns_label_objects(client: TestClient) -> None:
    response = client.post(
        "/api/v1/recipes",
        json={
            "titulo": "Sopa",
            "detalle": "Hervir.",
            "ingredientes": [],
            "pasos": [],
            "labels": ["  COCINA   rápida  ", "cocina rápida", ""],
        },
    )

    assert response.status_code == 201
    assert response.json()["labels"]
    assert response.json()["labels"][0]["name"] == "cocina rápida"
    assert all(set(label) == {"id", "name", "color"} for label in response.json()["labels"])
    assert "estado" not in response.json()


def test_anonymous_recipe_crud_and_image_operations(anonymous_client: TestClient) -> None:
    payload = {"titulo": "Sopa", "detalle": "Hervir.", "ingredientes": [], "pasos": [], "labels": []}
    created = anonymous_client.post("/api/v1/recipes", json=payload)
    assert created.status_code == 201

    updated = anonymous_client.patch(f"/api/v1/recipes/{RECIPE_ID}", json=payload)
    replaced = anonymous_client.put(f"/api/v1/recipes/{RECIPE_ID}", json=payload)
    deleted = anonymous_client.delete(f"/api/v1/recipes/{RECIPE_ID}")
    uploaded = anonymous_client.post(
        f"/api/v1/recipes/{RECIPE_ID}/image",
        files={"file": ("sopa.png", b"\x89PNG\r\n\x1a\nimage-data", "image/png")},
    )
    removed_image = anonymous_client.delete(f"/api/v1/recipes/{RECIPE_ID}/image")

    assert updated.status_code == replaced.status_code == 200
    assert deleted.status_code == 204
    assert uploaded.status_code == removed_image.status_code == 200
    assert removed_image.json()["imagenUrl"] == ""


def test_editorial_state_routes_are_removed(client: TestClient) -> None:
    assert client.post(f"/api/v1/recipes/{RECIPE_ID}/publish").status_code == 404
    assert client.post(f"/api/v1/recipes/{RECIPE_ID}/draft").status_code == 404


def test_authenticated_create_and_image_upload_are_public_contracts(client: TestClient) -> None:
    create = client.post(
        "/api/v1/recipes",
        json={"titulo": "Sopa", "detalle": "Hervir.", "ingredientes": [{"nombre": "Agua"}], "pasos": [{"instruccion": "Hervir agua."}], "labels": []},
    )
    recipe_id = create.json().get("id", str(RECIPE_ID))
    image = client.post(
        f"/api/v1/recipes/{recipe_id}/image",
        files={"file": ("sopa.png", b"\x89PNG\r\n\x1a\nimage-data", "image/png")},
    )

    assert create.status_code == 201
    assert "estado" not in create.json()
    assert image.status_code == 200
    assert image.json()["imagenUrl"].startswith("/media/recipes/")


def test_repeated_label_query_params_use_and_semantics_and_ignore_empty_values(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    labels = {"rápido": RAPID_LABEL, "vegetariano": VEGETARIAN_LABEL}
    recipes = [
        ManagedRecipeListItem(
            UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1"), "Ambas", "", (labels["rápido"], labels["vegetariano"])
        ),
        ManagedRecipeListItem(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb2"), "Rápida", "", (labels["rápido"],)),
        ManagedRecipeListItem(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb3"), "Verde", "", (labels["vegetariano"],)),
    ]

    class FilteringRepository(RecipeRepository):
        def search_management_by_title(self, query: str, limit: int, *args: object, **kwargs: object) -> list[ManagedRecipeListItem]:
            requested = kwargs.get("labels") or kwargs.get("label_names")
            if requested is None and args:
                requested = args[0]
            if requested is None:
                return recipes[:limit]
            effective = set(requested)
            return [recipe for recipe in recipes if effective <= {label.name for label in recipe.labels}][:limit]

        search_public_by_title = search_management_by_title

    from comemos_en_casa.recipes import api

    monkeypatch.setattr(api, "RecipeManagementRepository", FilteringRepository)

    both = client.get(
        "/api/v1/recipes",
        params=[("label", "RÁPIDO"), ("label", " vegetariano "), ("label", "rápido")],
    )
    empty = client.get("/api/v1/recipes", params=[("label", ""), ("label", "  ")])
    nonexistent = client.get("/api/v1/recipes", params=[("label", "desconocida")])

    assert [recipe["id"] for recipe in both.json()["recetas"]] == ["bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1"]
    assert len(empty.json()["recetas"]) == 3
    assert nonexistent.json()["recetas"] == []


def test_image_upload_rejects_non_image_content(client: TestClient) -> None:
    response = client.post(
        f"/api/v1/recipes/{RECIPE_ID}/image", files={"file": ("not-image.txt", b"not an image", "text/plain")}
    )

    assert response.status_code == 422
    assert response.json()["error"]["message"] == "La imagen debe ser JPEG, PNG o WebP."
