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


def test_backup_restore_requires_authenticated_user(meal_database):
    response = api_post("/api/v1/backups/backup-20261117T100000Z.zip/restore", payload={})

    assert response.status_code == 401


def test_backup_restore_replaces_database_and_images_from_archive(meal_database, tmp_path, monkeypatch):
    import zipfile
    import app.backups as backups

    monkeypatch.setattr(backups, "BACKUP_ROOT", tmp_path / "backups")
    backups.BACKUP_ROOT.mkdir()
    archive = backups.BACKUP_ROOT / "backup-20261117T100000Z.zip"
    with zipfile.ZipFile(archive, "w") as package:
        package.writestr("database.sql", "-- valid dump")
        package.writestr("images/comidas/item.webp", b"image")
    restored = []
    monkeypatch.setattr(backups, "restore_backup_contents", lambda source: restored.append(source))
    cookies = authenticate(meal_database)

    response = api_post(f"/api/v1/backups/{archive.name}/restore", payload={}, cookies=cookies, csrf_token=cookies["csrf_token"])

    assert response.status_code == 200
    assert response.json() == {"status": "restored"}
    assert restored == [archive]


def test_backup_restore_rejects_invalid_archive_and_reports_manual_recovery(meal_database, tmp_path, monkeypatch):
    import app.backups as backups

    monkeypatch.setattr(backups, "BACKUP_ROOT", tmp_path / "backups")
    backups.BACKUP_ROOT.mkdir()
    (backups.BACKUP_ROOT / "backup-20261117T100000Z.zip").write_bytes(b"not a zip")
    cookies = authenticate(meal_database)

    response = api_post("/api/v1/backups/backup-20261117T100000Z.zip/restore", payload={}, cookies=cookies, csrf_token=cookies["csrf_token"])

    assert response.status_code == 500
    assert "recuperación debe realizarse manualmente" in response.json()["detail"]


def test_restore_service_applies_database_and_restores_image_files(tmp_path, monkeypatch):
    import zipfile
    import app.backups as backups

    monkeypatch.setattr(backups, "BACKUP_ROOT", tmp_path / "backups")
    monkeypatch.setattr(backups, "DATA_ROOT", tmp_path / "data")
    backups.BACKUP_ROOT.mkdir()
    archive = backups.BACKUP_ROOT / "backup-20261117T100000Z.zip"
    with zipfile.ZipFile(archive, "w") as package:
        package.writestr("database.sql", "-- dump")
        package.writestr("images/comidas/new.webp", b"new image")
    executed = []
    monkeypatch.setattr(backups, "restore_database_dump", lambda source: executed.append(source.read_text()))

    backups.restore_backup_contents(archive)

    assert executed == ["-- dump"]
    assert (backups.DATA_ROOT / "comidas/new.webp").read_bytes() == b"new image"


def test_backup_schedule_requires_authenticated_user(meal_database):
    response = api_post("/api/v1/backups/schedule", payload={})

    assert response.status_code == 401


def test_user_can_save_daily_or_weekly_schedule_and_maximum(meal_database):
    cookies = authenticate(meal_database)

    response = api_post("/api/v1/backups/schedule", payload={"frequency": "weekly", "maximum": 5}, cookies=cookies, csrf_token=cookies["csrf_token"])

    assert response.status_code == 200
    assert response.json() == {"frequency": "weekly", "maximum": 5, "enabled": True}


def test_automatic_backup_runs_using_saved_schedule(meal_database, monkeypatch):
    import asyncio
    import app.backups as backups
    from app.models import BackupSchedule

    with meal_database() as db:
        db.add(BackupSchedule(id=1, frequency="daily", maximum=3))
        db.commit()
    created = []
    monkeypatch.setattr(backups, "create_backup_archive", lambda: created.append(True))

    asyncio.run(backups.run_scheduled_backup(session_factory=meal_database))

    assert created == [True]
    with meal_database() as db:
        schedule = db.get(BackupSchedule, 1)
        assert schedule.last_run_at is not None


def test_backup_retention_removes_oldest_when_limit_is_reached(meal_database, tmp_path, monkeypatch):
    import asyncio
    from datetime import datetime, timezone
    import app.backups as backups
    from app.models import BackupSchedule

    monkeypatch.setattr(backups, "BACKUP_ROOT", tmp_path / "backups")
    backups.BACKUP_ROOT.mkdir()
    for filename in ("backup-20261110T020000Z.zip", "backup-20261111T020000Z.zip"):
        (backups.BACKUP_ROOT / filename).write_bytes(b"old")
    with meal_database() as db:
        db.add(BackupSchedule(id=1, frequency="daily", maximum=2))
        db.commit()
    monkeypatch.setattr(backups, "create_backup_archive", lambda: (backups.BACKUP_ROOT / "backup-20261112T020000Z.zip").write_bytes(b"new"))

    asyncio.run(backups.run_scheduled_backup(now=datetime(2026, 11, 12, 2, tzinfo=timezone.utc), session_factory=meal_database))

    assert sorted(path.name for path in backups.BACKUP_ROOT.glob("backup-*.zip")) == ["backup-20261111T020000Z.zip", "backup-20261112T020000Z.zip"]
