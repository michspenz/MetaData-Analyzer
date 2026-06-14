#!/usr/bin/env python3
"""
analyzer.py
-----------
Metadata Analyzer — Forensic CLI Tool
======================================
Extracts and reports metadata from images (JPG, PNG, TIFF) and
documents (PDF, DOCX) for digital forensics investigations.

Usage:
    python analyzer.py <file>           # Analyze a single file
    python analyzer.py <folder/>        # Analyze all supported files in folder
    python analyzer.py <file> --json    # Also save individual JSON report
    python analyzer.py <folder/> --csv  # Save combined CSV report (default for folders)
    python analyzer.py --help           # Show this help message

Examples:
    python analyzer.py image.jpg
    python analyzer.py document.pdf
    python analyzer.py report.docx
    python analyzer.py evidence_folder/
    python analyzer.py image.jpg --json
    python analyzer.py evidence/ --csv --json
"""

import argparse
import sys
import os
from pathlib import Path

# ── Supported file types ────────────────────────────────────────────────────
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
PDF_EXTENSIONS   = {".pdf"}
DOCX_EXTENSIONS  = {".docx"}
ALL_SUPPORTED    = IMAGE_EXTENSIONS | PDF_EXTENSIONS | DOCX_EXTENSIONS

BANNER = r"""
 __  __      _            _       _            _
|  \/  | ___| |_ __ _  __| | __ _| |_ __ _   / \   _ __   __ _| |_   _ _______ _ __
| |\/| |/ _ \ __/ _` |/ _` |/ _` | __/ _` | / _ \ | '_ \ / _` | | | | |_  / _ \ '__|
| |  | |  __/ || (_| | (_| | (_| | || (_| |/ ___ \| | | | (_| | | |_| |/ /  __/ |
|_|  |_|\___|\__\__,_|\__,_|\__,_|\__\__,_/_/   \_\_| |_|\__,_|_|\__, /___\___|_|
                                                                    |___/
          Forensic Metadata Extraction Tool  |  Digital Forensics Portfolio
"""


def _detect_file_type(path: Path) -> str:
    """Return 'image', 'pdf', 'docx', or 'unsupported'."""
    ext = path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in PDF_EXTENSIONS:
        return "pdf"
    if ext in DOCX_EXTENSIONS:
        return "docx"
    return "unsupported"


def _analyze_single(path: Path) -> dict:
    """
    Dispatch analysis to the correct module based on file type.

    Args:
        path: Resolved Path object pointing to the file.

    Returns:
        Metadata dictionary, or an error dict if the type is unsupported.
    """
    file_type = _detect_file_type(path)

    if file_type == "image":
        from image_analyzer import analyze_image
        return analyze_image(str(path))

    if file_type == "pdf":
        from pdf_analyzer import analyze_pdf
        return analyze_pdf(str(path))

    if file_type == "docx":
        from docx_analyzer import analyze_docx
        return analyze_docx(str(path))

    return {
        "file_name": path.name,
        "file_path": str(path),
        "type": "unsupported",
        "errors": [f"File extension '{path.suffix}' is not supported."],
    }


def _collect_files(target: Path) -> list[Path]:
    """
    Collect all supported files from a directory (non-recursive).

    Args:
        target: Path to directory.

    Returns:
        Sorted list of supported file Paths.
    """
    return sorted(
        p for p in target.iterdir()
        if p.is_file() and p.suffix.lower() in ALL_SUPPORTED
    )


def main() -> None:
    print(BANNER)

    parser = argparse.ArgumentParser(
        prog="analyzer.py",
        description="Forensic metadata analysis tool for images and documents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "target",
        help="File or folder to analyze.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Save JSON report(s) to the reports/ directory.",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Save a CSV summary to the reports/ directory (auto-enabled for folders).",
    )
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Suppress pretty-print output to stdout.",
    )

    args = parser.parse_args()
    target = Path(args.target).resolve()

    # ── Validate target ──────────────────────────────────────────────────────
    if not target.exists():
        print(f"[ERROR] Path does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    from report_generator import (
        print_metadata_table,
        generate_json_report,
        generate_bulk_json_report,
        generate_csv_report,
    )

    results: list[dict] = []

    # ── Single file ──────────────────────────────────────────────────────────
    if target.is_file():
        print(f"[*] Analyzing: {target.name}")
        metadata = _analyze_single(target)
        results.append(metadata)

        if not args.no_print:
            print_metadata_table(metadata)

        if args.json:
            report_path = generate_json_report(metadata)
            print(f"[+] JSON report saved: {report_path}")

        if args.csv:
            csv_path = generate_csv_report(results)
            print(f"[+] CSV report saved:  {csv_path}")

    # ── Directory ────────────────────────────────────────────────────────────
    elif target.is_dir():
        files = _collect_files(target)

        if not files:
            print(f"[!] No supported files found in: {target}")
            print(f"    Supported extensions: {', '.join(sorted(ALL_SUPPORTED))}")
            sys.exit(0)

        print(f"[*] Found {len(files)} supported file(s) in: {target}\n")

        for i, file_path in enumerate(files, start=1):
            print(f"[{i}/{len(files)}] Analyzing: {file_path.name}")
            metadata = _analyze_single(file_path)
            results.append(metadata)

            if not args.no_print:
                print_metadata_table(metadata)

            if args.json:
                report_path = generate_json_report(metadata)
                print(f"    [+] JSON: {report_path}")

        # CSV is auto-generated for folder analysis
        csv_path = generate_csv_report(results)
        print(f"\n[+] CSV summary saved:  {csv_path}")

        bulk_path = generate_bulk_json_report(results)
        print(f"[+] Bulk JSON saved:    {bulk_path}")

    else:
        print(f"[ERROR] Target is neither a file nor a directory: {target}", file=sys.stderr)
        sys.exit(1)

    print(f"\n[✓] Analysis complete. {len(results)} file(s) processed.")


if __name__ == "__main__":
    main()
