"""FastAPI request/response translation for the shared meal calendar."""

from __future__ import annotations

from datetime import date, datetime, timezone
from ipaddress import ip_address
from typing import Annotated, Any, Literal
from uuid import UUID

import psycopg
from fastapi import APIRouter, Body, Depends, FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from comemos_en_casa.database import TransientDatabaseError, get_connection
from comemos_en_casa.recipes.schemas import Recipe

from .catalog_adapter import CatalogueCursorError, MealCalendarCatalogueAdapter
from .rate_limit import RateLimitExceeded, consume_rate_limit
from .repository import CalendarAssignment, MealCalendarRepository
from .schemas import AssignmentDraft, MealCalendarValidationError
from .service import current_week_start, validate_week_start, week_dates
from .settings import CANARY_TIMEZONE_NAME

API_PREFIX = "/api/v1/meal-calendar"


class AuthenticationRequired(Exception):
    """Raised when guest access is disabled before authentication is available."""


class _ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class RecipeSummaryResponse(_ApiModel):
    id: UUID
    title: str
    cover_image_url: str = Field(serialization_alias="coverImageUrl")


class RecipeDetailResponse(RecipeSummaryResponse):
    detail: str


class RecipeReferenceResponse(_ApiModel):
    id: UUID | None
    available: bool
    title: str
    cover_image_url: str | None = Field(serialization_alias="coverImageUrl")


class AssignmentResponse(_ApiModel):
    id: UUID
    date: date
    slot: Literal["lunch", "dinner"]
    kind: Literal["recipe", "free_text"]
    recipe: RecipeReferenceResponse | None = None
    text: str | None = None


class ContextResponse(_ApiModel):
    timezone: str
    current_week_start: date = Field(serialization_alias="currentWeekStart")
    guest_mode: bool = Field(serialization_alias="guestMode")


class WeekResponse(_ApiModel):
    week_start: date = Field(serialization_alias="weekStart")
    week_end: date = Field(serialization_alias="weekEnd")
    timezone: str
    assignments: list[AssignmentResponse]


class RecipeSearchResponse(_ApiModel):
    recipes: list[RecipeSummaryResponse]
    next_cursor: str | None = Field(serialization_alias="nextCursor")


class AssignmentWriteRequest(_ApiModel):
    id: UUID | None = None
    meal_date: date = Field(validation_alias=AliasChoices("date", "mealDate"))
    slot: Literal["lunch", "dinner"]
    kind: Literal["recipe", "free_text"]
    recipe_id: UUID | None = Field(default=None, validation_alias=AliasChoices("recipeId", "recipe_id"))
    free_text: str | None = Field(default=None, validation_alias=AliasChoices("text", "freeText", "free_text"))

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    def to_draft(self) -> AssignmentDraft:
        return AssignmentDraft.create(
            meal_date=self.meal_date,
            slot=self.slot,
            kind=self.kind,
            recipe_id=self.recipe_id,
            free_text=self.free_text,
        )


def _error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    field_errors: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    retryable: bool = False,
) -> JSONResponse:
    response_headers = {"Cache-Control": "no-store"}
    if headers is not None:
        response_headers.update(headers)
    return JSONResponse(
        status_code=status_code,
        headers=response_headers,
        content={
            "error": {
                "code": code,
                "message": message,
                "retryable": retryable,
                "fieldErrors": field_errors or {},
            }
        },
    )


def _validation_response(error: Exception, *, field: str | None = None) -> JSONResponse:
    field_errors = {field: str(error)} if field else {}
    return _error_response(422, "validation_failed", str(error), field_errors=field_errors)


def _assignment_response(assignment: CalendarAssignment) -> AssignmentResponse:
    if assignment.kind == "free_text":
        return AssignmentResponse(
            id=assignment.id,
            date=assignment.meal_date,
            slot=assignment.slot,
            kind="free_text",
            text=assignment.free_text,
        )

    available = assignment.recipe_id is not None and assignment.recipe_title is not None
    return AssignmentResponse(
        id=assignment.id,
        date=assignment.meal_date,
        slot=assignment.slot,
        kind="recipe",
        recipe=RecipeReferenceResponse(
            id=assignment.recipe_id if available else None,
            available=available,
            title=assignment.recipe_title if available else "Receta no disponible",
            cover_image_url=assignment.recipe_image_url if available else None,
        ),
    )


def _recipe_summary(recipe: Any) -> RecipeSummaryResponse:
    return RecipeSummaryResponse(id=recipe.id, title=recipe.title, cover_image_url=recipe.image_url)


def _recipe_detail(recipe: Recipe) -> RecipeDetailResponse:
    return RecipeDetailResponse(
        id=recipe.id,
        title=recipe.title,
        cover_image_url=recipe.image_url,
        detail=recipe.detail,
    )


def _set_no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


def _client_ip(request: Request) -> str:
    """Return a database-safe client address without trusting forwarded headers."""
    host = request.client.host if request.client is not None else "0.0.0.0"
    try:
        return str(ip_address(host))
    except ValueError:
        return "0.0.0.0"


def register_routes(application: FastAPI) -> None:
    """Register the bounded calendar API on an already-configured FastAPI app."""
    guest_mode_enabled = application.state.settings.enable_guest_user

    @application.exception_handler(RequestValidationError)
    async def request_validation_error(_: Any, error: RequestValidationError) -> JSONResponse:
        field_errors = {
            ".".join(str(part) for part in detail["loc"] if part != "body"): detail["msg"]
            for detail in error.errors()
        }
        return _error_response(422, "validation_failed", "Request validation failed", field_errors=field_errors)

    @application.exception_handler(AuthenticationRequired)
    async def authentication_required(_: Any, __: AuthenticationRequired) -> JSONResponse:
        return _error_response(
            401,
            "authentication_required",
            "Authentication is required to access the shared calendar.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @application.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded(_: Any, error: RateLimitExceeded) -> JSONResponse:
        result = error.result
        return _error_response(
            429,
            "rate_limit_exceeded",
            "Too many calendar requests. Try again after the current minute window.",
            retryable=True,
            headers={
                "Retry-After": str(result.retry_after),
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": "0",
            },
        )

    @application.exception_handler(TransientDatabaseError)
    @application.exception_handler(psycopg.InterfaceError)
    @application.exception_handler(psycopg.OperationalError)
    @application.exception_handler(psycopg.errors.DeadlockDetected)
    @application.exception_handler(psycopg.errors.SerializationFailure)
    async def transient_database_error(_: Any, __: Exception) -> JSONResponse:
        return _error_response(
            503,
            "database_unavailable",
            "Calendar data is temporarily unavailable. Please retry.",
            retryable=True,
            headers={"Retry-After": "1"},
        )

    def require_calendar_access() -> None:
        # Authentication is not integrated yet; disabling the selected guest mode
        # therefore has one explicit, stable outcome instead of exposing data.
        if not guest_mode_enabled:
            raise AuthenticationRequired()

    def enforce_read_rate_limit(request: Request, connection: Any = Depends(get_connection)) -> None:
        result = consume_rate_limit(connection, client_ip=_client_ip(request), operation_class="read")
        if not result.allowed:
            raise RateLimitExceeded(result)

    def enforce_write_rate_limit(request: Request, connection: Any = Depends(get_connection)) -> None:
        result = consume_rate_limit(connection, client_ip=_client_ip(request), operation_class="write")
        if not result.allowed:
            raise RateLimitExceeded(result)

    read_dependencies = [Depends(_set_no_store), Depends(require_calendar_access), Depends(enforce_read_rate_limit)]
    write_dependencies = [Depends(_set_no_store), Depends(require_calendar_access), Depends(enforce_write_rate_limit)]
    router = APIRouter(prefix=API_PREFIX)

    @router.get("/context", response_model=ContextResponse, dependencies=read_dependencies)
    def get_context() -> ContextResponse:
        return ContextResponse(
            timezone=CANARY_TIMEZONE_NAME,
            current_week_start=current_week_start(datetime.now(timezone.utc)),
            guest_mode=guest_mode_enabled,
        )

    @router.get(
        "/weeks/{week_start}",
        response_model=WeekResponse,
        response_model_exclude_none=True,
        dependencies=read_dependencies,
    )
    def get_week(week_start: str, connection: Any = Depends(get_connection)) -> WeekResponse | JSONResponse:
        try:
            parsed_week_start = validate_week_start(date.fromisoformat(week_start))
        except (MealCalendarValidationError, ValueError) as error:
            return _error_response(422, "invalid_week_start", str(error), field_errors={"weekStart": str(error)})

        dates = week_dates(parsed_week_start)
        assignments = MealCalendarRepository(connection).list_week(dates[0], dates[-1])
        return WeekResponse(
            week_start=dates[0],
            week_end=dates[-1],
            timezone=CANARY_TIMEZONE_NAME,
            assignments=[_assignment_response(assignment) for assignment in assignments],
        )

    @router.get("/recipes", response_model=RecipeSearchResponse, dependencies=read_dependencies)
    def search_recipes(
        q: str = "",
        cursor: str | None = None,
        limit: Annotated[int, Query(ge=1, le=50)] = 50,
        connection: Any = Depends(get_connection),
    ) -> RecipeSearchResponse | JSONResponse:
        try:
            page = MealCalendarCatalogueAdapter(connection).search_public_recipes(q, limit=limit, cursor=cursor)
        except (CatalogueCursorError, ValueError) as error:
            return _validation_response(error, field="cursor" if cursor is not None else "q")
        return RecipeSearchResponse(recipes=[_recipe_summary(recipe) for recipe in page.recipes], next_cursor=page.next_cursor)

    @router.get("/recipes/{recipe_id}", response_model=RecipeDetailResponse, dependencies=read_dependencies)
    def get_recipe(recipe_id: UUID, connection: Any = Depends(get_connection)) -> RecipeDetailResponse | JSONResponse:
        recipe = MealCalendarCatalogueAdapter(connection).find_public_recipe(recipe_id)
        if recipe is None:
            return _error_response(404, "recipe_not_found", "Recipe was not found")
        return _recipe_detail(recipe)

    @router.post(
        "/assignments",
        response_model=AssignmentResponse,
        response_model_exclude_none=True,
        status_code=201,
        dependencies=write_dependencies,
    )
    def create_assignment(
        request: Annotated[AssignmentWriteRequest, Body()],
        connection: Any = Depends(get_connection),
    ) -> AssignmentResponse | JSONResponse:
        if request.id is None:
            return _validation_response(ValueError("id is required"), field="id")
        try:
            draft = request.to_draft()
        except MealCalendarValidationError as error:
            return _validation_response(error)

        repository = MealCalendarRepository(connection)
        existing = repository.find_by_id(request.id)
        if existing is not None:
            if existing.matches(draft):
                return JSONResponse(status_code=200, headers={"Cache-Control": "no-store"}, content=_assignment_response(existing).model_dump(mode="json", by_alias=True, exclude_none=True))
            return _error_response(409, "idempotency_conflict", "Assignment id is already used with a different payload")
        if draft.recipe_id is not None and MealCalendarCatalogueAdapter(connection).find_public_recipe(draft.recipe_id) is None:
            return _error_response(404, "recipe_not_found", "Recipe was not found")

        if not repository.insert(request.id, draft):
            existing = repository.find_by_id(request.id)
            if existing is not None and existing.matches(draft):
                return JSONResponse(status_code=200, headers={"Cache-Control": "no-store"}, content=_assignment_response(existing).model_dump(mode="json", by_alias=True, exclude_none=True))
            return _error_response(409, "idempotency_conflict", "Assignment id is already used with a different payload")
        created = repository.find_by_id(request.id)
        assert created is not None
        return _assignment_response(created)

    @router.patch(
        "/assignments/{assignment_id}",
        response_model=AssignmentResponse,
        response_model_exclude_none=True,
        dependencies=write_dependencies,
    )
    def update_assignment(
        assignment_id: UUID,
        request: AssignmentWriteRequest,
        connection: Any = Depends(get_connection),
    ) -> AssignmentResponse | JSONResponse:
        try:
            draft = request.to_draft()
        except MealCalendarValidationError as error:
            return _validation_response(error)

        repository = MealCalendarRepository(connection)
        existing = repository.find_by_id(assignment_id)
        if existing is None:
            return _error_response(404, "assignment_not_found", "Assignment was not found")
        if existing.kind != draft.kind:
            return _validation_response(ValueError("kind cannot be changed"), field="kind")
        if draft.recipe_id is not None and MealCalendarCatalogueAdapter(connection).find_public_recipe(draft.recipe_id) is None:
            return _error_response(404, "recipe_not_found", "Recipe was not found")
        if not repository.update(assignment_id, draft):
            return _error_response(404, "assignment_not_found", "Assignment was not found")
        updated = repository.find_by_id(assignment_id)
        assert updated is not None
        return _assignment_response(updated)

    @router.delete("/assignments/{assignment_id}", status_code=204, dependencies=write_dependencies)
    def delete_assignment(assignment_id: UUID, connection: Any = Depends(get_connection)) -> Response:
        MealCalendarRepository(connection).delete(assignment_id)
        return Response(status_code=204, headers={"Cache-Control": "no-store"})

    # FastAPI 0.141 retains included routers as an internal wrapper without a
    # ``path`` attribute. Re-register concrete operations on the application so
    # route discovery and application-level dependency overrides both work.
    for route in router.routes:
        application.add_api_route(
            route.path,
            route.endpoint,
            response_model=route.response_model,
            status_code=route.status_code,
            tags=route.tags,
            dependencies=route.dependencies,
            summary=route.summary,
            description=route.description,
            response_description=route.response_description,
            responses=route.responses,
            deprecated=route.deprecated,
            methods=route.methods,
            operation_id=route.operation_id,
            response_model_include=route.response_model_include,
            response_model_exclude=route.response_model_exclude,
            response_model_by_alias=route.response_model_by_alias,
            response_model_exclude_unset=route.response_model_exclude_unset,
            response_model_exclude_defaults=route.response_model_exclude_defaults,
            response_model_exclude_none=route.response_model_exclude_none,
            include_in_schema=route.include_in_schema,
            response_class=route.response_class,
            name=route.name,
            openapi_extra=route.openapi_extra,
            generate_unique_id_function=route.generate_unique_id_function,
        )
