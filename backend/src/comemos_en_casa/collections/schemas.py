"""Validated private-collection values independent of HTTP and persistence."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from unicodedata import normalize
from uuid import UUID, uuid4


COLLECTION_NAME_MAX_CODE_POINTS = 200


class CollectionValidationError(ValueError):
    """Raised when a private collection value is outside its supported contract."""


def normalize_collection_name(value: str) -> str:
    """Normalize a collection name to the database's bounded, trimmed form."""
    if not isinstance(value, str):
        raise CollectionValidationError("collection name must be a string")
    name = normalize("NFC", " ".join(value.split()))
    if not 1 <= len(name) <= COLLECTION_NAME_MAX_CODE_POINTS:
        raise CollectionValidationError(f"collection name must contain 1 to {COLLECTION_NAME_MAX_CODE_POINTS} characters")
    return name


@dataclass(frozen=True)
class RecipeSummary:
    """The public recipe fields safely presented inside a private saved list."""

    id: UUID
    title: str
    image_url: str


@dataclass(frozen=True)
class Collection:
    """A user-owned collection and its current public recipe members."""

    id: UUID
    name: str
    recipes: tuple[RecipeSummary, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise CollectionValidationError("collection id must be a UUID")
        object.__setattr__(self, "name", normalize_collection_name(self.name))
        object.__setattr__(self, "recipes", tuple(self.recipes))

    @classmethod
    def create(cls, name: str, *, uuid_factory: Callable[[], UUID] = uuid4) -> "Collection":
        return cls(id=uuid_factory(), name=name)
