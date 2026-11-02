from sqlalchemy import create_engine, select


from meal_planning_test_support import meal_database, api_get, authenticate, post_with_session


def test_authenticated_user_can_create_category(meal_database):
    cookies = authenticate(meal_database)

    response = post_with_session("/api/v1/shopping-categories", {"name": "Verduras"}, cookies)

    assert response.status_code == 201
    assert response.json()["name"] == "Verduras"

def test_create_product_in_category(meal_database):
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
    command.stamp(config, "0007_recipes")
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite+pysqlite:///{database}")
    try:
        assert "shopping_categories" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
