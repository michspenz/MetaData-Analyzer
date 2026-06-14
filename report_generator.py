"""
report_generator.py
-------------------
Generates JSON and CSV forensic reports from metadata analysis results.
All reports are saved to the /reports directory automatically.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


REPORTS_DIR = Path(__file__).parent / "reports"


def _ensure_reports_dir() -> None:
    """Create the reports directory if it does not exist."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _flatten_dict(data: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    Recursively flatten a nested dictionary for CSV serialization.

    Args:
        data: Dictionary to flatten.
        parent_key: Prefix accumulated from parent keys.
        sep: Separator between key levels.

    Returns:
        Flat dictionary with dotted keys.
    """
    items: list[tuple[str, Any]] = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, "; ".join(str(i) for i in v)))
        else:
            items.append((new_key, v))
    return dict(items)


def generate_json_report(metadata: dict, output_path: str | None = None) -> str:
    """
    Serialize a single metadata result to a JSON file.

    Args:
        metadata: Dictionary returned by any analyzer.
        output_path: Optional explicit path. Auto-generated if None.

    Returns:
        Absolute path to the written JSON file.
    """
    _ensure_reports_dir()

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = Path(metadata.get("file_name", "unknown")).stem
        output_path = str(REPORTS_DIR / f"{safe_name}_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2, default=str)

    return output_path


def generate_bulk_json_report(results: list[dict], output_path: str | None = None) -> str:
    """
    Serialize multiple metadata results to a single JSON file.

    Args:
        results: List of metadata dictionaries.
        output_path: Optional explicit path. Auto-generated if None.

    Returns:
        Absolute path to the written JSON file.
    """
    _ensure_reports_dir()

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(REPORTS_DIR / f"bulk_report_{timestamp}.json")

    payload = {
        "generated_at": datetime.now().isoformat(),
        "total_files": len(results),
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)

    return output_path


def generate_csv_report(results: list[dict], output_path: str | None = None) -> str:
    """
    Write a flat CSV summary for all analyzed files.

    Args:
        results: List of metadata dictionaries (mixed types OK).
        output_path: Optional explicit path. Auto-generated if None.

    Returns:
        Absolute path to the written CSV file.
    """
    _ensure_reports_dir()

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(REPORTS_DIR / f"summary_{timestamp}.csv")

    flat_results = [_flatten_dict(r) for r in results]

    # Build a superset of all column names (preserving insertion order)
    all_keys: list[str] = []
    seen: set[str] = set()
    for row in flat_results:
        for k in row:
            if k not in seen:
                all_keys.append(k)
                seen.add(k)

    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        for row in flat_results:
            # Fill missing keys with empty string
            writer.writerow({k: row.get(k, "") for k in all_keys})

    return output_path


def print_metadata_table(metadata: dict) -> None:
    """
    Pretty-print metadata to stdout in a two-column table format.

    Args:
        metadata: Dictionary returned by any analyzer.
    """
    flat = _flatten_dict(metadata)
    max_key_len = max((len(k) for k in flat), default=20)
    width = max(max_key_len + 2, 30)

    print("\n" + "=" * 60)
    print(f"  FORENSIC METADATA — {metadata.get('file_name', 'Unknown')}")
    print("=" * 60)

    for key, value in flat.items():
        if key == "errors":
            continue
        if value is None or value == "" or value == {}:
            display = "[not found]"
        else:
            display = str(value)
        print(f"  {key:<{width}}  {display}")

    errors = metadata.get("errors", [])
    if errors:
        print("\n  WARNINGS / ERRORS:")
        for err in errors:
            print(f"    [!] {err}")

    print("=" * 60 + "\n")
