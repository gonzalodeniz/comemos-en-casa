"""Comprueba la consulta autenticada de trucos de cocina."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_database_session
from app.main import app
from app.models import Base, KitchenTip
from meal_planning_test_support import api_get, authenticate


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
