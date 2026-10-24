"""Centraliza las primitivas de seguridad de autenticación.

Normaliza correos y contraseñas, aplica Argon2 y resume tokens e identificadores de limitación antes de persistirlos.
"""

import hashlib
import hmac
import os
import secrets
import unicodedata

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)
from email_validator import EmailNotValidError, validate_email


PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_HASHER = PasswordHasher(
    time_cost=2,
    memory_cost=19 * 1024,
    parallelism=1,
)
_DUMMY_PASSWORD_HASH = PASSWORD_HASHER.hash("not-a-real-account-password")


def canonicalize_email(value: str) -> tuple[str, str]:
    original = value.strip()
    validated = validate_email(
        original,
        allow_display_name=False,
        check_deliverability=False,
        test_environment=True,
    )
    domain = (validated.ascii_domain or validated.domain).lower()
    local_part = unicodedata.normalize("NFC", validated.local_part).casefold()
    canonical = f"{local_part}@{domain}"
    return original, canonical


def validate_password(password: str) -> None:
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise ValueError("Password must contain between 8 and 128 characters")


def normalize_password(password: str) -> str:
    return unicodedata.normalize("NFC", password)


def hash_password(password: str) -> str:
    validate_password(password)
    return PASSWORD_HASHER.hash(normalize_password(password))


def verify_password(password_hash: str | None, password: str) -> bool:
    # Ejecuta un hash ficticio cuando no hay cuenta para reducir diferencias temporales observables.
    candidate = normalize_password(password)
    if not password_hash:
        try:
            PASSWORD_HASHER.verify(_DUMMY_PASSWORD_HASH, candidate)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            pass
        return False
    try:
        return PASSWORD_HASHER.verify(password_hash, candidate)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def rate_limit_hmac_key() -> bytes:
    value = os.getenv("AUTH_RATE_LIMIT_HMAC_KEY", "")
    try:
        key = bytes.fromhex(value)
    except ValueError as error:
        raise RuntimeError("AUTH_RATE_LIMIT_HMAC_KEY must be a 32-byte hex value") from error
    if len(key) != 32:
        raise RuntimeError("AUTH_RATE_LIMIT_HMAC_KEY must be a 32-byte hex value")
    return key


def digest_rate_limit_key(key: str) -> str:
    return hmac.new(rate_limit_hmac_key(), key.encode("utf-8"), hashlib.sha256).hexdigest()
