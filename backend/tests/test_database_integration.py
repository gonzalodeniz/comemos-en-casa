import os
import subprocess

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.skipif(
    os.getenv("RUN_DB_INTEGRATION") != "1",
    reason="requires an isolated PostgreSQL instance and an applied migration",
)
def test_database_is_ready_and_baseline_is_applied():
    with TestClient(app) as client:
        response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    migration = subprocess.run(
        ["alembic", "current"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert migration.returncode == 0, migration.stderr
    assert "0001_baseline (head)" in migration.stdout
