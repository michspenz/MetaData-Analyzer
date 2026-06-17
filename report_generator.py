"""
report_generator.py
-------------------
Generates JSON and CSV forensic reports from metadata analysis results.
All reports are saved to the /reports directory automatically.
"""

import csv
import html
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


def _render_value(value: Any) -> str:
    if value is None or value == "" or value == {}:
        return "<span class=\"empty\">[not found]</span>"
    return html.escape(str(value))


def _render_gps_link(gps: dict) -> str:
    lat = gps.get("latitude")
    lon = gps.get("longitude")
    if lat is None or lon is None:
        return _render_value(gps or None)
    label = f"{lat}, {lon}"
    href = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    return f"<a href=\"{html.escape(href)}\" target=\"_blank\">{html.escape(label)}</a>"


def generate_html_report(results: list[dict], output_path: str | None = None) -> str:
    """
    Generate a self-contained HTML report from analysis results.

    Args:
        results: List of metadata dictionaries.
        output_path: Optional explicit output file path.

    Returns:
        Absolute path to the written HTML file.
    """
    _ensure_reports_dir()

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(REPORTS_DIR / f"report_{timestamp}.html")

    rows = []
    for metadata in results:
        flat = _flatten_dict(metadata)
        row_cells = []
        for key, value in flat.items():
            if key == "errors":
                continue
            if key == "gps":
                cell = _render_gps_link(value)
            elif key in {"md5_hash", "sha256_hash"}:
                cell = f"<code>{html.escape(str(value))}</code>"
            else:
                cell = _render_value(value)
            row_cells.append((html.escape(key), cell))

        rows.append((html.escape(metadata.get("file_name", "unknown")), row_cells))

    html_content = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>Metadata Analyzer Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#f7f9fb; color:#202124; margin:0; padding:20px; }}
    h1 {{ margin-bottom: 10px; }}
    .report-container {{ max-width: 1200px; margin: auto; }}
    .file-card {{ background: #fff; border: 1px solid #dde2e8; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
    .file-header {{ padding: 16px 20px; border-bottom: 1px solid #eceff1; background: #f5f7fa; }}
    .file-header h2 {{ margin: 0; font-size: 1.1rem; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid #e5e9ef; }}
    th {{ background: #fafbfc; color: #2f4f65; font-weight: 700; }}
    td span.empty {{ color: #7a7f8d; font-style: italic; }}
    td code {{ display: block; font-family: Consolas, Menlo, Monaco, monospace; background: #f2f5f8; padding: 4px 6px; border-radius: 4px; }}
    a {{ color: #1a73e8; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class=\"report-container\">
    <h1>Metadata Analyzer Report</h1>
    <p>Generated at {html.escape(datetime.now().isoformat())}</p>
"""

    for file_name, cells in rows:
        html_content += f"  <div class=\"file-card\">\n"
        html_content += f"    <div class=\"file-header\"><h2>{file_name}</h2></div>\n"
        html_content += "    <table>\n      <thead>\n        <tr><th>Field</th><th>Value</th></tr>\n      </thead>\n      <tbody>\n"
        for key, cell in cells:
            html_content += f"        <tr><td>{key}</td><td>{cell}</td></tr>\n"
        html_content += "      </tbody>\n    </table>\n  </div>\n"

    html_content += "  </div>\n</body>\n</html>"

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html_content)

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
