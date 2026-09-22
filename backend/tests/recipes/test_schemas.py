from __future__ import annotations

from pathlib import Path
import sys
from uuid import UUID

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from comemos_en_casa.recipes import schemas
from comemos_en_casa.recipes.schemas import (
    Recipe,
    RecipeValidationError,
    normalize_title_search,
)


RECIPE_ID = UUID("12345678-1234-5678-1234-567812345678")


def test_recipe_create_normalizes_foundation_values_and_uses_injected_uuid() -> None:
    recipe = Recipe.create(
        title="  Cafe\u0301\t\n de   olla ",
        image_url="  HTTPS://example.test/cover.jpg  ",
        detail="  Line one\r\nLine two\rLine three  ",
        uuid_factory=lambda: RECIPE_ID,
    )

    assert recipe == Recipe(
        id=RECIPE_ID,
        title="Café de olla",
        image_url="HTTPS://example.test/cover.jpg",
        detail="Line one\nLine two\nLine three",
    )


def test_recipe_direct_construction_normalizes_foundation_values() -> None:
    recipe = Recipe(
        id=RECIPE_ID,
        title="  Cafe\u0301\t\n de   olla ",
        image_url="  HTTPS://example.test/cover.jpg  ",
        detail="  Line one\r\nLine two\rLine three  ",
    )

    assert recipe.id == RECIPE_ID
    assert recipe.title == "Café de olla"
    assert recipe.image_url == "HTTPS://example.test/cover.jpg"
    assert recipe.detail == "Line one\nLine two\nLine three"


@pytest.mark.parametrize(
    ("id", "title", "image_url", "detail", "message"),
    [
        ("not-a-uuid", "Title", "https://example.test/cover.jpg", "Detail", "id"),
        (RECIPE_ID, "   ", "https://example.test/cover.jpg", "Detail", "title"),
        (RECIPE_ID, "Title", "relative/image.jpg", "Detail", "image URL"),
        (RECIPE_ID, "Title", "https://example.test/cover.jpg", "  \r\n ", "detail"),
    ],
)
def test_recipe_direct_construction_rejects_invalid_foundation_values(
    id: object,
    title: object,
    image_url: object,
    detail: object,
    message: str,
) -> None:
    with pytest.raises(RecipeValidationError, match=message):
        Recipe(id=id, title=title, image_url=image_url, detail=detail)  # type: ignore[arg-type]


def test_recipe_restore_and_update_foundation_preserve_existing_identity() -> None:
    restored = Recipe.restore(
        id=RECIPE_ID,
        title="Sopa",
        image_url="https://example.test/sopa.jpg",
        detail="Caliente",
    )
    updated = Recipe.update_foundation(
        id=restored.id,
        title="  Sopa de ajo ",
        image_url="https://example.test/ajo.jpg",
        detail="Nueva receta",
    )

    assert restored.id == updated.id == RECIPE_ID
    assert updated.title == "Sopa de ajo"


@pytest.mark.parametrize(
    ("title", "message"),
    [
        ("   \t\n", "title"),
        ("x" * 201, "title"),
        (123, "title"),
    ],
)
def test_recipe_rejects_invalid_titles(title: object, message: str) -> None:
    with pytest.raises(RecipeValidationError, match=message):
        Recipe.create(
            title=title,  # type: ignore[arg-type]
            image_url="https://example.test/cover.jpg",
            detail="Detail",
        )


@pytest.mark.parametrize(
    "image_url",
    [
        "relative/image.jpg",
        "ftp://example.test/image.jpg",
        "https:///missing-host.jpg",
        "https://example.test/has space.jpg",
        "https://example.test/" + ("a" * 2049),
        123,
    ],
)
def test_recipe_rejects_invalid_image_urls(image_url: object) -> None:
    with pytest.raises(RecipeValidationError, match="image URL"):
        Recipe.create(
            title="Title",
            image_url=image_url,  # type: ignore[arg-type]
            detail="Detail",
        )


@pytest.mark.parametrize(
    "detail",
    [
        " \r\n ",
        "x" * 10001,
        123,
    ],
)
def test_recipe_rejects_invalid_detail(detail: object) -> None:
    with pytest.raises(RecipeValidationError, match="detail"):
        Recipe.create(
            title="Title",
            image_url="https://example.test/cover.jpg",
            detail=detail,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("invalid_id", ["not-a-uuid", None, 1])
def test_recipe_rejects_non_uuid_identity_values(invalid_id: object) -> None:
    with pytest.raises(RecipeValidationError, match="id"):
        Recipe.restore(
            id=invalid_id,  # type: ignore[arg-type]
            title="Title",
            image_url="https://example.test/cover.jpg",
            detail="Detail",
        )


@pytest.mark.parametrize("query", [None, 0, False])
def test_title_search_rejects_non_string_queries(query: object) -> None:
    with pytest.raises(RecipeValidationError, match="title search query"):
        normalize_title_search(query)  # type: ignore[arg-type]


def test_title_search_normalizes_case_accents_and_whitespace() -> None:
    assert normalize_title_search(" Tortilla\tESPAÑOLA ") == "tortilla espanola"
    assert normalize_title_search("  \t\n ") == ""


def test_label_normalization_preserves_accents_and_internal_spaces() -> None:
    assert schemas.normalize_label("  COCINA\u00a0\u2003 rápida  ") == "cocina rápida"
    assert schemas.normalize_label("menú ★ 2 / fácil") == "menú ★ 2 / fácil"


@pytest.mark.parametrize("value", ["x" * 26, "  " + ("á" * 26) + "  "])
def test_label_normalization_rejects_more_than_25_characters(value: str) -> None:
    with pytest.raises(RecipeValidationError, match="label"):
        schemas.normalize_label(value)


@pytest.mark.parametrize("value", ["contains\x00nul", "contains\x1fseparator"])
def test_label_normalization_rejects_control_characters(value: str) -> None:
    with pytest.raises(RecipeValidationError, match="label"):
        schemas.normalize_label(value)


def test_label_list_ignores_empty_values_deduplicates_before_the_ten_label_limit() -> None:
    values = [
        " Sopa ",
        "sopa",
        "",
        "   \t",
        "Ágil",
        "a\u0301GIL",
        "uno",
        "dos",
        "tres",
        "cuatro",
        "cinco",
        "seis",
        "siete",
        "ocho",
        "nueve",
        "diez",
        "once",
    ]

    assert schemas.normalize_labels(values) == (
        "sopa",
        "ágil",
        "uno",
        "dos",
        "tres",
        "cuatro",
        "cinco",
        "seis",
        "siete",
        "ocho",
    )


def test_recipe_label_exposes_identity_name_and_color() -> None:
    label = schemas.RecipeLabel(
        id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        name="sin gluten",
        color="#047857",
    )

    assert label.id == UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert label.name == "sin gluten"
    assert label.color == "#047857"
