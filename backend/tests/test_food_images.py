import base64
import io

import pytest
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import app.food_images as food_images
from app.food_images import InvalidFoodImage, cleanup_expired_temporary, crop_to_webp


def data_url(image: Image.Image, format: str = "PNG") -> str:
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    encoded = base64.b64encode(buffer.getvalue()).decode()
    mime = "image/png" if format == "PNG" else "image/jpeg"
    return f"data:{mime};base64,{encoded}"


def test_crop_outputs_512_square_webp_and_preserves_alpha():
    source = Image.new("RGBA", (40, 30), (12, 24, 36, 100))
    result = crop_to_webp(data_url(source), {"x": 0, "y": 0, "width": 30, "height": 30})
    with Image.open(io.BytesIO(result)) as output:
        assert output.format == "WEBP"
        assert output.size == (512, 512)
        assert output.mode == "RGBA"


def test_rejects_non_square_crop_and_unsupported_image():
    source = Image.new("RGB", (20, 20), "red")
    with pytest.raises(InvalidFoodImage):
        crop_to_webp(data_url(source), {"x": 0, "y": 0, "width": 20, "height": 10})
    with pytest.raises(InvalidFoodImage):
        crop_to_webp("not-an-image", {"x": 0, "y": 0, "width": 20, "height": 20})


def test_rejects_non_finite_crop_values():
    source = Image.new("RGB", (20, 20), "red")
    with pytest.raises(InvalidFoodImage):
        crop_to_webp(data_url(source), {"x": float("nan"), "y": 0, "width": 20, "height": 20})


def test_expired_temporary_files_are_removed_by_periodic_cleanup(tmp_path):
    session = uuid4()
    token = food_images.save_temporary(tmp_path, session, b"webp")
    path = food_images.temporary_path(tmp_path, session, token)
    assert path is not None
    assert cleanup_expired_temporary(tmp_path, now=path.stat().st_mtime + food_images.TEMP_LIFETIME_SECONDS + 1) == 1
    assert not path.exists()


def test_session_quota_is_serialized_across_concurrent_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(food_images, "MAX_SESSION_BYTES", 10)
    session = uuid4()
    def save():
        try:
            food_images.save_temporary(tmp_path, session, b"12345678")
            return "saved"
        except InvalidFoodImage:
            return "quota"
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: save(), range(2)))
    assert sorted(results) == ["quota", "saved"]
