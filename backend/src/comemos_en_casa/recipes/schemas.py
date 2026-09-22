"""Validated recipe catalogue values, independent of persistence and HTTP."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import re
from unicodedata import category, normalize
from urllib.parse import urlsplit
from uuid import UUID, uuid4


TITLE_MIN_CODE_POINTS = 1
TITLE_MAX_CODE_POINTS = 200
IMAGE_URL_MAX_CHARACTERS = 2048
DETAIL_MIN_CODE_POINTS = 1
DETAIL_MAX_CODE_POINTS = 10_000
INGREDIENT_NAME_MAX_CODE_POINTS = 500
INGREDIENT_QUANTITY_MAX_CODE_POINTS = 100
LABEL_MAX_CODE_POINTS = 25
MAX_RECIPE_LABELS = 10
LOCAL_MEDIA_IMAGE_URL_RE = re.compile(r"^/media/recipes/[0-9a-f-]+\.(?:jpg|png|webp)$")

# The order is part of the label-colour allocation contract.
RECIPE_LABEL_PALETTE = (
    "#1D4ED8",
    "#047857",
    "#B45309",
    "#BE123C",
    "#7C3AED",
    "#0F766E",
    "#C2410C",
    "#4338CA",
)


class RecipeValidationError(ValueError):
    """Raised when a value cannot satisfy the recipe foundation contract."""


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise RecipeValidationError(f"{field} must be a string")
    return normalize("NFC", value)


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def _validate_length(value: str, *, minimum: int, maximum: int, field: str) -> str:
    if not minimum <= len(value) <= maximum:
        raise RecipeValidationError(f"{field} must contain {minimum} to {maximum} characters")
    return value


def normalize_title(value: str) -> str:
    """Return a NFC, trimmed, single-space title within the catalogue bounds."""
    title = _normalize_whitespace(_require_string(value, "title"))
    return _validate_length(title, minimum=TITLE_MIN_CODE_POINTS, maximum=TITLE_MAX_CODE_POINTS, field="title")


def normalize_image_url(value: str) -> str:
    """Accept a legacy remote image URL, a local media URL, or no image yet."""
    image_url = _require_string(value, "image URL").strip()
    if not image_url:
        return ""
    _validate_length(image_url, minimum=1, maximum=IMAGE_URL_MAX_CHARACTERS, field="image URL")
    if any(character.isspace() for character in image_url):
        raise RecipeValidationError("image URL must not contain whitespace")
    if LOCAL_MEDIA_IMAGE_URL_RE.fullmatch(image_url):
        return image_url

    try:
        parsed = urlsplit(image_url)
    except ValueError as error:
        raise RecipeValidationError("image URL must be an absolute HTTP(S) URL") from error
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.hostname:
        raise RecipeValidationError("image URL must be an absolute HTTP(S) URL")
    return image_url


def normalize_detail(value: str) -> str:
    """Return a NFC detail with LF line endings and no surrounding whitespace."""
    detail = _require_string(value, "detail").replace("\r\n", "\n").replace("\r", "\n").strip()
    return _validate_length(detail, minimum=DETAIL_MIN_CODE_POINTS, maximum=DETAIL_MAX_CODE_POINTS, field="detail")


def normalize_title_search(value: str) -> str:
    """Return the common case- and accent-insensitive title search key."""
    search_text = _normalize_whitespace(_require_string(value, "title search query"))
    decomposed = normalize("NFKD", search_text.casefold())
    without_marks = "".join(character for character in decomposed if not category(character).startswith("M"))
    return normalize("NFC", without_marks)


def normalize_label(value: str) -> str:
    """Normalize one label name, returning an empty string for blank input.

    Control characters are rejected before whitespace processing so that a newline
    or tab cannot be silently converted into a valid label separator.
    """
    label = _require_string(value, "label")
    if not label.strip():
        return ""
    if any(category(character) == "Cc" for character in label):
        raise RecipeValidationError("label must not contain control characters")
    label = _normalize_whitespace(label.lower())
    if not label:
        return ""
    return _validate_length(label, minimum=1, maximum=LABEL_MAX_CODE_POINTS, field="label")


def normalize_labels(values: Iterable[str]) -> tuple[str, ...]:
    """Normalize, deduplicate, and bound recipe labels in first-seen order."""
    if isinstance(values, (str, bytes)):
        raise RecipeValidationError("labels must be a list of strings")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        label = normalize_label(value)
        if label and label not in seen:
            seen.add(label)
            normalized.append(label)
            if len(normalized) == MAX_RECIPE_LABELS:
                break
    return tuple(normalized)


def _validated_id(value: UUID) -> UUID:
    if not isinstance(value, UUID):
        raise RecipeValidationError("id must be a UUID")
    return value


@dataclass(frozen=True)
class RecipeLabel:
    """A globally shared, normalized recipe label."""

    id: UUID
    name: str
    color: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validated_id(self.id))
        normalized_name = normalize_label(self.name)
        if not normalized_name:
            raise RecipeValidationError("label must not be empty")
        object.__setattr__(self, "name", normalized_name)
        if not isinstance(self.color, str) or not self.color:
            raise RecipeValidationError("label color must be a non-empty string")


@dataclass(frozen=True)
class Ingredient:
    """One ordered, normalized recipe ingredient."""

    name: str
    quantity: str | None = None

    def __post_init__(self) -> None:
        name = _normalize_whitespace(_require_string(self.name, "ingredient name"))
        object.__setattr__(self, "name", _validate_length(name, minimum=1, maximum=INGREDIENT_NAME_MAX_CODE_POINTS, field="ingredient name"))
        if self.quantity is not None:
            quantity = _normalize_whitespace(_require_string(self.quantity, "ingredient quantity"))
            object.__setattr__(self, "quantity", _validate_length(quantity, minimum=1, maximum=INGREDIENT_QUANTITY_MAX_CODE_POINTS, field="ingredient quantity"))


@dataclass(frozen=True)
class PreparationStep:
    """One ordered preparation instruction."""

    instruction: str

    def __post_init__(self) -> None:
        instruction = normalize_detail(self.instruction)
        object.__setattr__(self, "instruction", instruction)


@dataclass(frozen=True)
class Recipe:
    """A current public recipe foundation value ready for persistence or detail reads."""

    id: UUID
    title: str
    image_url: str
    detail: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validated_id(self.id))
        object.__setattr__(self, "title", normalize_title(self.title))
        object.__setattr__(self, "image_url", normalize_image_url(self.image_url))
        object.__setattr__(self, "detail", normalize_detail(self.detail))

    @classmethod
    def create(
        cls, *, title: str, image_url: str, detail: str, uuid_factory: Callable[[], UUID] = uuid4
    ) -> "Recipe":
        return cls.restore(id=_validated_id(uuid_factory()), title=title, image_url=image_url, detail=detail)

    @classmethod
    def restore(cls, *, id: UUID, title: str, image_url: str, detail: str) -> "Recipe":
        return cls(id=_validated_id(id), title=normalize_title(title), image_url=normalize_image_url(image_url), detail=normalize_detail(detail))

    @classmethod
    def update_foundation(cls, *, id: UUID, title: str, image_url: str, detail: str) -> "Recipe":
        """Build a replacement foundation value while preserving its supplied identity."""
        return cls.restore(id=id, title=title, image_url=image_url, detail=detail)


@dataclass(frozen=True)
class ManagedRecipe:
    """A publicly readable recipe with normalized content and global labels."""

    recipe: Recipe
    ingredients: tuple[Ingredient, ...]
    steps: tuple[PreparationStep, ...]
    labels: tuple[RecipeLabel, ...] = ()


@dataclass(frozen=True)
class RecipeListItem:
    """The public recipe fields returned by title search."""

    id: UUID
    title: str
    image_url: str
    labels: tuple[RecipeLabel, ...] = ()


@dataclass(frozen=True)
class ManagedRecipeListItem(RecipeListItem):
    """A public list row with its globally shared labels."""
