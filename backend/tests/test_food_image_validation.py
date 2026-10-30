"""Content-validation boundaries using synthetic images and no network."""
import base64
import io

import pytest
from PIL import Image

from app.food_images import MAX_INPUT_BYTES, InvalidFoodImage, _decode_data_url, crop_to_webp


def url(raw: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(raw).decode()


def encoded_image(fmt: str, size=(12, 12), **kwargs) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", size, "red").save(output, format=fmt, **kwargs)
    return output.getvalue()


@pytest.mark.parametrize("fmt", ["JPEG", "PNG", "WEBP"])
def test_supported_content_decodes_regardless_of_claimed_mime(fmt):
    result = crop_to_webp(url(encoded_image(fmt)), {"x": 0, "y": 0, "width": 12, "height": 12})
    with Image.open(io.BytesIO(result)) as image:
        assert image.format == "WEBP" and image.size == (512, 512)


def test_input_byte_boundary():
    assert len(_decode_data_url(url(b"a" * MAX_INPUT_BYTES))) == MAX_INPUT_BYTES
    with pytest.raises(InvalidFoodImage):
        _decode_data_url(url(b"a" * (MAX_INPUT_BYTES + 1)))


@pytest.mark.parametrize("raw", [b"not an image", encoded_image("GIF")])
def test_rejects_corrupt_or_disguised_content(raw):
    with pytest.raises(InvalidFoodImage):
        crop_to_webp(url(raw), {"x": 0, "y": 0, "width": 12, "height": 12})


def test_rejects_over_pixel_limit():
    raw = encoded_image("PNG", (2501, 2000))
    with pytest.raises(InvalidFoodImage, match="megapixels"):
        crop_to_webp(url(raw), {"x": 0, "y": 0, "width": 100, "height": 100})


def test_removes_exif_metadata():
    exif = Image.Exif()
    exif[270] = "synthetic private metadata"
    raw = encoded_image("JPEG", exif=exif)
    result = crop_to_webp(url(raw), {"x": 0, "y": 0, "width": 12, "height": 12})
    with Image.open(io.BytesIO(result)) as image:
        assert not image.getexif()
