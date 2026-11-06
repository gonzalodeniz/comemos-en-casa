# Comprueba los contratos de la API del catálogo de recetas.
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_database_session
from app.main import app
from app.models import Base, FoodLabel, Recipe, RecipeFoodLabel, User, UserSession
from app.security import digest_token
from meal_planning_test_support import authenticate, api_post


@pytest.fixture
def recipe_db(tmp_path, monkeypatch):
    import app.meal_planning_api as meal_planning_api

    monkeypatch.setattr(meal_planning_api, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setenv("AUTH_RATE_LIMIT_HMAC_KEY", "42" * 32)
    engine = create_engine(
        f"sqlite+pysqlite:///{tmp_path / 'recipes.sqlite'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    async def database_session():
        with factory() as db:
            yield db

    app.dependency_overrides[get_database_session] = database_session
    try:
        yield factory
    finally:
        app.dependency_overrides.pop(get_database_session, None)
        engine.dispose()


def test_add_recipe_to_shopping_section_copies_name_and_ordered_ingredients(recipe_db):
    """Comprueba que añadir una receta copia el nombre y sus ingredientes en orden."""
    from app.models import RecipeShoppingIngredient, RecipeShoppingSection

    cookies = authenticate(recipe_db)
    with recipe_db() as db:
        receta = Recipe(title="Sopa", title_canonical="sopa", ingredients="agua\nsal\npasta")
        db.add(receta)
        db.commit()
        recipe_id = receta.id

    response = api_post(
        f"/api/v1/recipes/{recipe_id}/shopping-section",
        payload={}, cookies=cookies, csrf_token=cookies["csrf_token"],
    )
    assert response.status_code == 201
    with recipe_db() as db:
        seccion = db.get(RecipeShoppingSection, UUID(response.json()["id"]))
        ingredientes = db.query(RecipeShoppingIngredient).filter_by(section_id=seccion.id).order_by(RecipeShoppingIngredient.position).all()
        assert seccion.name == "Sopa"
        assert [item.text for item in ingredientes] == ["agua", "sal", "pasta"]
        assert all(not item.purchased for item in ingredientes)


def test_editing_recipe_preserves_existing_shopping_section(recipe_db):
    """Comprueba que editar la receta no cambia su copia en la compra."""
    from meal_planning_test_support import api_get, api_patch

    cookies = authenticate(recipe_db)
    with recipe_db() as db:
        receta = Recipe(title="Sopa", title_canonical="sopa", ingredients="agua\nsal")
        db.add(receta)
        db.commit()
        receta_id = receta.id

    creada = api_post(
        f"/api/v1/recipes/{receta_id}/shopping-section",
        payload={}, cookies=cookies, csrf_token=cookies["csrf_token"],
    )
    assert creada.status_code == 201
    editada = api_patch(
        f"/api/v1/recipes/{receta_id}",
        payload={"title": "Caldo", "ingredients": "pasta"},
        cookies=cookies, csrf_token=cookies["csrf_token"],
    )
    assert editada.status_code == 200
    lista = api_get("/api/v1/shopping-list", cookies=cookies)
    seccion = lista.json()["recipe_sections"][0]
    assert seccion["id"] == creada.json()["id"]
    assert seccion["name"] == "Sopa"
    assert [ingrediente["text"] for ingrediente in seccion["ingredients"]] == ["agua", "sal"]


def test_deleting_recipe_preserves_existing_shopping_section(recipe_db):
    """Comprueba que borrar la receta no elimina su copia de la compra."""
    from meal_planning_test_support import api_delete, api_get

    cookies = authenticate(recipe_db)
    with recipe_db() as db:
        receta = Recipe(title="Sopa", title_canonical="sopa", ingredients="agua\nsal")
        db.add(receta)
        db.commit()
        receta_id = receta.id

    creada = api_post(
        f"/api/v1/recipes/{receta_id}/shopping-section",
        payload={}, cookies=cookies, csrf_token=cookies["csrf_token"],
    )
    assert creada.status_code == 201
    borrada = api_delete(f"/api/v1/recipes/{receta_id}", cookies=cookies)
    assert borrada.status_code == 204
    lista = api_get("/api/v1/shopping-list", cookies=cookies)
    seccion = lista.json()["recipe_sections"][0]
    assert seccion["id"] == creada.json()["id"]
    assert seccion["name"] == "Sopa"
    assert [ingrediente["text"] for ingrediente in seccion["ingredients"]] == ["agua", "sal"]


def test_adding_recipe_twice_creates_independent_shopping_sections(recipe_db):
    """Comprueba que cada incorporación crea una copia independiente."""
    from meal_planning_test_support import api_get, api_delete
    from app.models import RecipeShoppingSection

    cookies = authenticate(recipe_db)
    with recipe_db() as db:
        receta = Recipe(title="Sopa", title_canonical="sopa", ingredients="agua\nsal")
        db.add(receta)
        db.commit()
        receta_id = receta.id
    ruta = f"/api/v1/recipes/{receta_id}/shopping-section"
    primera = api_post(ruta, payload={}, cookies=cookies, csrf_token=cookies["csrf_token"])
    segunda = api_post(ruta, payload={}, cookies=cookies, csrf_token=cookies["csrf_token"])
    assert primera.status_code == segunda.status_code == 201
    lista = api_get("/api/v1/shopping-list", cookies=cookies).json()["recipe_sections"]
    assert len(lista) == 2
    assert lista[0]["id"] != lista[1]["id"]
    eliminada = api_delete(
        f"/api/v1/shopping-list/recipe-sections/{lista[0]['id']}", cookies=cookies
    )
    assert eliminada.status_code == 204
    restante = api_get("/api/v1/shopping-list", cookies=cookies).json()["recipe_sections"]
    assert len(restante) == 1
    assert restante[0]["id"] == lista[1]["id"]
    assert [item["text"] for item in restante[0]["ingredients"]] == ["agua", "sal"]


def test_search_ranks_by_field_matches_and_uses_alphabetical_ties(recipe_db):
    from app.recipes_api import list_recipes, recipe_rank

    with recipe_db() as db:
        soup = FoodLabel(code=f"soup-{uuid4().hex}", name="Sopa")
        chicken = FoodLabel(code=f"chicken-{uuid4().hex}", name="Pollo")
        recipes = [
            Recipe(title="Sopa casera", title_canonical="sopa casera", ingredients="pollo"),
            Recipe(title="Sopa de pescado", title_canonical="sopa de pescado"),
            Recipe(title="Caldo", title_canonical="caldo"),
            Recipe(title="Guiso", title_canonical="guiso", ingredients="pollo"),
            Recipe(title="Sopa al horno", title_canonical="sopa al horno", ingredients="pollo"),
        ]
        db.add_all([soup, chicken, *recipes])
        db.flush()
        db.add_all([
            RecipeFoodLabel(recipe_id=recipes[0].id, food_label_id=soup.id),
            RecipeFoodLabel(recipe_id=recipes[4].id, food_label_id=soup.id),
            RecipeFoodLabel(recipe_id=recipes[1].id, food_label_id=soup.id),
            RecipeFoodLabel(recipe_id=recipes[2].id, food_label_id=chicken.id),
        ])
        db.commit()

        result = list_recipes(q="sopa pollo", food_id=None, _=None, db=db)["recipes"]
        titles = [item["title"] for item in result]
        assert titles == ["Sopa al horno", "Sopa casera", "Sopa de pescado", "Caldo", "Guiso"]
        filtered = list_recipes(q="", food_id=soup.id, _=None, db=db)["recipes"]
        assert [item["title"] for item in filtered] == ["Sopa al horno", "Sopa casera", "Sopa de pescado"]
        assert recipe_rank("Sopa casera", "", [], "SÓPA") is not None
        assert recipe_rank("Crema", "POLLO", [], "pollo") is not None
        assert recipe_rank("Crema", "", [], "pollo") is None


def test_manual_reconciliation_includes_only_old_unreferenced_recipe_images(recipe_db, tmp_path):
    from app.food_images import ORPHAN_GRACE_SECONDS, inspect_possible_orphans, reconcile_orphans

    root = tmp_path / "data"
    folder = root / "recetas"
    folder.mkdir(parents=True)
    active, orphan, fresh = [folder / (letter * 32 + ".webp") for letter in "abc"]
    for image in (active, orphan, fresh):
        image.write_bytes(b"webp")
    now = 2_000_000.0
    for image in (active, orphan):
        os.utime(image, (now - ORPHAN_GRACE_SECONDS - 1,) * 2)
    os.utime(fresh, (now,) * 2)
    with recipe_db() as db:
        db.add(Recipe(title="Linked", title_canonical="linked", image_path=f"recetas/{active.name}"))
        db.commit()
        assert inspect_possible_orphans(root, db, now=now) == [f"recetas/{orphan.name}"]
    assert reconcile_orphans(root, recipe_db, now=now) == [f"recetas/{orphan.name}"]
    assert active.exists() and fresh.exists() and not orphan.exists()


def test_recipe_mutations_validate_csrf_and_preserve_self_title(recipe_db):
    from fastapi import HTTPException
    from starlette.requests import Request
    from starlette.responses import Response

    from app.auth import ActiveSession, require_csrf
    from app.food_images import save_temporary
    from app.recipes_api import create_recipe, data_root, delete_recipe, update_recipe
    from app.models import UserSession

    csrf = f"csrf-{uuid4().hex}"
    session_id = uuid4()
    active = ActiveSession(user=None, session=UserSession(id=session_id, csrf_token_digest=digest_token(csrf)))

    def request(method="POST", token=csrf):
        headers = [(b"origin", b"http://localhost:5173")]
        if token:
            headers.extend([(b"x-csrf-token", token.encode()), (b"cookie", f"csrf_token={token}".encode())])
        return Request({"type": "http", "http_version": "1.1", "method": method,
                        "scheme": "http", "path": "/api/v1/recipes", "raw_path": b"/api/v1/recipes",
                        "query_string": b"", "root_path": "", "headers": headers,
                        "server": ("testserver", 80), "client": ("testclient", 123)})

    with recipe_db() as db:
        with pytest.raises(HTTPException) as denied:
            require_csrf(request(token=""), active)
        assert denied.value.status_code == 403
        label = FoodLabel(code=f"food-{uuid4().hex}", name="Pasta")
        db.add(label)
        db.commit()

        image_token = save_temporary(data_root(), session_id, b"test-image")
        created = create_recipe({"title": "  Pasta casera  ", "food_ids": [str(label.id)], "image_token": image_token}, request(), active, db)
        recipe = created["recipe"]
        assert recipe["title"] == "Pasta casera"
        assert recipe["foods"] == [{"id": str(label.id), "name": "Pasta"}]
        stored_image = data_root() / db.get(Recipe, UUID(recipe["id"])).image_path
        assert stored_image.exists() and stored_image.stat().st_mode & 0o777 == 0o600

        updated = update_recipe(UUID(recipe["id"]), {"title": " pasta casera ", "food_ids": [], "remove_image": True}, request("PATCH"), active, db)
        assert updated["recipe"]["title"] == "pasta casera"
        assert updated["recipe"]["foods"] == []
        assert not stored_image.exists()

        response = Response()
        delete_recipe(UUID(recipe["id"]), request("DELETE"), response, active, db)
        assert response.status_code == 204


def test_deleting_food_removes_only_its_recipe_links(recipe_db):
    import asyncio
    from starlette.requests import Request
    from starlette.responses import Response

    from app.auth import ActiveSession
    from app.meal_planning_api import delete_food_label
    from app.models import UserSession

    token = f"csrf-{uuid4().hex}"
    active = ActiveSession(user=None, session=UserSession(id=uuid4(), csrf_token_digest=digest_token(token)))
    request = Request({"type": "http", "http_version": "1.1", "method": "DELETE",
                       "scheme": "http", "path": "/api/v1/food-labels", "raw_path": b"/api/v1/food-labels",
                       "query_string": b"", "root_path": "", "headers": [
                           (b"origin", b"http://localhost:5173"),
                           (b"x-csrf-token", token.encode()),
                           (b"cookie", f"csrf_token={token}".encode())],
                       "server": ("testserver", 80), "client": ("testclient", 123)})
    with recipe_db() as db:
        pasta = FoodLabel(code=f"food-{uuid4().hex}", name="Pasta")
        soup = FoodLabel(code=f"food-{uuid4().hex}", name="Sopa")
        recipe_one = Recipe(title="Pasta casera", title_canonical="pasta casera")
        recipe_two = Recipe(title="Sopa de pasta", title_canonical="sopa de pasta")
        db.add_all([pasta, soup, recipe_one, recipe_two])
        db.flush()
        db.add_all([
            RecipeFoodLabel(recipe_id=recipe_one.id, food_label_id=pasta.id),
            RecipeFoodLabel(recipe_id=recipe_two.id, food_label_id=pasta.id),
            RecipeFoodLabel(recipe_id=recipe_two.id, food_label_id=soup.id),
        ])
        db.commit()
        asyncio.run(delete_food_label(pasta.id, request, Response(), active, db))
        assert db.get(Recipe, recipe_one.id) is not None
        assert db.get(Recipe, recipe_two.id) is not None
        assert db.query(RecipeFoodLabel).filter_by(food_label_id=pasta.id).count() == 0
        assert db.query(RecipeFoodLabel).filter_by(recipe_id=recipe_two.id).count() == 1


def test_recipe_migration_creates_and_reverts_its_schema():
    import importlib.util
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import inspect

    migration_path = __import__("pathlib").Path(__file__).parents[1] / "migrations" / "versions" / "0007_recipes.py"
    spec = importlib.util.spec_from_file_location("recipe_migration", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        FoodLabel.__table__.create(connection)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert {"recipes", "recipe_food_labels"}.issubset(inspect(connection).get_table_names())
        assert {"uq_recipes_title_canonical"} == {
            constraint["name"] for constraint in inspect(connection).get_unique_constraints("recipes")
        }
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert "recipes" not in inspect(connection).get_table_names()
        assert "recipe_food_labels" not in inspect(connection).get_table_names()
    engine.dispose()


def test_recipe_validation_rejects_malformed_associations_and_image_fields(recipe_db):
    from fastapi import HTTPException

    from app.recipes_api import prepare

    with recipe_db() as db:
        for payload in (
            {"title": "Recipe", "food_ids": [123]},
            {"title": "Recipe", "food_ids": [], "image_token": 123},
            {"title": "Recipe", "food_ids": [], "remove_image": "true"},
        ):
            with pytest.raises(HTTPException) as invalid:
                prepare(payload, db, uuid4())
            assert invalid.value.status_code == 422
