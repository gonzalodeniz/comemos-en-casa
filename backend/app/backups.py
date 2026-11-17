"""Crea copias conjuntas de la base de datos y los archivos de usuario."""
import asyncio
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.auth import ActiveSession, get_active_session, require_csrf
from app.meal_planning_api import DATA_ROOT

router = APIRouter(prefix="/api/v1", tags=["backups"])
BACKUP_ROOT = Path(os.getenv("APP_BACKUP_ROOT", "/app/data/backups"))
_WRITE_LOCK = asyncio.Lock()


@router.get("/backups")
async def list_backups(active_session: ActiveSession = Depends(get_active_session)):
    """Lista únicamente archivos ZIP de copias almacenados en el servidor."""
    BACKUP_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    files = sorted((path for path in BACKUP_ROOT.glob("backup-*.zip") if path.is_file() and not path.is_symlink()), key=lambda path: path.name, reverse=True)
    return {"backups": [{"filename": path.name, "size": path.stat().st_size} for path in files]}


@router.get("/backups/{filename}")
async def download_backup(filename: str, active_session: ActiveSession = Depends(get_active_session)):
    """Entrega una copia existente que cumpla el formato de nombre generado."""
    if not re.fullmatch(r"backup-\d{8}T\d{6}Z\.zip", filename):
        raise HTTPException(status_code=404, detail="Backup not found")
    path = BACKUP_ROOT / filename
    if path.is_symlink() or not path.is_file():
        raise HTTPException(status_code=404, detail="Backup not found")
    return FileResponse(path, media_type="application/zip", filename=filename)


@router.post("/backups/{filename}/restore")
async def restore_backup(filename: str, request: Request, active_session: ActiveSession = Depends(get_active_session)):
    """Valida la sesión y la protección CSRF antes de restaurar una copia."""
    require_csrf(request, active_session)
    if not re.fullmatch(r"backup-\d{8}T\d{6}Z\.zip", filename):
        raise HTTPException(status_code=404, detail="Backup not found")
    source = BACKUP_ROOT / filename
    if source.is_symlink() or not source.is_file():
        raise HTTPException(status_code=404, detail="Backup not found")
    try:
        async with _WRITE_LOCK:
            await asyncio.to_thread(restore_backup_contents, source)
        return {"status": "restored"}
    except Exception as error:
        raise HTTPException(status_code=500, detail="La restauración falló; la recuperación debe realizarse manualmente") from error


def create_database_dump(target: Path) -> None:
    """Genera un volcado PostgreSQL usando las credenciales del entorno."""
    url = os.getenv("DATABASE_URL")
    if url:
        from sqlalchemy.engine import make_url
        parsed = make_url(url)
        env = {**os.environ, "PGPASSWORD": parsed.password or ""}
        args = ["pg_dump", "--format=plain", "--clean", "--if-exists", "--no-owner", "--no-privileges", "--host", parsed.host or "localhost", "--port", str(parsed.port or 5432), "--username", parsed.username or "", "--dbname", parsed.database or ""]
    else:
        env = {**os.environ, "PGPASSWORD": os.getenv("DB_PASSWORD", "")}
        args = ["pg_dump", "--format=plain", "--clean", "--if-exists", "--no-owner", "--no-privileges", "--host", os.getenv("DB_HOST", "localhost"), "--port", "5432", "--username", os.getenv("DB_USER", "comemos"), "--dbname", os.getenv("DB_NAME", "comemos")]
    with target.open("wb") as output:
        subprocess.run(args, env=env, stdout=output, stderr=subprocess.PIPE, check=True, timeout=300)


def restore_database_dump(source: Path) -> None:
    """Aplica un volcado SQL en una única transacción PostgreSQL."""
    from sqlalchemy.engine import make_url
    url = os.getenv("DATABASE_URL")
    parsed = make_url(url) if url else None
    env = {**os.environ, "PGPASSWORD": (parsed.password if parsed else os.getenv("DB_PASSWORD", "")) or ""}
    args = ["psql", "--no-psqlrc", "--set", "ON_ERROR_STOP=1", "--single-transaction", "--host", parsed.host if parsed else os.getenv("DB_HOST", "localhost"), "--port", str(parsed.port if parsed else 5432), "--username", parsed.username if parsed else os.getenv("DB_USER", "comemos"), "--dbname", parsed.database if parsed else os.getenv("DB_NAME", "comemos"), "--file", str(source)]
    subprocess.run(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=600)


def restore_backup_contents(source: Path) -> None:
    """Valida el ZIP, restaura PostgreSQL y sustituye las imágenes almacenadas."""
    with tempfile.TemporaryDirectory(dir=BACKUP_ROOT) as temporary:
        stage = Path(temporary)
        with zipfile.ZipFile(source) as archive:
            names = archive.namelist()
            if "database.sql" not in names or any(name.startswith("/") or ".." in Path(name).parts for name in names):
                raise ValueError("Invalid backup contents")
            for member in archive.infolist():
                if member.filename.startswith("images/"):
                    if (member.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ValueError("Symbolic links are not allowed")
                    archive.extract(member, stage)
            archive.extract("database.sql", stage)
        restore_database_dump(stage / "database.sql")
        replacement = stage / "images"
        DATA_ROOT.parent.mkdir(parents=True, exist_ok=True)
        previous = stage / "previous-images"
        if DATA_ROOT.exists():
            DATA_ROOT.rename(previous)
        if replacement.exists():
            replacement.rename(DATA_ROOT)


@router.post("/backups", status_code=status.HTTP_201_CREATED)
async def create_backup(request: Request, active_session: ActiveSession = Depends(get_active_session)):
    """Guarda una copia comprimida mientras las peticiones de escritura esperan."""
    require_csrf(request, active_session)
    BACKUP_ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    filename = f"backup-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.zip"
    destination = BACKUP_ROOT / filename
    try:
        async with _WRITE_LOCK:
            with tempfile.TemporaryDirectory(dir=BACKUP_ROOT) as temporary:
                temporary_path = Path(temporary)
                dump = temporary_path / "database.sql"
                await asyncio.to_thread(create_database_dump, dump)
                with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                    archive.write(dump, "database.sql")
                    if DATA_ROOT.exists():
                        for file in DATA_ROOT.rglob("*"):
                            if file.is_file() and not file.is_symlink():
                                archive.write(file, str(Path("images") / file.relative_to(DATA_ROOT)))
        return {"status": "created", "filename": filename}
    except Exception as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="No se pudo crear la copia de seguridad") from error
