from sqlalchemy import create_engine

from meal_planning_test_support import (
    api_get,
    authenticate,
    meal_database,
    post_with_session,
)


def test_database_schema_contains_shopping_list_items_with_quantity_and_unit(
    tmp_path, monkeypatch
):
    """Verifica que la migración crea cantidad y unidad en el esquema."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import Numeric, inspect

    database = tmp_path / "shopping-list.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{database}")
    config = Config("alembic.ini")
    command.stamp(config, "0009_shopping_products")
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite+pysqlite:///{database}")
    try:
        inspector = inspect(engine)
        assert "shopping_list_items" in inspector.get_table_names()
        assert {"quantity", "unit"}.issubset(
            {column["name"] for column in inspector.get_columns("shopping_list_items")}
        )
        quantity_column = next(
            column
            for column in inspector.get_columns("shopping_list_items")
            if column["name"] == "quantity"
        )
        assert isinstance(quantity_column["type"], Numeric)
    finally:
        engine.dispose()


def test_adds_product_to_shopping_list_with_quantity_and_unit(meal_database):
    """Comprueba que se puede añadir y recuperar un producto con su cantidad."""
    cookies = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Frutas"}, cookies
    )
    product = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        cookies,
    )

    added = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 3, "unit": "unit"},
        cookies,
    )

    assert added.status_code == 201

    response = api_get("/api/v1/shopping-list", cookies=cookies)

    assert response.status_code == 200
    item = next(
        item for item in response.json()["items"]
        if item["product_id"] == product.json()["id"]
    )
    assert item["quantity"] == 3
    assert item["unit"] == "unit"


def test_aggregates_compatible_quantities_and_keeps_units_separate_from_weight(
    meal_database,
):
    """Comprueba que se suman cantidades compatibles sin mezclar medidas."""
    cookies = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Frutas"}, cookies
    )
    product = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        cookies,
    )

    for quantity, unit in ((2, "unit"), (3, "unit"), (0.5, "kg"), (1.25, "kg")):
        response = post_with_session(
            "/api/v1/shopping-list",
            {"product_id": product.json()["id"], "quantity": quantity, "unit": unit},
            cookies,
        )
        assert response.status_code == 201

    response = api_get("/api/v1/shopping-list", cookies=cookies)

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2
    items_by_unit = {item["unit"]: item for item in items}
    assert items_by_unit["unit"]["product_id"] == product.json()["id"]
    assert items_by_unit["unit"]["quantity"] == 5
    assert items_by_unit["g"]["product_id"] == product.json()["id"]
    assert items_by_unit["g"]["quantity"] == 1750


def test_shows_shopping_list_entries_to_another_user(meal_database):
    """Comprueba que otro usuario puede consultar los elementos de la lista."""
    creator = authenticate(meal_database)
    other_user = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Frutas"}, creator
    )
    product = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        creator,
    )
    added = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 3, "unit": "unit"},
        creator,
    )
    assert added.status_code == 201

    response = api_get("/api/v1/shopping-list", cookies=other_user)

    assert response.status_code == 200
    assert response.json()["items"] == [
        {"product_id": product.json()["id"], "quantity": 3, "unit": "unit"}
    ]


def test_converts_between_grams_and_kilograms_when_aggregating(meal_database):
    """Comprueba que el peso se convierte y se muestra siempre en gramos."""
    cookies = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Frutas"}, cookies
    )
    product = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        cookies,
    )

    for quantity, unit in ((0.5, "kg"), (250, "g")):
        added = post_with_session(
            "/api/v1/shopping-list",
            {"product_id": product.json()["id"], "quantity": quantity, "unit": unit},
            cookies,
        )
        assert added.status_code == 201

    response = api_get("/api/v1/shopping-list", cookies=cookies)

    assert response.status_code == 200
    assert response.json()["items"] == [
        {"product_id": product.json()["id"], "quantity": 750, "unit": "g"}
    ]


def test_redondea_pesos_antes_de_responder_cantidades_enteras(meal_database):
    """Comprueba el redondeo por unidad y la respuesta entera en gramos."""
    cookies = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Frutas"}, cookies
    )
    product = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        cookies,
    )

    first = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 1.255, "unit": "kg"},
        cookies,
    )
    assert first.status_code == 201
    assert first.json()["quantity"] == 1260
    assert type(first.json()["quantity"]) is int

    second = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 250.6, "unit": "g"},
        cookies,
    )
    assert second.status_code == 201
    assert second.json()["quantity"] == 1511
    assert type(second.json()["quantity"]) is int
