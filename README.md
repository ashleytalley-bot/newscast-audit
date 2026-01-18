# Newscast Audit — Web Application

A browser-based tool for analyzing newscast quality audit survey data. Upload your Microsoft Forms Excel export and get instant analysis with interactive charts, summary tables, and exportable reports.

## Features

- **Zero Installation** - Runs entirely in the browser via Pyodide (Python in WebAssembly).
- **Comprehensive Analysis** - Overall metrics, per-newscast breakdowns, and volume stats.
- **Dynamic Configuration** - YAML-driven settings for stations, surveys, and name normalization.
- **Enhanced Error Handling** - Rich UI with actionable guidance for data quality issues.
- **Export Options** - Download results as Excel workbooks or PowerPoint presentations.
- **Privacy-First** - Data processing happens locally on your machine; no data is ever uploaded.

## Directory Structure

```text
newscast-audit/
├── docs/                   # Web Application (Deployed to GitHub Pages)
│   ├── index.html          # Main UI entry point
│   ├── config/             # YAML configuration files (Station, Survey, Patterns)
│   ├── js/                 # JavaScript (app.js logic, error-ui components)
│   ├── css/                # Styles (branding, layout, error UI)
│   ├── lib/                # Shared Python logic (cleaners, builders, utils)
│   └── py/pipeline/        # Modular processing pipeline (orchestrator, steps)
│
├── tests/                  # Pytest suite for backend logic
├── build.py                # Manifest generator for frontend assets
├── check_types.sh          # Static type checking script (Mypy)
├── mypy.ini                # Mypy configuration
└── requirements-test.txt   # Development dependencies
```

## Quick Start (Local Development)

### 1. Build Manifests
The frontend needs a manifest of all Python and config files to load them into the browser. Run this whenever you add or remove files:
```bash
python3 build.py
```

### 2. Launch Server
```bash
cd docs
python3 -m http.server 8000
```
Visit `http://localhost:8000` in your browser.

## Configuration

The application is driven by YAML files in `docs/config/`:

- **`stations/default.yaml`**: Station names, timezones, and performance thresholds.
- **`surveys/newscast-audit-v1.yaml`**: Column mappings and metric definitions.
- **`normalization/newscast-patterns.yaml`**: Regex patterns for newscast time normalization.

## Development & Quality

### Maintenance Scripts
- **`./check_types.sh`**: Runs Mypy across the library and pipeline.
- **`python3 build.py`**: Updates `py-files.json` and `config-files.json` manifests.

### Automated Checks
A Git pre-commit hook is installed to automatically run `check_types.sh` before every commit. To install dependencies for local development:
```bash
pip install -r requirements-test.txt
```

### Running Tests
```bash
python3 -m pytest tests/
```

## Deployment

The app is hosted via GitHub Pages from the `docs/` folder. Simply push to `main` to deploy changes. Ensure you have run `python3 build.py` if you have added new Python or YAML files.

---
**Internal TEGNA tool.** Not for public distribution.
