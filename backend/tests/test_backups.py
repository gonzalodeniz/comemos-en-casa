"""Verifica la creación de copias de seguridad desde la API."""
from meal_planning_test_support import api_get, api_post, authenticate, meal_database


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


def test_backup_list_requires_authenticated_user(meal_database):
    response = api_get("/api/v1/backups")

    assert response.status_code == 401


def test_backup_list_returns_available_archives(meal_database, tmp_path, monkeypatch):
    import app.backups as backups

    monkeypatch.setattr(backups, "BACKUP_ROOT", tmp_path / "backups")
    backups.BACKUP_ROOT.mkdir()
    (backups.BACKUP_ROOT / "backup-20261117T100000Z.zip").write_bytes(b"archive")
    (backups.BACKUP_ROOT / "unrelated.zip").write_bytes(b"ignore")
    cookies = authenticate(meal_database)

    response = api_get("/api/v1/backups", cookies=cookies)

    assert response.status_code == 200
    assert response.json() == {"backups": [{"filename": "backup-20261117T100000Z.zip", "size": 7}]}


def test_backup_download_returns_selected_archive(meal_database, tmp_path, monkeypatch):
    import app.backups as backups

    monkeypatch.setattr(backups, "BACKUP_ROOT", tmp_path / "backups")
    backups.BACKUP_ROOT.mkdir()
    (backups.BACKUP_ROOT / "backup-20261117T100000Z.zip").write_bytes(b"archive bytes")
    cookies = authenticate(meal_database)

    response = api_get("/api/v1/backups/backup-20261117T100000Z.zip", cookies=cookies)

    assert response.status_code == 200
    assert response.content == b"archive bytes"
    assert response.headers["content-type"] == "application/zip"


def test_backup_download_rejects_unknown_filename(meal_database, tmp_path, monkeypatch):
    import app.backups as backups

    monkeypatch.setattr(backups, "BACKUP_ROOT", tmp_path / "backups")
    backups.BACKUP_ROOT.mkdir()
    (backups.BACKUP_ROOT / "backup-20261117T100000Z.zip").write_bytes(b"archive")
    cookies = authenticate(meal_database)

    response = api_get("/api/v1/backups/../../secret.zip", cookies=cookies)

    assert response.status_code == 404
