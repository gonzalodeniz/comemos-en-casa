from sqlalchemy import create_engine
from app.models import (RecipeShoppingIngredient, RecipeShoppingSection, ShoppingCategory, ShoppingProduct, ShoppingListItem)

from meal_planning_test_support import (
    api_get,
    api_delete,
    authenticate,
    meal_database,
    post_with_session,
)


def test_list_shows_recipe_sections_with_ordered_ingredients(meal_database):
    """Comprueba que la lista muestra las secciones y sus ingredientes ordenados."""
    cookies = authenticate(meal_database)
    with meal_database() as db:
        seccion = RecipeShoppingSection(name="Sopa")
        db.add(seccion)
        db.flush()
        segundo = RecipeShoppingIngredient(section_id=seccion.id, text="Sal", position=1, purchased=True)
        primero = RecipeShoppingIngredient(section_id=seccion.id, text="Agua", position=0, purchased=False)
        db.add_all([segundo, primero])
        db.commit()

    respuesta = api_get("/api/v1/shopping-list", cookies=cookies)

    assert respuesta.status_code == 200
    assert respuesta.json()["recipe_sections"] == [{
        "id": str(seccion.id), "name": "Sopa", "ingredients": [
            {"id": str(primero.id), "text": "Agua", "purchased": False},
            {"id": str(segundo.id), "text": "Sal", "purchased": True},
        ],
    }]


def test_mark_recipe_ingredient_purchased_only_changes_selected_ingredient(meal_database):
    """Comprueba que comprar una línea no modifica las demás líneas."""
    from meal_planning_test_support import api_post

    cookies = authenticate(meal_database)
    with meal_database() as db:
        section = RecipeShoppingSection(name="Sopa")
        db.add(section)
        db.flush()
        selected = RecipeShoppingIngredient(section_id=section.id, text="2 zanahorias", position=0)
        sibling = RecipeShoppingIngredient(section_id=section.id, text="1 cebolla", position=1)
        db.add_all([selected, sibling])
        db.commit()

    response = api_post(
        f"/api/v1/shopping-list/recipe-ingredients/{selected.id}/purchase",
        payload={}, cookies=cookies, csrf_token=cookies["csrf_token"],
    )

    assert response.status_code == 200
    with meal_database() as db:
        assert db.get(RecipeShoppingIngredient, selected.id).purchased is True
        assert db.get(RecipeShoppingIngredient, sibling.id).purchased is False


def test_unmark_recipe_ingredient_purchased_only_changes_selected_ingredient(meal_database):
    """Comprueba que desmarcar una línea no modifica las demás líneas."""
    from meal_planning_test_support import api_post

    cookies = authenticate(meal_database)
    with meal_database() as db:
        section = RecipeShoppingSection(name="Sopa")
        db.add(section)
        db.flush()
        selected = RecipeShoppingIngredient(section_id=section.id, text="2 zanahorias", position=0, purchased=True)
        sibling = RecipeShoppingIngredient(section_id=section.id, text="1 cebolla", position=1, purchased=True)
        db.add_all([selected, sibling])
        db.commit()

    response = api_post(
        f"/api/v1/shopping-list/recipe-ingredients/{selected.id}/unpurchase",
        payload={}, cookies=cookies, csrf_token=cookies["csrf_token"],
    )

    assert response.status_code == 200
    with meal_database() as db:
        assert db.get(RecipeShoppingIngredient, selected.id).purchased is False
        assert db.get(RecipeShoppingIngredient, sibling.id).purchased is True


def test_delete_recipe_ingredient_preserves_sibling_ingredient(meal_database):
    """Comprueba que eliminar una línea conserva las demás de la sección."""
    cookies = authenticate(meal_database)
    with meal_database() as db:
        section = RecipeShoppingSection(name="Sopa")
        db.add(section)
        db.flush()
        selected = RecipeShoppingIngredient(section_id=section.id, text="Zanahoria", position=0)
        sibling = RecipeShoppingIngredient(section_id=section.id, text="Cebolla", position=1)
        db.add_all([selected, sibling])
        db.commit()

    response = api_delete(
        f"/api/v1/shopping-list/recipe-ingredients/{selected.id}", cookies=cookies
    )

    assert response.status_code == 204
    with meal_database() as db:
        assert db.get(RecipeShoppingIngredient, selected.id) is None
        assert db.get(RecipeShoppingIngredient, sibling.id).text == "Cebolla"


def test_delete_recipe_section_preserves_other_sections_and_manual_items(meal_database):
    """Comprueba que eliminar una sección conserva las demás compras."""
    cookies = authenticate(meal_database)
    with meal_database() as db:
        section = RecipeShoppingSection(name="Sopa")
        other = RecipeShoppingSection(name="Ensalada")
        category = ShoppingCategory(name="Verduras")
        db.add_all([section, other, category])
        db.flush()
        ingredient = RecipeShoppingIngredient(section_id=section.id, text="Zanahoria", position=0)
        other_ingredient = RecipeShoppingIngredient(section_id=other.id, text="Tomate", position=0)
        product = ShoppingProduct(category_id=category.id, name="Pan")
        db.add_all([ingredient, other_ingredient, product])
        db.flush()
        manual = ShoppingListItem(product_id=product.id, quantity=1, unit="unit")
        db.add(manual)
        db.commit()

    response = api_delete(
        f"/api/v1/shopping-list/recipe-sections/{section.id}", cookies=cookies
    )

    assert response.status_code == 204
    with meal_database() as db:
        assert db.get(RecipeShoppingSection, section.id) is None
        assert db.get(RecipeShoppingIngredient, ingredient.id) is None
        assert db.get(RecipeShoppingIngredient, other_ingredient.id).text == "Tomate"
        assert db.get(ShoppingListItem, manual.id).quantity == 1


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
    command.stamp(config, "0007_recipes")
    command.upgrade(config, "0009_shopping_products")
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite+pysqlite:///{database}")
    try:
        inspector = inspect(engine)
        assert "shopping_list_items" in inspector.get_table_names()
        assert {"id", "quantity", "unit", "purchased"}.issubset(
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


def test_database_schema_contains_recipe_shopping_sections_with_name(tmp_path, monkeypatch):
    """Comprueba que la migración crea secciones independientes con nombre."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    database = tmp_path / "recipe-shopping.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{database}")
    config = Config("alembic.ini")
    command.stamp(config, "0007_recipes")
    command.upgrade(config, "0011_shopping_item_purchased")
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite+pysqlite:///{database}")
    try:
        inspector = inspect(engine)
        assert "recipe_shopping_sections" in inspector.get_table_names()
        assert {"id", "name"}.issubset(
            {column["name"] for column in inspector.get_columns("recipe_shopping_sections")}
        )
    finally:
        engine.dispose()


def test_database_schema_contains_ordered_recipe_shopping_ingredients(tmp_path, monkeypatch):
    """Comprueba que la migración persiste texto y posición de cada ingrediente."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    database = tmp_path / "recipe-shopping-ingredients.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{database}")
    config = Config("alembic.ini")
    command.stamp(config, "0007_recipes")
    command.upgrade(config, "0011_shopping_item_purchased")
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite+pysqlite:///{database}")
    try:
        inspector = inspect(engine)
        assert "recipe_shopping_ingredients" in inspector.get_table_names()
        columns = {column["name"] for column in inspector.get_columns("recipe_shopping_ingredients")}
        assert {"id", "section_id", "text", "position", "purchased"}.issubset(columns)
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


def test_migration_adds_optional_product_image_path(tmp_path, monkeypatch):
    """Verifica que una base existente admite productos con y sin imagen."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect, text

    database = tmp_path / "productos.sqlite"
    url = f"sqlite+pysqlite:///{database}"
    monkeypatch.setenv("DATABASE_URL", url)
    engine = create_engine(url)
    try:
        with engine.begin() as conexion:
            conexion.execute(text("CREATE TABLE shopping_products (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL)"))
            conexion.execute(text("INSERT INTO shopping_products (id, name) VALUES (1, 'Manzana')"))
        config = Config("alembic.ini")
        command.stamp(config, "0012_recipe_shopping_sections")
        command.upgrade(config, "head")
        columna = next(c for c in inspect(engine).get_columns("shopping_products") if c["name"] == "image_path")
        assert columna["nullable"]
        with engine.begin() as conexion:
            assert conexion.execute(text("SELECT image_path FROM shopping_products WHERE id = 1")).scalar_one() is None
            conexion.execute(text("UPDATE shopping_products SET image_path = 'productos/manzana.webp' WHERE id = 1"))
            assert conexion.execute(text("SELECT image_path FROM shopping_products WHERE id = 1")).scalar_one() == "productos/manzana.webp"
    finally:
        engine.dispose()


def test_create_product_with_image_persists_image(meal_database):
    """Comprueba que la imagen de un producto creado permanece disponible en el catálogo."""
    import base64
    import io
    from PIL import Image

    cookies = authenticate(meal_database)
    imagen = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(imagen, format="PNG")
    datos = base64.b64encode(imagen.getvalue()).decode("ascii")
    preparada = post_with_session(
        "/api/v1/food-labels/images/prepare",
        {"data_url": f"data:image/png;base64,{datos}", "crop": {"x": 0, "y": 0, "width": 10, "height": 10}},
        cookies,
    )
    assert preparada.status_code == 200
    categoria = post_with_session("/api/v1/shopping-categories", {"name": "Frutas"}, cookies)
    ruta = f"/api/v1/shopping-categories/{categoria.json()['id']}/products"
    creado = post_with_session(ruta, {"name": "Manzana", "image_token": preparada.json()["image_token"]}, cookies)
    assert creado.status_code == 201

    productos = api_get(ruta, cookies=cookies).json()["products"]
    producto = next(item for item in productos if item["id"] == creado.json()["id"])
    imagen_guardada = api_get(f"/api/v1{producto['image_url']}", cookies=cookies)
    assert imagen_guardada.status_code == 200
    assert imagen_guardada.headers["content-type"] == "image/webp"


def test_shopping_list_items_have_stable_ids(meal_database):
    """Comprueba que la API expone la identidad persistente del elemento."""
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

    response = api_get("/api/v1/shopping-list", cookies=cookies)
    assert added.json()["id"]
    assert response.json()["items"][0]["id"] == added.json()["id"]


def test_mark_item_as_purchased_moves_it_to_purchased_section(meal_database):
    """Comprueba que marcar comprado conserva datos y persiste el estado."""
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

    marked = post_with_session(
        f"/api/v1/shopping-list/{added.json()['id']}/purchase", {}, cookies
    )

    assert marked.status_code == 200
    response = api_get("/api/v1/shopping-list", cookies=cookies)
    assert response.json()["items"] == []
    assert response.json()["purchased_items"] == [
        {
            "id": added.json()["id"],
            "product_id": product.json()["id"],
            "quantity": 3,
            "unit": "unit",
        }
    ]


def test_unmarking_purchased_item_moves_it_to_pending(meal_database):
    """Comprueba que desmarcar conserva producto, cantidad y medida."""
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
        {"product_id": product.json()["id"], "quantity": 3, "unit": "g"},
        cookies,
    )
    post_with_session(
        f"/api/v1/shopping-list/{added.json()['id']}/purchase", {}, cookies
    )

    unmarked = post_with_session(
        f"/api/v1/shopping-list/{added.json()['id']}/unpurchase", {}, cookies
    )

    assert unmarked.status_code == 200
    response = api_get("/api/v1/shopping-list", cookies=cookies)
    assert response.json()["purchased_items"] == []
    assert response.json()["items"] == [
        {
            "id": added.json()["id"],
            "product_id": product.json()["id"],
            "quantity": 3,
            "unit": "g",
        }
    ]


def test_unmarking_merges_compatible_pending_quantity(meal_database):
    """Comprueba que desmarcar suma cantidades de igual producto y unidad."""
    cookies = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Frutas"}, cookies
    )
    product = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        cookies,
    )
    bought = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 3, "unit": "unit"},
        cookies,
    )
    post_with_session(
        f"/api/v1/shopping-list/{bought.json()['id']}/purchase", {}, cookies
    )
    pending = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 2, "unit": "unit"},
        cookies,
    )

    unmarked = post_with_session(
        f"/api/v1/shopping-list/{bought.json()['id']}/unpurchase", {}, cookies
    )

    assert unmarked.status_code == 200
    response = api_get("/api/v1/shopping-list", cookies=cookies)
    assert response.json()["purchased_items"] == []
    assert response.json()["items"] == [
        {
            "id": pending.json()["id"],
            "product_id": product.json()["id"],
            "quantity": 5,
            "unit": "unit",
        }
    ]


def test_unmarking_preserves_incompatible_units_separately(meal_database):
    """Comprueba que desmarcar no fusiona unidades incompatibles."""
    cookies = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Frutas"}, cookies
    )
    product = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        cookies,
    )
    bought = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 3, "unit": "g"},
        cookies,
    )
    post_with_session(
        f"/api/v1/shopping-list/{bought.json()['id']}/purchase", {}, cookies
    )
    pending = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 2, "unit": "unit"},
        cookies,
    )

    unmarked = post_with_session(
        f"/api/v1/shopping-list/{bought.json()['id']}/unpurchase", {}, cookies
    )

    assert unmarked.status_code == 200
    response = api_get("/api/v1/shopping-list", cookies=cookies)
    assert response.json()["purchased_items"] == []
    assert sorted(
        (item["quantity"], item["unit"]) for item in response.json()["items"]
    ) == [(2, "unit"), (3, "g")]


def test_unmarked_item_persists_for_another_user(meal_database):
    """Comprueba que otro usuario ve pendiente la cantidad resultante al desmarcar."""
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
    bought = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 3, "unit": "unit"},
        creator,
    )
    post_with_session(
        f"/api/v1/shopping-list/{bought.json()['id']}/purchase", {}, creator
    )
    pending = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 2, "unit": "unit"},
        creator,
    )

    unmarked = post_with_session(
        f"/api/v1/shopping-list/{bought.json()['id']}/unpurchase", {}, creator
    )
    response = api_get("/api/v1/shopping-list", cookies=other_user)

    assert unmarked.status_code == 200
    assert response.status_code == 200
    assert response.json()["purchased_items"] == []
    assert response.json()["items"] == [
        {
            "id": pending.json()["id"],
            "product_id": product.json()["id"],
            "quantity": 5,
            "unit": "unit",
        }
    ]


def test_adding_purchased_product_creates_new_pending_item(meal_database):
    """Comprueba que añadir un producto comprado crea una entrada pendiente."""
    cookies = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Frutas"}, cookies
    )
    product = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        cookies,
    )
    purchased = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 3, "unit": "unit"},
        cookies,
    )
    post_with_session(
        f"/api/v1/shopping-list/{purchased.json()['id']}/purchase", {}, cookies
    )

    pending = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 2, "unit": "unit"},
        cookies,
    )

    response = api_get("/api/v1/shopping-list", cookies=cookies)
    assert response.json()["purchased_items"] == [
        {
            "id": purchased.json()["id"],
            "product_id": product.json()["id"],
            "quantity": 3,
            "unit": "unit",
        }
    ]
    assert response.json()["items"] == [
        {
            "id": pending.json()["id"],
            "product_id": product.json()["id"],
            "quantity": 2,
            "unit": "unit",
        }
    ]


def test_marking_item_merges_compatible_purchased_quantities(meal_database):
    """Comprueba que al marcar se fusionan solo medidas compatibles."""
    cookies = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Frutas"}, cookies
    )
    product = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        cookies,
    )
    purchased = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 3, "unit": "unit"},
        cookies,
    )
    post_with_session(
        f"/api/v1/shopping-list/{purchased.json()['id']}/purchase", {}, cookies
    )
    pending = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 2, "unit": "unit"},
        cookies,
    )

    marked = post_with_session(
        f"/api/v1/shopping-list/{pending.json()['id']}/purchase", {}, cookies
    )

    response = api_get("/api/v1/shopping-list", cookies=cookies)
    assert marked.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["purchased_items"] == [
        {
            "id": purchased.json()["id"],
            "product_id": product.json()["id"],
            "quantity": 5,
            "unit": "unit",
        }
    ]


def test_marking_item_keeps_incompatible_units_separate(meal_database):
    """Comprueba que marcar no fusiona unidades incompatibles."""
    cookies = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Frutas"}, cookies
    )
    product = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        cookies,
    )
    purchased = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 3, "unit": "unit"},
        cookies,
    )
    post_with_session(
        f"/api/v1/shopping-list/{purchased.json()['id']}/purchase", {}, cookies
    )
    pending = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 500, "unit": "g"},
        cookies,
    )

    post_with_session(
        f"/api/v1/shopping-list/{pending.json()['id']}/purchase", {}, cookies
    )

    response = api_get("/api/v1/shopping-list", cookies=cookies)
    assert response.json()["items"] == []
    items_by_unit = {
        item["unit"]: item for item in response.json()["purchased_items"]
    }
    assert items_by_unit == {
        "unit": {
            "id": purchased.json()["id"],
            "product_id": product.json()["id"],
            "quantity": 3,
            "unit": "unit",
        },
        "g": {
            "id": pending.json()["id"],
            "product_id": product.json()["id"],
            "quantity": 500,
            "unit": "g",
        },
    }


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
        {
            "id": added.json()["id"],
            "product_id": product.json()["id"],
            "quantity": 3,
            "unit": "unit",
        }
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

    added_ids = []
    for quantity, unit in ((0.5, "kg"), (250, "g")):
        added = post_with_session(
            "/api/v1/shopping-list",
            {"product_id": product.json()["id"], "quantity": quantity, "unit": unit},
            cookies,
        )
        assert added.status_code == 201
        added_ids.append(added.json()["id"])

    response = api_get("/api/v1/shopping-list", cookies=cookies)

    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "id": added_ids[0],
            "product_id": product.json()["id"],
            "quantity": 750,
            "unit": "g",
        }
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


def test_deleting_pending_item_preserves_other_entries(meal_database):
    """Comprueba que borrar una entrada no altera las demás del mismo producto."""
    cookies = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Frutas"}, cookies
    )
    product = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        cookies,
    )
    pendiente = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 3, "unit": "unit"},
        cookies,
    )
    gramos = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 250, "unit": "g"},
        cookies,
    )

    deleted = api_delete(
        f"/api/v1/shopping-list/{pendiente.json()['id']}", cookies=cookies
    )
    response = api_get("/api/v1/shopping-list", cookies=cookies)

    assert deleted.status_code == 204
    assert response.json()["items"] == [
        {
            "id": gramos.json()["id"],
            "product_id": product.json()["id"],
            "quantity": 250,
            "unit": "g",
        }
    ]
    assert response.json()["purchased_items"] == []


def test_deleting_purchased_item_preserves_catalog_product(meal_database):
    """Comprueba que borrar una entrada comprada no elimina el producto del catálogo."""
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
        {"product_id": product.json()["id"], "quantity": 2, "unit": "unit"},
        cookies,
    )
    post_with_session(
        f"/api/v1/shopping-list/{added.json()['id']}/purchase", {}, cookies
    )

    deleted = api_delete(
        f"/api/v1/shopping-list/{added.json()['id']}", cookies=cookies
    )

    assert deleted.status_code == 204
    assert api_get("/api/v1/shopping-list", cookies=cookies).json()["purchased_items"] == []
    assert api_get(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        cookies=cookies,
    ).json()["products"] == [{"id": product.json()["id"], "name": "Manzanas"}]


def test_deleted_item_stays_absent_for_shared_list_readers(meal_database):
    """Comprueba que el borrado persiste para otros usuarios y conserva otras entradas."""
    cookies = authenticate(meal_database)
    other_user = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Frutas"}, cookies
    )
    product = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        cookies,
    )
    deleted_item = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 2, "unit": "unit"},
        cookies,
    )
    remaining_item = post_with_session(
        "/api/v1/shopping-list",
        {"product_id": product.json()["id"], "quantity": 150, "unit": "g"},
        cookies,
    )

    deleted = api_delete(
        f"/api/v1/shopping-list/{deleted_item.json()['id']}", cookies=cookies
    )
    response = api_get("/api/v1/shopping-list", cookies=other_user)

    assert deleted.status_code == 204
    assert response.json()["items"] == [
        {
            "id": remaining_item.json()["id"],
            "product_id": product.json()["id"],
            "quantity": 150,
            "unit": "g",
        }
    ]
    assert response.json()["purchased_items"] == []
