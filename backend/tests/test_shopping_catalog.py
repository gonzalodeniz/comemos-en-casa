# Comprueba categorías y productos del catálogo compartido de compra.
from sqlalchemy import create_engine, select


from meal_planning_test_support import meal_database, api_get, authenticate, post_with_session


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
    command.stamp(config, "0007_recipes")
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite+pysqlite:///{database}")
    try:
        assert "shopping_categories" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
