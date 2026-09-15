"""Public recipe reads and authenticated management routes."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, FastAPI, File, Query, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from comemos_en_casa.auth.api import CurrentUser
from comemos_en_casa.database import get_connection

from .management import RecipeManagementError, RecipeManagementService
from .repository import RecipeManagementRepository
from .schemas import Ingredient, ManagedRecipe, ManagedRecipeListItem, PreparationStep, Recipe, RecipeValidationError


API_PREFIX = "/api/v1/recipes"
MAX_IMAGE_BYTES = 10 * 1024 * 1024
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

    def components(self) -> tuple[list[Ingredient], list[PreparationStep]]:
        return [item.to_domain() for item in self.ingredients], [item.to_domain() for item in self.steps]


class IngredientResponse(_ApiModel):
    name: str = Field(serialization_alias="nombre")
    quantity: str | None = Field(default=None, serialization_alias="cantidad")


class StepResponse(_ApiModel):
    instruction: str = Field(serialization_alias="instruccion")


class RecipeListResponse(_ApiModel):
    id: UUID
    title: str = Field(serialization_alias="titulo")
    image_url: str = Field(serialization_alias="imagenUrl")
    status: str = Field(serialization_alias="estado")


class RecipeDetailResponse(RecipeListResponse):
    detail: str = Field(serialization_alias="detalle")
    ingredients: list[IngredientResponse] = Field(serialization_alias="ingredientes")
    steps: list[StepResponse] = Field(serialization_alias="pasos")


class RecipeSearchResponse(_ApiModel):
    recipes: list[RecipeListResponse] = Field(serialization_alias="recetas")


def _error(status_code: int, code: str, message: str, *, fields: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
        content={"error": {"code": code, "message": message, "fieldErrors": fields or {}}},
    )


def _validation(error: Exception, field: str | None = None) -> JSONResponse:
    return _error(422, "validation_failed", str(error), fields={field: str(error)} if field else None)


def _detail_response(recipe: ManagedRecipe) -> RecipeDetailResponse:
    return RecipeDetailResponse(
        id=recipe.recipe.id,
        title=recipe.recipe.title,
        image_url=recipe.recipe.image_url,
        status=recipe.status,
        detail=recipe.recipe.detail,
        ingredients=[IngredientResponse(name=item.name, quantity=item.quantity) for item in recipe.ingredients],
        steps=[StepResponse(instruction=item.instruction) for item in recipe.steps],
    )


def _list_response(recipe: ManagedRecipeListItem) -> RecipeListResponse:
    return RecipeListResponse(id=recipe.id, title=recipe.title, image_url=recipe.image_url, status=recipe.status)


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


def register_routes(application: FastAPI) -> None:
    """Register public reads and session-protected recipe mutations."""
    router = APIRouter(prefix=API_PREFIX)

    @router.get("", response_model=RecipeSearchResponse)
    def list_recipes(
        q: str = "", limit: Annotated[int, Query(ge=1, le=50)] = 50, connection: Any = Depends(get_connection)
    ) -> RecipeSearchResponse | JSONResponse:
        try:
            recipes = RecipeManagementRepository(connection).search_management_by_title(q, limit)
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
        request: RecipeWriteRequest, _: CurrentUser, connection: Any = Depends(get_connection)
    ) -> RecipeDetailResponse | JSONResponse:
        try:
            ingredients, steps = request.components()
            return _detail_response(
                RecipeManagementService(RecipeManagementRepository(connection)).create(
                    title=request.title, detail=request.detail, ingredients=ingredients, steps=steps
                )
            )
        except (RecipeValidationError, RecipeManagementError) as error:
            return _validation(error)

    def _update_recipe(recipe_id: UUID, request: RecipeWriteRequest, connection: Any) -> RecipeDetailResponse | JSONResponse:
        repository = RecipeManagementRepository(connection)
        existing = repository.find_management_by_id(recipe_id)
        if existing is None:
            return _error(404, "recipe_not_found", "No se encontró la receta.")
        try:
            ingredients, steps = request.components()
            replacement = Recipe.update_foundation(
                id=recipe_id, title=request.title, image_url=existing.recipe.image_url, detail=request.detail
            )
        except RecipeValidationError as error:
            return _validation(error)
        repository.update_management(replacement, ingredients, steps)
        updated = repository.find_management_by_id(recipe_id)
        assert updated is not None
        return _detail_response(updated)

    @router.put("/{recipe_id}", response_model=RecipeDetailResponse)
    def replace_recipe(
        recipe_id: UUID, request: RecipeWriteRequest, _: CurrentUser, connection: Any = Depends(get_connection)
    ) -> RecipeDetailResponse | JSONResponse:
        return _update_recipe(recipe_id, request, connection)

    @router.patch("/{recipe_id}", response_model=RecipeDetailResponse)
    def update_recipe(
        recipe_id: UUID, request: RecipeWriteRequest, _: CurrentUser, connection: Any = Depends(get_connection)
    ) -> RecipeDetailResponse | JSONResponse:
        return _update_recipe(recipe_id, request, connection)

    @router.post("/{recipe_id}/publish", response_model=RecipeDetailResponse)
    def publish_recipe(recipe_id: UUID, _: CurrentUser, connection: Any = Depends(get_connection)) -> RecipeDetailResponse | JSONResponse:
        repository = RecipeManagementRepository(connection)
        if not repository.set_status(recipe_id, "published"):
            return _error(404, "recipe_not_found", "No se encontró la receta.")
        recipe = repository.find_management_by_id(recipe_id)
        assert recipe is not None
        return _detail_response(recipe)

    @router.post("/{recipe_id}/draft", response_model=RecipeDetailResponse)
    def draft_recipe(recipe_id: UUID, _: CurrentUser, connection: Any = Depends(get_connection)) -> RecipeDetailResponse | JSONResponse:
        repository = RecipeManagementRepository(connection)
        if not repository.set_status(recipe_id, "draft"):
            return _error(404, "recipe_not_found", "No se encontró la receta.")
        recipe = repository.find_management_by_id(recipe_id)
        assert recipe is not None
        return _detail_response(recipe)

    @router.post("/{recipe_id}/image", response_model=RecipeDetailResponse)
    async def upload_image(
        recipe_id: UUID,
        _: CurrentUser,
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

    @router.delete("/{recipe_id}", status_code=204)
    def delete_recipe(recipe_id: UUID, _: CurrentUser, connection: Any = Depends(get_connection)) -> Response:
        RecipeManagementRepository(connection).delete(recipe_id)
        return Response(status_code=204, headers={"Cache-Control": "no-store"})

    application.include_router(router)
