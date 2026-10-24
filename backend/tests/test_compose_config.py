"""Comprueba las garantías de configuración de Compose.

Asegura que los secretos y puertos locales se configuren de forma segura sin iniciar servicios.
"""

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
        env={
            **os.environ,
            "POSTGRES_PASSWORD": "pa@ss",
            "AUTH_RATE_LIMIT_HMAC_KEY": "0" * 64,
            "APP_PUBLIC_URL": "http://localhost:5173",
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    backend = json.loads(result.stdout)["services"]["backend"]["environment"]
    assert backend["DB_PASSWORD"] == "pa@ss"
    assert backend["DB_HOST"] == "postgres"
    assert backend["APP_PUBLIC_URL"] == "http://localhost:5173"


def test_local_services_only_publish_on_loopback():
    if shutil.which("docker") is None:
        pytest.skip("Docker Compose CLI unavailable")
    result = subprocess.run(
        ["docker", "compose", "config", "--format", "json"],
        cwd=ROOT,
        env={
            **os.environ,
            "POSTGRES_PASSWORD": "local-test-only",
            "AUTH_RATE_LIMIT_HMAC_KEY": "0" * 64,
            "APP_PUBLIC_URL": "http://localhost:5173",
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    services = json.loads(result.stdout)["services"]
    for name in ("frontend", "backend"):
        assert services[name]["ports"][0]["host_ip"] == "127.0.0.1"
