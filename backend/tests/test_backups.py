"""Verifica la creación de copias de seguridad desde la API."""
from meal_planning_test_support import api_post, authenticate, meal_database


def test_backup_endpoint_requires_authenticated_user(meal_database):
    response = api_post("/api/v1/backups", payload={})

    assert response.status_code == 401


def test_backup_endpoint_creates_database_and_images_snapshot(meal_database, tmp_path, monkeypatch):
    import app.backups as backups

    monkeypatch.setattr(backups, "DATA_ROOT", tmp_path / "images")
    monkeypatch.setattr(backups, "BACKUP_ROOT", tmp_path / "backups")
    monkeypatch.setattr(backups, "create_database_dump", lambda target: target.write_bytes(b"database"))
    backups.DATA_ROOT.mkdir()
    (backups.DATA_ROOT / "example.webp").write_bytes(b"image")
    cookies = authenticate(meal_database)

    response = api_post("/api/v1/backups", payload={}, cookies=cookies, csrf_token=cookies["csrf_token"])

    assert response.status_code == 201
    assert response.json()["status"] == "created"
    archive = backups.BACKUP_ROOT / response.json()["filename"]
    assert archive.is_file()
