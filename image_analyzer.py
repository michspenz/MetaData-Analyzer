"""
image_analyzer.py
-----------------
Forensic metadata extractor for image files (JPG, JPEG, PNG, TIFF).
Extracts EXIF data, GPS coordinates, and file system metadata.
"""

import os
import struct
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    raise ImportError("Pillow is required. Run: pip install Pillow")


def _convert_gps_coordinate(coord_tuple: tuple, ref: str) -> Optional[float]:
    """
    Convert GPS coordinate tuple (degrees, minutes, seconds) to decimal degrees.

    Args:
        coord_tuple: Tuple of (degrees, minutes, seconds) as rationals.
        ref: Cardinal direction reference ('N', 'S', 'E', 'W').

    Returns:
        Decimal degrees as float, or None on failure.
    """
    def _to_float(value):
        # Handle tuples like (num, den), fractions.Fraction, or plain numbers
        try:
            from fractions import Fraction
        except Exception:
            Fraction = None

        if value is None:
            return None
        # Pillow may return a rational as a tuple (num, den)
        if isinstance(value, tuple) and len(value) == 2:
            num, den = value
            try:
                return float(num) / float(den) if float(den) != 0 else None
            except Exception:
                return None
        # fractions.Fraction
        if Fraction is not None and isinstance(value, Fraction):
            try:
                return float(value)
            except Exception:
                return None
        # plain numeric
        try:
            return float(value)
        except Exception:
            return None

    try:
        d = _to_float(coord_tuple[0])
        m = _to_float(coord_tuple[1])
        s = _to_float(coord_tuple[2])
        if d is None or m is None or s is None:
            return None
        decimal = d + (m / 60.0) + (s / 3600.0)
        if ref in ("S", "W"):
            decimal = -decimal
        return round(decimal, 6)
    except (TypeError, ZeroDivisionError, IndexError):
        return None


def _extract_gps(exif_data: dict) -> dict:
    """
    Parse GPS IFD data from raw EXIF into a readable dict.

    Args:
        exif_data: Raw EXIF dictionary from Pillow.

    Returns:
        Dict with latitude, longitude, altitude, and timestamp if available.
    """
    gps_info = {}
    raw_gps = exif_data.get("GPSInfo")
    if not raw_gps:
        return gps_info

    decoded: dict[str, Any] = {}
    for tag_id, value in raw_gps.items():
        tag_name = GPSTAGS.get(tag_id, str(tag_id))
        decoded[tag_name] = value

    lat = _convert_gps_coordinate(
        decoded.get("GPSLatitude"), decoded.get("GPSLatitudeRef", "N")
    )
    lon = _convert_gps_coordinate(
        decoded.get("GPSLongitude"), decoded.get("GPSLongitudeRef", "E")
    )

    if lat is not None:
        gps_info["latitude"] = lat
    if lon is not None:
        gps_info["longitude"] = lon

    alt_raw = decoded.get("GPSAltitude")
    if alt_raw is not None:
        try:
            gps_info["altitude_m"] = round(float(alt_raw), 2)
        except (TypeError, ZeroDivisionError):
            pass

    gps_timestamp = decoded.get("GPSTimeStamp")
    gps_datestamp = decoded.get("GPSDateStamp")
    if gps_timestamp and gps_datestamp:
        try:
            h, m, s = [float(x) for x in gps_timestamp]
            gps_info["gps_timestamp"] = f"{gps_datestamp} {int(h):02d}:{int(m):02d}:{int(s):02d} UTC"
        except Exception:
            gps_info["_error"] = "Failed to parse GPS timestamp/date"

    return gps_info


def analyze_image(file_path: str) -> dict:
    """
    Extract comprehensive forensic metadata from an image file.

    Args:
        file_path: Absolute or relative path to the image file.

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
        "type": "image",
        "format": None,
        "mode": None,
        "width_px": None,
        "height_px": None,
        "resolution_dpi": None,
        "creation_date": None,
        "modification_date": None,
        "camera_make": None,
        "camera_model": None,
        "lens_model": None,
        "software": None,
        "orientation": None,
        "exposure_time": None,
        "f_number": None,
        "iso_speed": None,
        "focal_length_mm": None,
        "flash": None,
        "color_space": None,
        "gps": {},
        "exif_version": None,
        "errors": [],
    }

    # File system metadata
    try:
        stat = path.stat()
        result["file_size_bytes"] = stat.st_size
        result["file_size_kb"] = round(stat.st_size / 1024, 2)
        result["modification_date"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        # st_birthtime on macOS/Windows; st_ctime is creation on Windows, change on Linux
        if hasattr(stat, "st_birthtime"):
            result["creation_date"] = datetime.fromtimestamp(stat.st_birthtime).isoformat()
        else:
            result["creation_date"] = datetime.fromtimestamp(stat.st_ctime).isoformat()
    except OSError as e:
        result["errors"].append(f"File stat error: {e}")

    # Image and EXIF metadata
    try:
        with Image.open(path) as img:
            result["format"] = img.format
            result["mode"] = img.mode
            result["width_px"] = img.width
            result["height_px"] = img.height

            dpi = img.info.get("dpi")
            if dpi:
                result["resolution_dpi"] = f"{dpi[0]} x {dpi[1]}"

            # Try to get EXIF via getexif() (Pillow >= 6)
            exif_raw = None
            try:
                exif_raw = img.getexif()
            except AttributeError:
                pass

            if exif_raw:
                exif_data: dict[str, Any] = {}
                for tag_id, value in exif_raw.items():
                    tag_name = TAGS.get(tag_id, str(tag_id))
                    exif_data[tag_name] = value

                result["camera_make"] = exif_data.get("Make")
                result["camera_model"] = exif_data.get("Model")
                result["lens_model"] = exif_data.get("LensModel")
                result["software"] = exif_data.get("Software")
                result["orientation"] = exif_data.get("Orientation")
                result["exif_version"] = exif_data.get("ExifVersion")
                result["color_space"] = exif_data.get("ColorSpace")

                # Dates from EXIF override filesystem dates when available
                dt_original = exif_data.get("DateTimeOriginal") or exif_data.get("DateTime")
                if dt_original:
                    result["creation_date"] = dt_original

                # Exposure details
                et = exif_data.get("ExposureTime")
                if et is not None:
                    try:
                        result["exposure_time"] = f"1/{round(1 / float(et))}s" if float(et) < 1 else f"{float(et)}s"
                    except (ZeroDivisionError, TypeError):
                        result["exposure_time"] = str(et)

                fn = exif_data.get("FNumber")
                if fn is not None:
                    try:
                        result["f_number"] = f"f/{float(fn)}"
                    except TypeError:
                        result["f_number"] = str(fn)

                result["iso_speed"] = exif_data.get("ISOSpeedRatings")

                fl = exif_data.get("FocalLength")
                if fl is not None:
                    try:
                        result["focal_length_mm"] = f"{float(fl)}mm"
                    except TypeError:
                        result["focal_length_mm"] = str(fl)

                flash_val = exif_data.get("Flash")
                if flash_val is not None:
                    result["flash"] = "Fired" if flash_val & 0x1 else "Did not fire"

                # GPS
                gps = _extract_gps(exif_data)
                # Move any GPS parsing errors into the top-level errors list
                gps_err = gps.pop("_error", None) if isinstance(gps, dict) else None
                if gps_err:
                    result["errors"].append(f"GPS parse error: {gps_err}")
                result["gps"] = gps

    except Exception as e:
        result["errors"].append(f"Image processing error: {e}")

    return result
