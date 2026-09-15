"""Validated recipe catalogue values, independent of persistence and HTTP."""

from collections.abc import Callable
from dataclasses import dataclass
from unicodedata import category, normalize
from urllib.parse import urlsplit
from uuid import UUID, uuid4


TITLE_MIN_CODE_POINTS = 1
TITLE_MAX_CODE_POINTS = 200
IMAGE_URL_MIN_CHARACTERS = 1
IMAGE_URL_MAX_CHARACTERS = 2048
DETAIL_MIN_CODE_POINTS = 1
DETAIL_MAX_CODE_POINTS = 10_000


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
    return _validate_length(
        title,
        minimum=TITLE_MIN_CODE_POINTS,
        maximum=TITLE_MAX_CODE_POINTS,
        field="title",
    )


def normalize_image_url(value: str) -> str:
    """Return a trimmed absolute HTTP(S) URL without internal whitespace."""
    image_url = _require_string(value, "image URL").strip()
    _validate_length(
        image_url,
        minimum=IMAGE_URL_MIN_CHARACTERS,
        maximum=IMAGE_URL_MAX_CHARACTERS,
        field="image URL",
    )
    if any(character.isspace() for character in image_url):
        raise RecipeValidationError("image URL must not contain whitespace")

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
    return _validate_length(
        detail,
        minimum=DETAIL_MIN_CODE_POINTS,
        maximum=DETAIL_MAX_CODE_POINTS,
        field="detail",
    )


def normalize_title_search(value: str) -> str:
    """Return the common case- and accent-insensitive title search key."""
    search_text = _normalize_whitespace(_require_string(value, "title search query"))
    decomposed = normalize("NFKD", search_text.casefold())
    without_marks = "".join(character for character in decomposed if not category(character).startswith("M"))
    return normalize("NFC", without_marks)


def _validated_id(value: UUID) -> UUID:
    if not isinstance(value, UUID):
        raise RecipeValidationError("id must be a UUID")
    return value


@dataclass(frozen=True)
class Recipe:
    """A current public recipe foundation value ready for persistence or detail reads."""

    id: UUID
    title: str
    image_url: str
    detail: str

    def __post_init__(self) -> None:
        """Normalize and validate every public construction path."""
        object.__setattr__(self, "id", _validated_id(self.id))
        object.__setattr__(self, "title", normalize_title(self.title))
        object.__setattr__(self, "image_url", normalize_image_url(self.image_url))
        object.__setattr__(self, "detail", normalize_detail(self.detail))

    @classmethod
    def create(
        cls,
        *,
        title: str,
        image_url: str,
        detail: str,
        uuid_factory: Callable[[], UUID] = uuid4,
    ) -> "Recipe":
        return cls.restore(
            id=_validated_id(uuid_factory()),
            title=title,
            image_url=image_url,
            detail=detail,
        )

    @classmethod
    def restore(cls, *, id: UUID, title: str, image_url: str, detail: str) -> "Recipe":
        return cls(
            id=_validated_id(id),
            title=normalize_title(title),
            image_url=normalize_image_url(image_url),
            detail=normalize_detail(detail),
        )

    @classmethod
    def update_foundation(
        cls,
        *,
        id: UUID,
        title: str,
        image_url: str,
        detail: str,
    ) -> "Recipe":
        """Build a replacement foundation value while preserving its supplied identity."""
        return cls.restore(id=id, title=title, image_url=image_url, detail=detail)


@dataclass(frozen=True)
class RecipeListItem:
    """The public recipe fields returned by title search."""

    id: UUID
    title: str
    image_url: str
