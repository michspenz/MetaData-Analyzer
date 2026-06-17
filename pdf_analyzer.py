"""
pdf_analyzer.py
---------------
Forensic metadata extractor for PDF documents.
Extracts document properties, authorship, and creation tool chain.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from analysis_utils import calculate_entropy, calculate_file_hashes, detect_mime_type, entropy_flag

try:
    import PyPDF2
except ImportError:
    raise ImportError("PyPDF2 is required. Run: pip install PyPDF2")


def _parse_pdf_date(date_str: Optional[str]) -> Optional[str]:
    """
    Normalize PDF date string (D:YYYYMMDDHHmmSSOHH'mm') to ISO 8601.

    Args:
        date_str: Raw PDF date string or None.

    Returns:
        ISO 8601 formatted datetime string or the original string on failure.
    """
    if not date_str:
        return None

    # Decode bytes if necessary
    if isinstance(date_str, bytes):
        try:
            date_str = date_str.decode("utf-8", errors="replace")
        except Exception:
            return None

    cleaned = date_str.strip()
    if cleaned.startswith("D:"):
        cleaned = cleaned[2:]

    # PDF date may include timezone as +HH'mm' or -HH'mm' or Z (UTC).
    # Normalize variants to a form parseable by datetime.
    try:
        # Remove apostrophes used in timezone markers
        cleaned = cleaned.replace("'", "")

        # If timezone is 'Z', convert to +0000
        if cleaned.endswith("Z"):
            cleaned = cleaned[:-1] + "+0000"

        # If timezone is like +HHmm or +HH:mm, normalize to +HHMM
        # Remove any trailing colon from timezone
        if (len(cleaned) >= 5) and (cleaned[-3] == ":") and (cleaned[-6] in "+-"):
            # e.g. 20200101123000+01:00 -> 20200101123000+0100
            cleaned = cleaned[:-3]

        # Try parsing with timezone first
        fmts = [
            ("%Y%m%d%H%M%S%z", 14),
            ("%Y%m%d%H%M%S", 14),
            ("%Y%m%d%H%M", 12),
            ("%Y%m%d", 8),
        ]

        for fmt, length in fmts:
            try:
                part = cleaned[: length + (5 if fmt.endswith("%z") and len(cleaned) > length else 0)]
                dt = datetime.strptime(part, fmt)
                return dt.isoformat()
            except ValueError:
                continue
    except Exception:
        # Fall back to returning the raw string when parsing fails
        return date_str

    return date_str


def analyze_pdf(file_path: str) -> dict:
    """
    Extract comprehensive forensic metadata from a PDF file.

    Args:
        file_path: Absolute or relative path to the PDF.

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
        "type": "pdf",
        "mime_type": None,
        "md5_hash": None,
        "sha256_hash": None,
        "entropy": None,
        "entropy_flag": "NORMAL",
        "title": None,
        "author": None,
        "creator": None,
        "producer": None,
        "subject": None,
        "keywords": None,
        "creation_date": None,
        "modification_date": None,
        "num_pages": None,
        "pdf_version": None,
        "is_encrypted": False,
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
        with open(path, "rb") as fh:
            reader = PyPDF2.PdfReader(fh)

            result["is_encrypted"] = reader.is_encrypted

            if reader.is_encrypted:
                # Attempt decryption with empty password (many PDFs use this)
                try:
                    reader.decrypt("")
                except Exception:
                    result["errors"].append("PDF is encrypted and could not be decrypted.")
                    return result

            result["num_pages"] = len(reader.pages)

            # PDF version from the header
            try:
                result["pdf_version"] = reader.pdf_header
            except AttributeError:
                pass

            meta = reader.metadata
            if meta:
                result["title"] = meta.get("/Title") or meta.get("Title")
                result["author"] = meta.get("/Author") or meta.get("Author")
                result["creator"] = meta.get("/Creator") or meta.get("Creator")
                result["producer"] = meta.get("/Producer") or meta.get("Producer")
                result["subject"] = meta.get("/Subject") or meta.get("Subject")
                result["keywords"] = meta.get("/Keywords") or meta.get("Keywords")

                raw_created = meta.get("/CreationDate") or meta.get("CreationDate")
                raw_modified = meta.get("/ModDate") or meta.get("ModDate")

                result["creation_date"] = _parse_pdf_date(raw_created)
                result["modification_date"] = _parse_pdf_date(raw_modified)

    except PyPDF2.errors.PdfReadError as e:
        result["errors"].append(f"PDF read error (possibly corrupted): {e}")
    except Exception as e:
        result["errors"].append(f"Unexpected error: {e}")

    return result
