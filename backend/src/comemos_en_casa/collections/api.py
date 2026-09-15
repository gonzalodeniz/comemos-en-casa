"""Authenticated HTTP routes for private recipe favorites and collections."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI
from fastapi.responses import JSONResponse, Response
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from comemos_en_casa.auth.api import CurrentUser
from comemos_en_casa.auth.models import User
from comemos_en_casa.database import get_connection

from .repository import CollectionsRepository
from .schemas import Collection, CollectionValidationError, RecipeSummary


ME_API_PREFIX = "/api/v1/me"
RECIPES_API_PREFIX = "/api/v1/recipes"


class _ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class RecipeResponse(_ApiModel):
    id: UUID
    title: str = Field(serialization_alias="titulo")
    image_url: str = Field(serialization_alias="imagenUrl")
    status: str = Field(serialization_alias="estado")


class FavoritesResponse(_ApiModel):
    favorites: list[RecipeResponse] = Field(serialization_alias="favoritos")


class CollectionWriteRequest(_ApiModel):
    name: str = Field(validation_alias=AliasChoices("nombre", "name"), serialization_alias="nombre")


class CollectionResponse(_ApiModel):
    id: UUID
    name: str = Field(serialization_alias="nombre")
    recipes: list[RecipeResponse] = Field(serialization_alias="recetas")


class CollectionsResponse(_ApiModel):
    collections: list[CollectionResponse] = Field(serialization_alias="colecciones")


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
        content={"error": {"code": code, "message": message, "fieldErrors": {}}},
    )


def _recipe_response(recipe: RecipeSummary) -> RecipeResponse:
    return RecipeResponse(id=recipe.id, title=recipe.title, image_url=recipe.image_url, status=recipe.status)


def _collection_response(collection: Collection) -> CollectionResponse:
    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        recipes=[_recipe_response(recipe) for recipe in collection.recipes],
    )


def _collection_or_404(repository: CollectionsRepository, user: User, collection_id: UUID) -> Collection | JSONResponse:
    collection = repository.find_collection(user.id, collection_id)
    return collection if collection is not None else _error(404, "collection_not_found", "No se encontró la colección.")


def _recipe_or_404(repository: CollectionsRepository, recipe_id: UUID) -> JSONResponse | None:
    return None if repository.recipe_exists(recipe_id) else _error(404, "recipe_not_found", "No se encontró la receta.")


def register_routes(application: FastAPI) -> None:
    """Register routes which are private to the authenticated current user."""
    me_router = APIRouter(prefix=ME_API_PREFIX)
    recipes_router = APIRouter(prefix=RECIPES_API_PREFIX)

    @me_router.get("/favorites", response_model=FavoritesResponse)
    def list_favorites(user: CurrentUser, connection: Any = Depends(get_connection)) -> FavoritesResponse:
        favorites = CollectionsRepository(connection).list_favorites(user.id)
        return FavoritesResponse(favorites=[_recipe_response(recipe) for recipe in favorites])

    @recipes_router.put("/{recipe_id}/favorite", status_code=204, response_model=None)
    def add_favorite(recipe_id: UUID, user: CurrentUser, connection: Any = Depends(get_connection)) -> Response | JSONResponse:
        repository = CollectionsRepository(connection)
        if (error := _recipe_or_404(repository, recipe_id)) is not None:
            return error
        repository.add_favorite(user.id, recipe_id)
        return Response(status_code=204, headers={"Cache-Control": "no-store"})

    @recipes_router.delete("/{recipe_id}/favorite", status_code=204, response_model=None)
    def remove_favorite(recipe_id: UUID, user: CurrentUser, connection: Any = Depends(get_connection)) -> Response | JSONResponse:
        repository = CollectionsRepository(connection)
        if (error := _recipe_or_404(repository, recipe_id)) is not None:
            return error
        repository.remove_favorite(user.id, recipe_id)
        return Response(status_code=204, headers={"Cache-Control": "no-store"})

    @me_router.get("/collections", response_model=CollectionsResponse)
    def list_collections(user: CurrentUser, connection: Any = Depends(get_connection)) -> CollectionsResponse:
        collections = CollectionsRepository(connection).list_collections(user.id)
        return CollectionsResponse(collections=[_collection_response(collection) for collection in collections])

    @me_router.post("/collections", response_model=CollectionResponse, status_code=201)
    def create_collection(
        request: CollectionWriteRequest, user: CurrentUser, connection: Any = Depends(get_connection)
    ) -> CollectionResponse | JSONResponse:
        try:
            collection = Collection.create(request.name)
        except CollectionValidationError as error:
            return _error(422, "validation_failed", str(error))
        CollectionsRepository(connection).create_collection(user.id, collection)
        return _collection_response(collection)

    @me_router.get("/collections/{collection_id}", response_model=CollectionResponse)
    def get_collection(
        collection_id: UUID, user: CurrentUser, connection: Any = Depends(get_connection)
    ) -> CollectionResponse | JSONResponse:
        collection = _collection_or_404(CollectionsRepository(connection), user, collection_id)
        return collection if isinstance(collection, JSONResponse) else _collection_response(collection)

    @me_router.patch("/collections/{collection_id}", response_model=CollectionResponse)
    def update_collection(
        collection_id: UUID, request: CollectionWriteRequest, user: CurrentUser, connection: Any = Depends(get_connection)
    ) -> CollectionResponse | JSONResponse:
        try:
            collection = Collection(id=collection_id, name=request.name)
        except CollectionValidationError as error:
            return _error(422, "validation_failed", str(error))
        repository = CollectionsRepository(connection)
        if not repository.update_collection(user.id, collection):
            return _error(404, "collection_not_found", "No se encontró la colección.")
        updated = repository.find_collection(user.id, collection_id)
        assert updated is not None
        return _collection_response(updated)

    @me_router.delete("/collections/{collection_id}", status_code=204, response_model=None)
    def delete_collection(collection_id: UUID, user: CurrentUser, connection: Any = Depends(get_connection)) -> Response | JSONResponse:
        if not CollectionsRepository(connection).delete_collection(user.id, collection_id):
            return _error(404, "collection_not_found", "No se encontró la colección.")
        return Response(status_code=204, headers={"Cache-Control": "no-store"})

    @me_router.post("/collections/{collection_id}/recipes/{recipe_id}", status_code=204, response_model=None)
    def add_recipe_to_collection(
        collection_id: UUID, recipe_id: UUID, user: CurrentUser, connection: Any = Depends(get_connection)
    ) -> Response | JSONResponse:
        repository = CollectionsRepository(connection)
        if isinstance(_collection_or_404(repository, user, collection_id), JSONResponse):
            return _error(404, "collection_not_found", "No se encontró la colección.")
        if (error := _recipe_or_404(repository, recipe_id)) is not None:
            return error
        repository.add_recipe_to_collection(user.id, collection_id, recipe_id)
        return Response(status_code=204, headers={"Cache-Control": "no-store"})

    @me_router.delete("/collections/{collection_id}/recipes/{recipe_id}", status_code=204, response_model=None)
    def remove_recipe_from_collection(
        collection_id: UUID, recipe_id: UUID, user: CurrentUser, connection: Any = Depends(get_connection)
    ) -> Response | JSONResponse:
        repository = CollectionsRepository(connection)
        if isinstance(_collection_or_404(repository, user, collection_id), JSONResponse):
            return _error(404, "collection_not_found", "No se encontró la colección.")
        if (error := _recipe_or_404(repository, recipe_id)) is not None:
            return error
        repository.remove_recipe_from_collection(user.id, collection_id, recipe_id)
        return Response(status_code=204, headers={"Cache-Control": "no-store"})

    application.include_router(me_router)
    application.include_router(recipes_router)
