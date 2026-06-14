from pathlib import Path
from pdf_analyzer import analyze_pdf
from PyPDF2 import PdfWriter


def test_pdf_successful_extraction(tmp_path: Path):
    out = tmp_path / "simple.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with open(out, "wb") as fh:
        writer.write(fh)

    result = analyze_pdf(str(out))
    assert result["file_name"] == out.name
    assert result["type"] == "pdf"
    assert result["num_pages"] == 1


def test_pdf_missing_metadata(tmp_path: Path):
    out = tmp_path / "nometa.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with open(out, "wb") as fh:
        writer.write(fh)

    result = analyze_pdf(str(out))
    # metadata fields may be None or empty; ensure no crash and errors list present
    assert "errors" in result


def test_pdf_corrupted_file(tmp_path: Path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf")

    result = analyze_pdf(str(bad))
    assert "errors" in result
    assert any("PDF read error" in e or "Unexpected error" in e for e in result["errors"]) or result.get("is_encrypted") is not None
