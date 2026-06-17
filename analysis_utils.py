"""
analysis_utils.py
----------------
Shared forensic utility helpers for hashing, entropy, and MIME detection.
"""

import hashlib
import math
import mimetypes
from pathlib import Path
from typing import Optional

try:
    import magic
except ImportError:  # pragma: no cover
    magic = None


def calculate_file_hashes(path: Path) -> tuple[str, str]:
    """Calculate MD5 and SHA256 hashes for a file."""
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()


def calculate_entropy(path: Path) -> float:
    """Return the Shannon entropy of a file in bits per byte."""
    with path.open("rb") as fh:
        data = fh.read()
    if not data:
        return 0.0

    freq = [0] * 256
    for byte in data:
        freq[byte] += 1

    entropy = 0.0
    length = len(data)
    for count in freq:
        if count:
            p = count / length
            entropy -= p * math.log2(p)
    return round(entropy, 4)


def entropy_flag(entropy_value: float) -> str:
    """Return an entropy flag for forensic interpretation."""
    return (
        "HIGH - possible encryption/compression"
        if entropy_value > 7.0
        else "NORMAL"
    )


def detect_mime_type(path: Path) -> str:
    """Detect the MIME type of a file using libmagic, falling back to mimetypes."""
    if magic is not None:
        try:
            mime = magic.from_file(str(path), mime=True)
            if isinstance(mime, str) and mime:
                return mime
        except Exception:
            pass

    guessed = mimetypes.guess_type(str(path))[0]
    return guessed or "application/octet-stream"
