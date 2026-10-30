"""Validate, crop and store user-provided food images."""
from __future__ import annotations

import base64
import binascii
import fcntl
import io
import math
import os
import threading
import time
from pathlib import Path
from uuid import UUID, uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_PIXELS = 5_000_000
MAX_SESSION_BYTES = 50 * 1024 * 1024
TEMP_LIFETIME_SECONDS = 3600
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
_quota_guard = threading.RLock()


class InvalidFoodImage(ValueError):
    pass


def _decode_data_url(data_url: str) -> bytes:
    if not data_url.startswith("data:image/") or ";base64," not in data_url:
        raise InvalidFoodImage("Provide a supported image file")
    _, encoded = data_url.split(",", 1)
    if len(encoded) > ((MAX_INPUT_BYTES + 2) // 3) * 4:
        raise InvalidFoodImage("Image exceeds 2 MiB")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise InvalidFoodImage("Invalid image data") from error
    if not raw or len(raw) > MAX_INPUT_BYTES:
        raise InvalidFoodImage("Image exceeds 2 MiB")
    return raw


def crop_to_webp(data_url: str, crop: dict[str, float]) -> bytes:
    raw = _decode_data_url(data_url)
    try:
        with Image.open(io.BytesIO(raw)) as image:
            if image.format not in ALLOWED_FORMATS or getattr(image, "n_frames", 1) != 1:
                raise InvalidFoodImage("Only static JPG, PNG, or WebP images are supported")
            if image.width * image.height > MAX_PIXELS:
                raise InvalidFoodImage("Image exceeds 5 megapixels")
            image = ImageOps.exif_transpose(image).convert("RGBA")
            try:
                x, y, width, height = (float(crop[k]) for k in ("x", "y", "width", "height"))
            except (KeyError, TypeError, ValueError, OverflowError) as error:
                raise InvalidFoodImage("Invalid crop area") from error
            if not all(math.isfinite(value) for value in (x, y, width, height)):
                raise InvalidFoodImage("Invalid crop area")
            if x < 0 or y < 0 or width <= 0 or height <= 0 or abs(width - height) > 1.5:
                raise InvalidFoodImage("Crop must be square")
            if x >= image.width or y >= image.height or x + width > image.width + 1 or y + height > image.height + 1:
                raise InvalidFoodImage("Crop is outside the image")
            left, top = max(0, round(x)), max(0, round(y))
            right, bottom = min(image.width, round(x + width)), min(image.height, round(y + height))
            side = min(right - left, bottom - top)
            if side <= 0:
                raise InvalidFoodImage("Invalid crop area")
            cropped = image.crop((left, top, left + side, top + side)).resize((512, 512), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            cropped.save(output, format="WEBP", quality=85, method=4)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        if isinstance(error, InvalidFoodImage):
            raise
        raise InvalidFoodImage("Image could not be decoded") from error


def _session_temp_dir(root: Path, session_id: UUID) -> Path:
    return root / ".tmp" / str(session_id)


def save_temporary(root: Path, session_id: UUID, image_data: bytes) -> str:
    directory = _session_temp_dir(root, session_id)
    with _quota_guard:
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / ".quota.lock").open("a+b") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                now = time.time()
                total = 0
                for path in directory.glob("*.webp"):
                    try:
                        if now - path.stat().st_mtime > TEMP_LIFETIME_SECONDS:
                            path.unlink(missing_ok=True)
                        else:
                            total += path.stat().st_size
                    except OSError:
                        continue
                if total + len(image_data) > MAX_SESSION_BYTES:
                    raise InvalidFoodImage("Temporary image quota exceeded")
                token = uuid4().hex
                target = directory / f"{token}.webp"
                temporary = directory / f".{token}.tmp"
                temporary.write_bytes(image_data)
                os.replace(temporary, target)
                return token
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)


def cleanup_expired_temporary(root: Path, *, now: float | None = None, max_entries: int = 10000) -> int:
    """Remove expired temp files in a bounded scan; safe to run periodically."""
    cutoff = (time.time() if now is None else now) - TEMP_LIFETIME_SECONDS
    removed = 0
    temp_root = root / ".tmp"
    with _quota_guard:
        try:
            entries = temp_root.iterdir()
            scanned = 0
            for session_dir in entries:
                if scanned >= max_entries:
                    break
                scanned += 1
                if not session_dir.is_dir() or session_dir.is_symlink():
                    continue
                for path in session_dir.iterdir():
                    if scanned >= max_entries:
                        break
                    scanned += 1
                    if path.suffix == ".webp" and path.is_file() and not path.is_symlink() and path.stat().st_mtime < cutoff:
                        path.unlink(missing_ok=True)
                        removed += 1
        except FileNotFoundError:
            pass
    return removed


def temporary_path(root: Path, session_id: UUID, token: str) -> Path | None:
    if len(token) != 32 or any(c not in "0123456789abcdef" for c in token):
        return None
    path = _session_temp_dir(root, session_id) / f"{token}.webp"
    try:
        if time.time() - path.stat().st_mtime > TEMP_LIFETIME_SECONDS:
            path.unlink(missing_ok=True)
            return None
    except OSError:
        return None
    return path


def publish_temporary(root: Path, session_id: UUID, token: str) -> str | None:
    with _quota_guard:
        source = temporary_path(root, session_id, token)
        if source is None:
            return None
        folder = root / "comidas"
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{uuid4().hex}.webp"
        os.replace(source, target)
        return f"comidas/{target.name}"
