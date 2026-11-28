# Comprueba categorías y productos del catálogo compartido de compra.
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select


from meal_planning_test_support import meal_database, api_get, api_patch, authenticate, post_with_session


def test_mover_producto_conserva_identidad_imagen_y_entradas(meal_database):
    """Traslada el producto y publica la URL de imagen con la categoría de destino."""
    from app.models import ShoppingCategory, ShoppingListItem, ShoppingProduct

    cookies = authenticate(meal_database)
    with meal_database() as db:
        origen, destino = ShoppingCategory(name="Fruta"), ShoppingCategory(name="Otros")
        db.add_all([origen, destino])
        db.flush()
        producto = ShoppingProduct(category_id=origen.id, name="Pera", image_path="productos/pera.webp")
        db.add(producto)
        db.flush()
        entrada = ShoppingListItem(product_id=producto.id, quantity=1, unit="unit", purchased=False)
        db.add(entrada)
        db.commit()
        origen_id, destino_id, producto_id, entrada_id = origen.id, destino.id, producto.id, entrada.id

    base = "/api/v1/shopping-categories"
    ruta_origen = f"{base}/{origen_id}/products"
    ruta_destino = f"{base}/{destino_id}/products"
    respuesta = api_patch(f"{ruta_origen}/{producto_id}", payload={"category_id": str(destino_id)}, cookies=cookies, csrf_token=cookies["csrf_token"])

    assert respuesta.status_code == 200
    trasladado = respuesta.json()
    assert trasladado["id"] == str(producto_id)
    assert trasladado["name"] == "Pera"
    assert trasladado["image_url"].startswith(f"/shopping-categories/{destino_id}/products/{producto_id}/image?v=")
    assert api_get(ruta_origen, cookies=cookies).json()["products"] == []
    assert api_get(ruta_destino, cookies=cookies).json()["products"] == [trasladado]
    assert api_get("/api/v1/shopping-products/search?q=pera", cookies=cookies).json()["products"] == [
        {**trasladado, "category_id": str(destino_id)},
    ]
    with meal_database() as db:
        assert db.get(ShoppingProduct, producto_id).image_path == "productos/pera.webp"
        assert db.get(ShoppingListItem, entrada_id).product_id == producto_id


@pytest.mark.parametrize(("destino", "estado"), [("no-es-un-uuid", 422), (str(uuid4()), 404)])
def test_mover_producto_rechaza_destino_invalido_sin_aplicar_otros_cambios(meal_database, destino, estado):
    """No modifica el producto si la categoría de destino no es válida."""
    cookies = authenticate(meal_database)
    categoria = post_with_session("/api/v1/shopping-categories", {"name": "Fruta"}, cookies).json()
    base = f"/api/v1/shopping-categories/{categoria['id']}/products"
    producto = post_with_session(base, {"name": "Pera"}, cookies).json()

    respuesta = api_patch(f"{base}/{producto['id']}", payload={"category_id": destino, "name": "Manzana"}, cookies=cookies, csrf_token=cookies["csrf_token"])

    assert respuesta.status_code == estado
    assert api_get(base, cookies=cookies).json()["products"] == [producto]


def test_renombrar_y_rechazar_duplicados_en_distintas_categorias(meal_database):
    """Impide duplicados globales al crear o renombrar, ignorando espacios y mayúsculas."""
    from meal_planning_test_support import api_patch
    cookies = authenticate(meal_database)
    primera = post_with_session("/api/v1/shopping-categories", {"name": "Fruta"}, cookies).json()
    segunda = post_with_session("/api/v1/shopping-categories", {"name": "Otros"}, cookies).json()
    ruta = f"/api/v1/shopping-categories/{primera['id']}/products"
    producto = post_with_session(ruta, {"name": "Pera"}, cookies).json()
    otra_ruta = f"/api/v1/shopping-categories/{segunda['id']}/products"
    otro = post_with_session(otra_ruta, {"name": "Manzana"}, cookies).json()
    assert post_with_session(otra_ruta, {"name": "  pERA  "}, cookies).status_code == 409
    assert api_patch(f"{otra_ruta}/{otro['id']}", payload={"name": " PERA "}, cookies=cookies, csrf_token=cookies["csrf_token"]).status_code == 409
    respuesta = api_patch(f"{ruta}/{producto['id']}", payload={"name": " Pera conferencia "}, cookies=cookies, csrf_token=cookies["csrf_token"])
    assert respuesta.status_code == 200
    assert respuesta.json()["name"] == "Pera conferencia"


def test_authenticated_user_can_create_category(meal_database):
    cookies = authenticate(meal_database)

    response = post_with_session("/api/v1/shopping-categories", {"name": "Verduras"}, cookies)

    assert response.status_code == 201
    assert response.json()["name"] == "Verduras"

def test_search_products_matches_partial_name_across_categories(meal_database):
    """Busca productos por nombre parcial en todas las categorías."""
    cookies = authenticate(meal_database)
    fruta = post_with_session("/api/v1/shopping-categories", {"name": "Fruta"}, cookies).json()
    limpieza = post_with_session("/api/v1/shopping-categories", {"name": "Limpieza"}, cookies).json()
    fina = post_with_session(f"/api/v1/shopping-categories/{fruta['id']}/products", {"name": "Sal fina"}, cookies).json()
    gorda = post_with_session(f"/api/v1/shopping-categories/{limpieza['id']}/products", {"name": "Sal gorda"}, cookies).json()

    respuesta = api_get("/api/v1/shopping-products/search?q=sal", cookies=cookies)

    assert respuesta.status_code == 200
    assert respuesta.json()["products"] == [
        {**fina, "category_id": fruta["id"]},
        {**gorda, "category_id": limpieza["id"]},
    ]

def test_create_product_in_category(meal_database):
    """Comprueba la creación autenticada de un producto en una categoría."""
    cookies = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Verduras"}, cookies
    )

    response = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        cookies,
    )

    assert response.status_code == 201
    assert response.json() == {"id": response.json()["id"], "name": "Manzanas"}

def test_product_is_visible_to_another_user(meal_database):
    """Comprueba que el producto creado forma parte del catálogo compartido."""
    creator = authenticate(meal_database)
    other_user = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Verduras"}, creator
    )
    created = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "Manzanas"},
        creator,
    )

    response = api_get(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        cookies=other_user,
    )

    assert response.status_code == 200
    assert response.json()["products"] == [created.json()]

def test_create_product_rejects_blank_name(meal_database):
    """Comprueba que un nombre compuesto solo por espacios se rechaza."""
    cookies = authenticate(meal_database)
    category = post_with_session(
        "/api/v1/shopping-categories", {"name": "Verduras"}, cookies
    )

    response = post_with_session(
        f"/api/v1/shopping-categories/{category.json()['id']}/products",
        {"name": "   "},
        cookies,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid product"

def test_another_authenticated_user_can_list_created_category(meal_database):
    creator = authenticate(meal_database)
    other_user = authenticate(meal_database)
    created = post_with_session("/api/v1/shopping-categories", {"name": "Verduras"}, creator)

    response = api_get("/api/v1/shopping-categories", cookies=other_user)

    assert response.status_code == 200
    assert response.json()["categories"] == [
        {"id": created.json()["id"], "name": "Verduras"}
    ]

def test_category_can_be_persisted(meal_database):
    from app.models import ShoppingCategory

    with meal_database() as db:
        db.add(ShoppingCategory(name="Verduras"))
        db.commit()
        category = db.scalar(select(ShoppingCategory))

    assert category.name == "Verduras"

def test_shopping_category_model_stores_its_name():
    from app.models import ShoppingCategory

    category = ShoppingCategory(name="Verduras")

    assert category.name == "Verduras"

def test_database_schema_contains_shopping_categories(tmp_path, monkeypatch):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    database = tmp_path / "migrations.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{database}")
    config = Config("alembic.ini")
    # La revisión marcada presupone que la tabla de usuarios ya existe.
    import sqlite3
    with sqlite3.connect(database) as conexion:
        conexion.execute("CREATE TABLE users (id TEXT PRIMARY KEY)")
        # La revisión 0007 también presupone creada la planificación de comidas.
        conexion.execute("CREATE TABLE meal_assignments (id TEXT PRIMARY KEY)")
    command.stamp(config, "0007_recipes")
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite+pysqlite:///{database}")
    try:
        assert "shopping_categories" in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_borrar_producto_elimina_entradas_y_conserva_recetas(meal_database):
    """Verifica el borrado de entradas pendientes y compradas sin alterar recetas."""
    from app.models import Recipe, ShoppingCategory, ShoppingListItem, ShoppingProduct
    from meal_planning_test_support import api_delete
    cookies = authenticate(meal_database)
    with meal_database() as db:
        categoria = ShoppingCategory(name="Fruta")
        db.add(categoria)
        db.flush()
        producto = ShoppingProduct(category_id=categoria.id, name="Pera")
        db.add(producto)
        db.flush()
        db.add_all([ShoppingListItem(product_id=producto.id, quantity=1, unit="unit", purchased=False), ShoppingListItem(product_id=producto.id, quantity=1, unit="unit", purchased=True), Recipe(title="Postre", title_canonical="postre", ingredients="Pera")])
        db.commit()
        ruta = f"/api/v1/shopping-categories/{categoria.id}/products/{producto.id}"
    assert api_delete(ruta, cookies=cookies).status_code == 204
    assert api_get(ruta.rsplit('/', 1)[0], cookies=cookies).json()["products"] == []
    lista = api_get("/api/v1/shopping-list", cookies=cookies).json()
    assert lista["items"] == [] and lista["purchased_items"] == []
    with meal_database() as db:
        assert db.scalar(select(Recipe)).ingredients == "Pera"


def test_borrar_producto_exige_sesion_y_csrf(meal_database):
    """Protege el borrado frente a peticiones sin sesión o sin token CSRF."""
    from meal_planning_test_support import api_delete
    cookies = authenticate(meal_database)
    categoria = post_with_session("/api/v1/shopping-categories", {"name": "Fruta"}, cookies).json()
    base = f"/api/v1/shopping-categories/{categoria['id']}/products"
    producto = post_with_session(base, {"name": "Pera"}, cookies).json()
    ruta = f"{base}/{producto['id']}"
    assert api_delete(ruta).status_code == 401
    assert api_delete(ruta, cookies={"session": cookies["session"]}).status_code == 403
    assert api_get(base, cookies=cookies).json()["products"] == [producto]
