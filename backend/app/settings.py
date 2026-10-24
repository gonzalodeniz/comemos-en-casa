"""Valida la configuración de orígenes y URL pública.

Rechaza orígenes comodín y exige una URL HTTP(S) absoluta para construir enlaces de recuperación.
"""

import os
from urllib.parse import urlsplit


DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def allowed_origins() -> tuple[str, ...]:
    configured = os.getenv("CORS_ALLOWED_ORIGINS")
    if configured is None:
        return DEFAULT_CORS_ORIGINS
    origins = tuple(origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip())
    if not origins or "*" in origins:
        raise RuntimeError("CORS_ALLOWED_ORIGINS must list explicit origins")
    return origins


def public_app_url() -> str:
    value = os.getenv("APP_PUBLIC_URL", "").strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError("APP_PUBLIC_URL must be an absolute HTTP(S) URL")
    return value
