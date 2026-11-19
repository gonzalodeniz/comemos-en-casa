"""Comprueba la consulta autenticada de trucos de cocina."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_database_session
from app.main import app
from app.models import Base, KitchenTip
from meal_planning_test_support import api_delete, api_get, api_patch, api_post, authenticate


@pytest.fixture
def trucos_db(tmp_path):
    """Prepara una base de datos aislada para consultar los trucos."""
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'trucos.sqlite'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        db.add_all([
            KitchenTip(title="Limpiar lechuga con Thermomix", content="Indicaciones de prueba."),
            KitchenTip(title="Limpiar una sartén de aluminio", content="Indicaciones de prueba."),
        ])
        db.commit()

    async def database_session():
        with factory() as db:
            yield db

    app.dependency_overrides[get_database_session] = database_session
    try:
        yield factory
    finally:
        app.dependency_overrides.pop(get_database_session, None)
        engine.dispose()


def test_list_kitchen_tips_includes_the_two_initial_examples(trucos_db):
    """Comprueba que el catálogo presenta ambos trucos con indicaciones."""
    cookies = authenticate(trucos_db)
    response = api_get("/api/v1/kitchen-tips", cookies=cookies)

    assert response.status_code == 200
    trucos = response.json()["trucos"]
    assert [truco["title"] for truco in trucos] == [
        "Limpiar lechuga con Thermomix",
        "Limpiar una sartén de aluminio",
    ]
    assert all(truco["content"] for truco in trucos)


def test_created_kitchen_tip_is_visible_to_another_authenticated_user(trucos_db):
    """Comprueba que los trucos creados se comparten entre usuarios autenticados."""
    cookies_usuario = authenticate(trucos_db)
    cookies_otro_usuario = authenticate(trucos_db)
    creado = api_post(
        "/api/v1/kitchen-tips",
        payload={"title": "Nuevo truco", "content": "Contenido compartido."},
        cookies=cookies_usuario,
        csrf_token=cookies_usuario["csrf_token"],
    )
    assert creado.status_code == 201

    response = api_get("/api/v1/kitchen-tips", cookies=cookies_otro_usuario)

    assert response.status_code == 200
    assert any(truco["title"] == "Nuevo truco" for truco in response.json()["trucos"])


@pytest.mark.parametrize("payload", [
    {"title": "   ", "content": "Contenido."},
    {"title": "Título", "content": "   "},
])
def test_create_kitchen_tip_rejects_blank_fields(trucos_db, payload):
    """Comprueba que no se aceptan títulos ni contenidos en blanco."""
    cookies = authenticate(trucos_db)
    response = api_post(
        "/api/v1/kitchen-tips", payload=payload, cookies=cookies,
        csrf_token=cookies["csrf_token"],
    )
    assert response.status_code == 422
    with trucos_db() as db:
        assert db.query(KitchenTip).count() == 2


def test_edit_kitchen_tip_updates_title_and_content_for_another_user(trucos_db):
    """Comprueba que la edición se comparte con otros usuarios autenticados."""
    cookies = authenticate(trucos_db)
    otro_usuario = authenticate(trucos_db)
    truco = api_get("/api/v1/kitchen-tips", cookies=cookies).json()["trucos"][0]
    response = api_patch(f"/api/v1/kitchen-tips/{truco['id']}",
        payload={"title": "Título editado", "content": "Contenido editado."}, cookies=cookies, csrf_token=cookies["csrf_token"])
    assert response.status_code == 200
    actualizado = next(t for t in api_get("/api/v1/kitchen-tips", cookies=otro_usuario).json()["trucos"] if t["id"] == truco["id"])
    assert actualizado["title"] == "Título editado"
    assert actualizado["content"] == "Contenido editado."


@pytest.mark.parametrize("payload", [
    {"title": "   ", "content": "Contenido."},
    {"title": "Título", "content": "   "},
])
def test_edit_kitchen_tip_rejects_blank_fields_without_changing_tip(trucos_db, payload):
    """Comprueba que un campo en blanco conserva el truco original."""
    cookies = authenticate(trucos_db)
    original = api_get("/api/v1/kitchen-tips", cookies=cookies).json()["trucos"][0]
    response = api_patch(f"/api/v1/kitchen-tips/{original['id']}", payload=payload,
        cookies=cookies, csrf_token=cookies["csrf_token"])
    assert response.status_code == 422
    assert next(t for t in api_get("/api/v1/kitchen-tips", cookies=cookies).json()["trucos"] if t["id"] == original["id"]) == original


def test_delete_kitchen_tip_is_persisted_and_visible_to_another_authenticated_user(trucos_db):
    """Comprueba que borrar un truco lo retira del catálogo compartido."""
    cookies_usuario = authenticate(trucos_db)
    cookies_otro_usuario = authenticate(trucos_db)
    truco = api_get("/api/v1/kitchen-tips", cookies=cookies_usuario).json()["trucos"][0]

    eliminado = api_delete(f"/api/v1/kitchen-tips/{truco['id']}", cookies=cookies_usuario)

    assert eliminado.status_code == 204
    trucos_visibles = api_get("/api/v1/kitchen-tips", cookies=cookies_otro_usuario).json()["trucos"]
    assert all(elemento["id"] != truco["id"] for elemento in trucos_visibles)


def test_delete_kitchen_tip_requires_authentication(trucos_db):
    """Comprueba que solo una sesión autenticada puede borrar trucos."""
    truco = api_get("/api/v1/kitchen-tips", cookies=authenticate(trucos_db)).json()["trucos"][0]

    respuesta = api_delete(f"/api/v1/kitchen-tips/{truco['id']}")

    assert respuesta.status_code == 401
