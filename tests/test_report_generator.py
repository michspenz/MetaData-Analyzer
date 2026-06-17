from pathlib import Path
from report_generator import generate_html_report


def test_generate_html_report(tmp_path: Path):
    results = [
        {
            "file_name": "test.txt",
            "file_path": str(tmp_path / "test.txt"),
            "mime_type": "text/plain",
            "md5_hash": "abc123",
            "sha256_hash": "def456",
            "entropy": 4.5,
            "entropy_flag": "NORMAL",
            "gps": {},
            "errors": [],
        }
    ]
    output_path = tmp_path / "report.html"
    written = generate_html_report(results, output_path=str(output_path))

    assert written == str(output_path)
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Metadata Analyzer Report" in content
    assert "md5_hash" in content
    assert "sha256_hash" in content
    assert "text/plain" in content
