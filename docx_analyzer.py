"""
docx_analyzer.py
----------------
Forensic metadata extractor for Microsoft Word (.docx) documents.
Surfaces authorship, revision history, and timestamps embedded in
the Open XML core properties.
"""

from pathlib import Path
from typing import Any, Optional

from analysis_utils import calculate_entropy, calculate_file_hashes, detect_mime_type, entropy_flag

try:
    from docx import Document
    from docx.opc.exceptions import PackageNotFoundError
except ImportError:
    raise ImportError("python-docx is required. Run: pip install python-docx")


def _safe_str(value: Any) -> Optional[str]:
    """
    Convert a value to string, returning None for empty or None values.

    Args:
        value: Any value to convert.

    Returns:
        Stripped string or None.
    """
    if value is None:
        return None
    result = str(value).strip()
    return result if result else None


def analyze_docx(file_path: str) -> dict:
    """
    Extract comprehensive forensic metadata from a DOCX file.

    Args:
        file_path: Absolute or relative path to the .docx file.

    Returns:
        Dictionary containing all extracted metadata fields.
    """
    path = Path(file_path).resolve()
    result: dict[str, Any] = {
        "file_name": path.name,
        "file_path": str(path),
        "file_size_bytes": None,
        "file_size_kb": None,
        "file_extension": path.suffix.lower(),
        "type": "docx",
        "mime_type": None,
        "md5_hash": None,
        "sha256_hash": None,
        "entropy": None,
        "entropy_flag": "NORMAL",
        "title": None,
        "subject": None,
        "author": None,
        "last_modified_by": None,
        "description": None,
        "keywords": None,
        "category": None,
        "creation_date": None,
        "modification_date": None,
        "last_printed": None,
        "revision_number": None,
        "word_count": None,
        "paragraph_count": None,
        "character_count": None,
        "application": None,
        "app_version": None,
        "errors": [],
    }

    # File system metadata
    try:
        stat = path.stat()
        result["file_size_bytes"] = stat.st_size
        result["file_size_kb"] = round(stat.st_size / 1024, 2)
        result["md5_hash"], result["sha256_hash"] = calculate_file_hashes(path)
        result["entropy"] = calculate_entropy(path)
        result["entropy_flag"] = entropy_flag(result["entropy"])
        result["mime_type"] = detect_mime_type(path)
    except OSError as e:
        result["errors"].append(f"File stat error: {e}")

    try:
        doc = Document(str(path))

        # Core properties (Dublin Core + OPC)
        core = doc.core_properties
        result["title"] = _safe_str(getattr(core, "title", None))
        result["subject"] = _safe_str(getattr(core, "subject", None))
        result["author"] = _safe_str(getattr(core, "author", None))
        result["last_modified_by"] = _safe_str(getattr(core, "last_modified_by", None))
        result["description"] = _safe_str(getattr(core, "description", None))
        result["keywords"] = _safe_str(getattr(core, "keywords", None))
        result["category"] = _safe_str(getattr(core, "category", None))
        result["revision_number"] = _safe_str(getattr(core, "revision", None))

        created = getattr(core, "created", None)
        modified = getattr(core, "modified", None)
        last_printed = getattr(core, "last_printed", None)

        if created:
            result["creation_date"] = created.isoformat()
        if modified:
            result["modification_date"] = modified.isoformat()
        if last_printed:
            result["last_printed"] = last_printed.isoformat()

        # Extended properties (word count, app name, etc.)
        try:
            ext = doc.element.body.getroottree().getroot()
            # python-docx exposes extended props through the part
            app_part = doc.part.package.part_related_by(
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties"
            )
            if app_part:
                import xml.etree.ElementTree as ET
                tree = ET.fromstring(app_part.blob)
                ns = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
                words = tree.find(f"{{{ns}}}Words")
                paragraphs = tree.find(f"{{{ns}}}Paragraphs")
                chars = tree.find(f"{{{ns}}}Characters")
                app_name = tree.find(f"{{{ns}}}Application")
                app_ver = tree.find(f"{{{ns}}}AppVersion")

                result["word_count"] = int(words.text) if words is not None and words.text else None
                result["paragraph_count"] = int(paragraphs.text) if paragraphs is not None and paragraphs.text else None
                result["character_count"] = int(chars.text) if chars is not None and chars.text else None
                result["application"] = app_name.text if app_name is not None else None
                result["app_version"] = app_ver.text if app_ver is not None else None
        except Exception as e:
            result["errors"].append(f"Extended properties parse error: {e}")

    except PackageNotFoundError:
        result["errors"].append("File is not a valid .docx package (possibly corrupted or renamed).")
    except Exception as e:
        result["errors"].append(f"Unexpected error: {e}")

    return result
