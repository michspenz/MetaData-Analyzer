from pathlib import Path
from PIL import Image
from image_analyzer import analyze_image


def test_exif_stripped_on_jpeg_without_exif(tmp_path: Path):
    image_path = tmp_path / "no_exif.jpg"
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    img.save(image_path)

    result = analyze_image(str(image_path))
    assert result["type"] == "image"
    assert result["exif_stripped"] is True
    assert result["gps"] == {}
