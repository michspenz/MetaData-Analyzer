# Metadata Analyzer
![CI](https://github.com/michspenz/MetaData-Analyzer/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> Forensic metadata extraction tool for images and documents. Built for DFIR investigations.

[Landing Page](https://michspenz.github.io/MetaData-Analyzer) · 
[Report Bug](https://github.com/michspenz/MetaData-Analyzer/issues) · 
[View Demo](#sample-output)

---

## What it does

Drop any image, PDF, or Word document into it and it extracts the hidden 
metadata layer — who created it, when, with what device, and where on Earth.

| Format | Key Fields Extracted |
|--------|---------------------|
| JPG / JPEG / PNG / TIFF | Camera make & model, GPS coordinates, exposure, ISO, focal length, EXIF strip detection, MD5/SHA256, entropy |
| PDF | Author, creator tool, producer, dates, page count, encryption status, MD5/SHA256, entropy |
| DOCX | Author, last modified by, revision number, application, dates, word count, MD5/SHA256, entropy |

**Output formats:** JSON · CSV · HTML (with clickable GPS map links)

---

## Installation

```bash
git clone https://github.com/michspenz/MetaData-Analyzer.git
cd MetaData-Analyzer
pip install -r requirements.txt
```

---

## Usage

```bash
# Single file
python analyzer.py photo.jpg
python analyzer.py document.pdf

# Entire folder
python analyzer.py evidence/

# With reports
python analyzer.py evidence/ --html --json --csv

# Recursive scan
python analyzer.py evidence/ --recursive
```

---
---

## Roadmap

- [ ] Timeline generation from timestamps
- [ ] Steganography detection (LSB analysis)
- [ ] Chain of custody audit log
- [ ] GUI version

---

## Disclaimer

For defensive and forensic use only. Only analyze files you own or 
have explicit authorization to examine.

---

**Michael Oscar** · [GitHub](https://github.com/michspenz) · 
[Twitter](https://x.com/kiing_vamp)

---
