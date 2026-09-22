from __future__ import annotations

import importlib
from pathlib import Path
import sys
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.auth.models import User
from comemos_en_casa.collections.schemas import Collection, RecipeSummary


USER_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OTHER_USER_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
COLLECTION_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
RECIPE_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
MISSING_ID = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
USER = User(USER_ID, "subject", "persona@example.test", "Persona", None)


class CollectionsRepository:
    favorites: set[UUID] = set()
    collections: dict[UUID, tuple[UUID, Collection]] = {}
    recipes = {RECIPE_ID: RecipeSummary(RECIPE_ID, "Sopa pública", "")}

    def __init__(self, _: object) -> None:
        pass

    def list_favorites(self, user_id: UUID) -> list[RecipeSummary]:
        return [self.recipes[recipe_id] for recipe_id in self.favorites if recipe_id in self.recipes] if user_id == USER_ID else []

    def recipe_exists(self, recipe_id: UUID) -> bool:
        return recipe_id in self.recipes

    def add_favorite(self, user_id: UUID, recipe_id: UUID) -> None:
        if user_id == USER_ID:
            self.favorites.add(recipe_id)

    def remove_favorite(self, user_id: UUID, recipe_id: UUID) -> None:
        if user_id == USER_ID:
            self.favorites.discard(recipe_id)

    def list_collections(self, user_id: UUID) -> list[Collection]:
        return [collection for owner, collection in self.collections.values() if owner == user_id]

    def find_collection(self, user_id: UUID, collection_id: UUID) -> Collection | None:
        stored = self.collections.get(collection_id)
        return None if stored is None or stored[0] != user_id else stored[1]

    def create_collection(self, user_id: UUID, collection: Collection) -> None:
        self.collections[collection.id] = (user_id, collection)

    def update_collection(self, user_id: UUID, collection: Collection) -> bool:
        if self.find_collection(user_id, collection.id) is None:
            return False
        self.collections[collection.id] = (user_id, collection)
        return True

    def delete_collection(self, user_id: UUID, collection_id: UUID) -> bool:
        if self.find_collection(user_id, collection_id) is None:
            return False
        del self.collections[collection_id]
        return True

    def add_recipe_to_collection(self, user_id: UUID, collection_id: UUID, recipe_id: UUID) -> bool:
        collection = self.find_collection(user_id, collection_id)
        if collection is None:
            return False
        recipes = collection.recipes if recipe_id in {recipe.id for recipe in collection.recipes} else (*collection.recipes, self.recipes[recipe_id])
        self.collections[collection_id] = (user_id, Collection(collection.id, collection.name, recipes))
        return True

    def remove_recipe_from_collection(self, user_id: UUID, collection_id: UUID, recipe_id: UUID) -> bool:
        collection = self.find_collection(user_id, collection_id)
        if collection is None:
            return False
        self.collections[collection_id] = (
            user_id,
            Collection(collection.id, collection.name, tuple(recipe for recipe in collection.recipes if recipe.id != recipe_id)),
        )
        return True


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db/app")
    monkeypatch.setenv("MEDIA_ROOT", str(tmp_path / "media"))
    sys.modules.pop("comemos_en_casa.app", None)
    app_module = importlib.import_module("comemos_en_casa.app")
    application = app_module.create_app()
    from comemos_en_casa.auth.api import current_user_dependency
    from comemos_en_casa.collections import api

    CollectionsRepository.favorites = set()
    CollectionsRepository.collections = {MISSING_ID: (OTHER_USER_ID, Collection(MISSING_ID, "Privada"))}
    monkeypatch.setattr(api, "CollectionsRepository", CollectionsRepository)
    application.dependency_overrides[app_module.get_connection] = lambda: object()
    application.dependency_overrides[current_user_dependency] = lambda: USER
    return TestClient(application)


def test_favorites_are_private_and_use_spanish_aliases(client: TestClient) -> None:
    assert client.put(f"/api/v1/recipes/{RECIPE_ID}/favorite").status_code == 204

    response = client.get("/api/v1/me/favorites")

    assert response.status_code == 200
    assert response.json() == {"favoritos": [{"id": str(RECIPE_ID), "titulo": "Sopa pública", "imagenUrl": ""}]}
    assert client.delete(f"/api/v1/recipes/{RECIPE_ID}/favorite").status_code == 204


def test_collection_operations_enforce_ownership_and_return_nested_public_recipes(client: TestClient) -> None:
    created = client.post("/api/v1/me/collections", json={"nombre": "  Cenas rápidas  "})
    collection_id = created.json()["id"]

    added = client.post(f"/api/v1/me/collections/{collection_id}/recipes/{RECIPE_ID}")
    found = client.get(f"/api/v1/me/collections/{collection_id}")
    listing = client.get("/api/v1/me/collections")
    updated = client.patch(f"/api/v1/me/collections/{collection_id}", json={"nombre": "Cenas"})
    foreign = client.patch(f"/api/v1/me/collections/{MISSING_ID}", json={"nombre": "No permitido"})
    removed = client.delete(f"/api/v1/me/collections/{collection_id}/recipes/{RECIPE_ID}")
    deleted = client.delete(f"/api/v1/me/collections/{collection_id}")

    assert created.status_code == 201
    assert created.json()["nombre"] == "Cenas rápidas"
    assert added.status_code == removed.status_code == deleted.status_code == 204
    assert found.json()["recetas"][0]["titulo"] == "Sopa pública"
    assert listing.json()["colecciones"][0]["nombre"] == "Cenas rápidas"
    assert updated.json()["nombre"] == "Cenas"
    assert foreign.status_code == 404
    assert foreign.json()["error"]["code"] == "collection_not_found"


def test_collection_recipe_operations_report_missing_public_recipes(client: TestClient) -> None:
    created = client.post("/api/v1/me/collections", json={"nombre": "Cenas"})
    collection_id = created.json()["id"]

    response = client.post(f"/api/v1/me/collections/{collection_id}/recipes/{MISSING_ID}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "recipe_not_found"


def test_routes_return_401_when_current_user_dependency_rejects_the_request(client: TestClient) -> None:
    from comemos_en_casa.auth.api import current_user_dependency

    client.app.dependency_overrides[current_user_dependency] = lambda: (_ for _ in ()).throw(HTTPException(status_code=401))

    assert client.get("/api/v1/me/favorites").status_code == 401
