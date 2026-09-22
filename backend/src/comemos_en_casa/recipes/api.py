"""Public recipe reads, writes, images, and global label suggestions."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, FastAPI, File, Query, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from comemos_en_casa.database import get_connection

from .management import RecipeManagementError, RecipeManagementService
from .repository import RecipeManagementRepository
from .schemas import (
    Ingredient,
    ManagedRecipe,
    ManagedRecipeListItem,
    PreparationStep,
    RecipeLabel,
    RecipeValidationError,
    normalize_labels,
)


API_PREFIX = "/api/v1/recipes"
LABELS_API_PREFIX = "/api/v1/labels"
MAX_IMAGE_BYTES = 10 * 1024 * 1024
LABEL_SUGGESTION_LIMIT = 50
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": ("jpg", "image/jpeg"),
    b"\x89PNG\r\n\x1a\n": ("png", "image/png"),
}


class _ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class IngredientRequest(_ApiModel):
    name: str = Field(validation_alias=AliasChoices("nombre", "name"), serialization_alias="nombre")
    quantity: str | None = Field(default=None, validation_alias=AliasChoices("cantidad", "quantity"), serialization_alias="cantidad")

    def to_domain(self) -> Ingredient:
        return Ingredient(name=self.name, quantity=self.quantity)


class StepRequest(_ApiModel):
    instruction: str = Field(
        validation_alias=AliasChoices("instruccion", "instrucción", "instruction"), serialization_alias="instruccion"
    )

    def to_domain(self) -> PreparationStep:
        return PreparationStep(instruction=self.instruction)


class RecipeWriteRequest(_ApiModel):
    title: str = Field(validation_alias=AliasChoices("titulo", "título", "title"), serialization_alias="titulo")
    detail: str = Field(validation_alias=AliasChoices("detalle", "detail"), serialization_alias="detalle")
    ingredients: list[IngredientRequest] = Field(
        default_factory=list, validation_alias=AliasChoices("ingredientes", "ingredients"), serialization_alias="ingredientes"
    )
    steps: list[StepRequest] = Field(
        default_factory=list, validation_alias=AliasChoices("pasos", "steps"), serialization_alias="pasos"
    )
    labels: list[str] = Field(default_factory=list)

    def components(self) -> tuple[list[Ingredient], list[PreparationStep]]:
        return [item.to_domain() for item in self.ingredients], [item.to_domain() for item in self.steps]


class IngredientResponse(_ApiModel):
    name: str = Field(serialization_alias="nombre")
    quantity: str | None = Field(default=None, serialization_alias="cantidad")


class StepResponse(_ApiModel):
    instruction: str = Field(serialization_alias="instruccion")


class RecipeLabelResponse(_ApiModel):
    id: UUID
    name: str
    color: str


class RecipeListResponse(_ApiModel):
    id: UUID
    title: str = Field(serialization_alias="titulo")
    image_url: str = Field(serialization_alias="imagenUrl")
    labels: list[RecipeLabelResponse]


class RecipeDetailResponse(RecipeListResponse):
    detail: str = Field(serialization_alias="detalle")
    ingredients: list[IngredientResponse] = Field(serialization_alias="ingredientes")
    steps: list[StepResponse] = Field(serialization_alias="pasos")


class RecipeSearchResponse(_ApiModel):
    recipes: list[RecipeListResponse] = Field(serialization_alias="recetas")


class LabelSearchResponse(_ApiModel):
    labels: list[RecipeLabelResponse]


def _error(status_code: int, code: str, message: str, *, fields: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
        content={"error": {"code": code, "message": message, "fieldErrors": fields or {}}},
    )


def _validation(error: Exception, field: str | None = None) -> JSONResponse:
    return _error(422, "validation_failed", str(error), fields={field: str(error)} if field else None)


def _label_response(label: RecipeLabel) -> RecipeLabelResponse:
    return RecipeLabelResponse(id=label.id, name=label.name, color=label.color)


def _detail_response(recipe: ManagedRecipe) -> RecipeDetailResponse:
    return RecipeDetailResponse(
        id=recipe.recipe.id,
        title=recipe.recipe.title,
        image_url=recipe.recipe.image_url,
        detail=recipe.recipe.detail,
        ingredients=[IngredientResponse(name=item.name, quantity=item.quantity) for item in recipe.ingredients],
        steps=[StepResponse(instruction=item.instruction) for item in recipe.steps],
        labels=[_label_response(label) for label in recipe.labels],
    )


def _list_response(recipe: ManagedRecipeListItem) -> RecipeListResponse:
    return RecipeListResponse(
        id=recipe.id,
        title=recipe.title,
        image_url=recipe.image_url,
        labels=[_label_response(label) for label in recipe.labels],
    )


def _image_kind(data: bytes) -> tuple[str, str] | None:
    for signature, kind in IMAGE_SIGNATURES.items():
        if data.startswith(signature):
            return kind
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ("webp", "image/webp")
    return None


async def _read_image(upload: UploadFile) -> tuple[bytes, str]:
    data = await upload.read(MAX_IMAGE_BYTES + 1)
    if not data:
        raise RecipeManagementError("La imagen no puede estar vacía.")
    if len(data) > MAX_IMAGE_BYTES:
        raise RecipeManagementError("La imagen no puede superar 10 MB.")
    kind = _image_kind(data)
    if kind is None:
        raise RecipeManagementError("La imagen debe ser JPEG, PNG o WebP.")
    return data, kind[0]


def _normalized_query_labels(values: list[str]) -> tuple[str, ...]:
    return normalize_labels(values)


def register_routes(application: FastAPI) -> None:
    """Register the public recipe and label API."""
    router = APIRouter(prefix=API_PREFIX)
    labels_router = APIRouter(prefix=LABELS_API_PREFIX)

    @router.get("", response_model=RecipeSearchResponse)
    def list_recipes(
        q: str = "",
        limit: Annotated[int, Query(ge=1, le=50)] = 50,
        label: Annotated[list[str] | None, Query()] = None,
        connection: Any = Depends(get_connection),
    ) -> RecipeSearchResponse | JSONResponse:
        try:
            effective_labels = _normalized_query_labels(label or [])
            repository = RecipeManagementRepository(connection)
            if effective_labels:
                recipes = repository.search_management_by_title(q, limit, labels=effective_labels)
            else:
                recipes = repository.search_management_by_title(q, limit)
        except RecipeValidationError as error:
            return _validation(error, "busqueda")
        return RecipeSearchResponse(recipes=[_list_response(recipe) for recipe in recipes])

    @router.get("/{recipe_id}", response_model=RecipeDetailResponse)
    def get_recipe(recipe_id: UUID, connection: Any = Depends(get_connection)) -> RecipeDetailResponse | JSONResponse:
        recipe = RecipeManagementRepository(connection).find_management_by_id(recipe_id)
        if recipe is None:
            return _error(404, "recipe_not_found", "No se encontró la receta.")
        return _detail_response(recipe)

    @router.post("", response_model=RecipeDetailResponse, status_code=201)
    def create_recipe(
        request: RecipeWriteRequest, connection: Any = Depends(get_connection)
    ) -> RecipeDetailResponse | JSONResponse:
        try:
            ingredients, steps = request.components()
            created = RecipeManagementService(RecipeManagementRepository(connection)).create(
                title=request.title,
                detail=request.detail,
                ingredients=ingredients,
                steps=steps,
                labels=request.labels,
            )
            return _detail_response(created)
        except (RecipeValidationError, RecipeManagementError) as error:
            return _validation(error)

    def _update_recipe(recipe_id: UUID, request: RecipeWriteRequest, connection: Any) -> RecipeDetailResponse | JSONResponse:
        repository = RecipeManagementRepository(connection)
        existing = repository.find_management_by_id(recipe_id)
        if existing is None:
            return _error(404, "recipe_not_found", "No se encontró la receta.")
        try:
            ingredients, steps = request.components()
            replacement = existing.recipe.update_foundation(
                id=recipe_id, title=request.title, image_url=existing.recipe.image_url, detail=request.detail
            )
            if not repository.update_management(replacement, ingredients, steps, labels=request.labels):
                return _error(404, "recipe_not_found", "No se encontró la receta.")
        except RecipeValidationError as error:
            return _validation(error)
        updated = repository.find_management_by_id(recipe_id)
        assert updated is not None
        return _detail_response(updated)

    @router.put("/{recipe_id}", response_model=RecipeDetailResponse)
    def replace_recipe(
        recipe_id: UUID, request: RecipeWriteRequest, connection: Any = Depends(get_connection)
    ) -> RecipeDetailResponse | JSONResponse:
        return _update_recipe(recipe_id, request, connection)

    @router.patch("/{recipe_id}", response_model=RecipeDetailResponse)
    def update_recipe(
        recipe_id: UUID, request: RecipeWriteRequest, connection: Any = Depends(get_connection)
    ) -> RecipeDetailResponse | JSONResponse:
        return _update_recipe(recipe_id, request, connection)

    @router.post("/{recipe_id}/publish", include_in_schema=False)
    def retired_publish_route(recipe_id: str) -> JSONResponse:
        return _error(404, "not_found", "La ruta no está disponible.")

    @router.post("/{recipe_id}/draft", include_in_schema=False)
    def retired_draft_route(recipe_id: str) -> JSONResponse:
        return _error(404, "not_found", "La ruta no está disponible.")

    @router.post("/{retired_action}", include_in_schema=False)
    def retired_recipe_route(retired_action: str) -> JSONResponse:
        return _error(404, "not_found", "La ruta no está disponible.")

    @router.post("/{recipe_id}/image", response_model=RecipeDetailResponse)
    async def upload_image(
        recipe_id: UUID,
        file: UploadFile = File(...),
        connection: Any = Depends(get_connection),
    ) -> RecipeDetailResponse | JSONResponse:
        repository = RecipeManagementRepository(connection)
        if repository.find_management_by_id(recipe_id) is None:
            return _error(404, "recipe_not_found", "No se encontró la receta.")
        try:
            data, extension = await _read_image(file)
        except RecipeManagementError as error:
            return _validation(error, "imagen")
        media_root = Path(application.state.settings.media_root)
        destination = media_root / "recipes" / f"{uuid4()}.{extension}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        if not repository.set_image_url(recipe_id, f"/media/recipes/{destination.name}"):
            return _error(404, "recipe_not_found", "No se encontró la receta.")
        recipe = repository.find_management_by_id(recipe_id)
        assert recipe is not None
        return _detail_response(recipe)

    @router.delete("/{recipe_id}/image", response_model=RecipeDetailResponse)
    def remove_image(recipe_id: UUID, connection: Any = Depends(get_connection)) -> RecipeDetailResponse | JSONResponse:
        repository = RecipeManagementRepository(connection)
        if not repository.delete_image(recipe_id):
            return _error(404, "recipe_not_found", "No se encontró la receta.")
        recipe = repository.find_management_by_id(recipe_id)
        assert recipe is not None
        return _detail_response(recipe)

    @router.delete("/{recipe_id}", status_code=204)
    def delete_recipe(recipe_id: UUID, connection: Any = Depends(get_connection)) -> Response:
        RecipeManagementRepository(connection).delete(recipe_id)
        return Response(status_code=204, headers={"Cache-Control": "no-store"})

    @labels_router.get("", response_model=LabelSearchResponse)
    def list_labels(
        q: str = "", limit: Annotated[int, Query(ge=1, le=LABEL_SUGGESTION_LIMIT)] = LABEL_SUGGESTION_LIMIT,
        connection: Any = Depends(get_connection),
    ) -> LabelSearchResponse | JSONResponse:
        try:
            suggestions = RecipeManagementRepository(connection).search_labels(q, limit)
        except RecipeValidationError as error:
            return _validation(error, "q")
        return LabelSearchResponse(labels=[_label_response(label) for label in suggestions])

    application.include_router(router)
    application.include_router(labels_router)
