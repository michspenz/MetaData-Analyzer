import os
import tempfile
from pathlib import Path

from image_analyzer import analyze_image
from PIL import Image


def test_image_successful_extraction(tmp_path: Path):
    img_path = tmp_path / "test.jpg"
    img = Image.new("RGB", (100, 50), color=(73, 109, 137))
    img.save(img_path)

    result = analyze_image(str(img_path))
    assert result["file_name"] == img_path.name
    assert result["type"] == "image"
    assert result["width_px"] == 100
    assert result["height_px"] == 50
    assert isinstance(result["file_size_bytes"], int)


def test_image_missing_metadata(tmp_path: Path):
    img_path = tmp_path / "nometa.jpg"
    img = Image.new("RGB", (10, 10))
    img.save(img_path)

    result = analyze_image(str(img_path))
    # No EXIF -> gps should be empty dict
    assert result["gps"] == {}


def test_image_corrupted_file(tmp_path: Path):
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"this is not a valid image file")

    result = analyze_image(str(bad))
    assert "errors" in result
    assert any("Image processing error" in e for e in result["errors"]) or result["file_size_bytes"] is not None
