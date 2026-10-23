import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_compose_passes_database_password_without_url_parsing():
    if shutil.which("docker") is None:
        pytest.skip("Docker Compose CLI unavailable")
    result = subprocess.run(
        ["docker", "compose", "config", "--format", "json"],
        cwd=ROOT,
        env={**os.environ, "POSTGRES_PASSWORD": "pa@ss"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    backend = json.loads(result.stdout)["services"]["backend"]["environment"]
    assert backend["DB_PASSWORD"] == "pa@ss"
    assert backend["DB_HOST"] == "postgres"


def test_local_services_only_publish_on_loopback():
    if shutil.which("docker") is None:
        pytest.skip("Docker Compose CLI unavailable")
    result = subprocess.run(
        ["docker", "compose", "config", "--format", "json"],
        cwd=ROOT,
        env={**os.environ, "POSTGRES_PASSWORD": "local-test-only"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    services = json.loads(result.stdout)["services"]
    for name in ("frontend", "backend"):
        assert services[name]["ports"][0]["host_ip"] == "127.0.0.1"
