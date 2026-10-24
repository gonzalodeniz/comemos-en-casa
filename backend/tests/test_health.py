"""Verifica los endpoints de salud y disponibilidad.

Comprueba respuestas de estado y el comportamiento cuando la dependencia de base de datos no está disponible.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_service_unavailable_when_database_is_down(monkeypatch):
    monkeypatch.setattr("app.main.database_is_ready", lambda: False)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_ready_returns_ok_when_database_is_available(monkeypatch):
    monkeypatch.setattr("app.main.database_is_ready", lambda: True)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
