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
│   ├── config/             # YAML configuration files
│   ├── js/                 # TypeScript source and compiled JS modules
│   ├── lib/                # Shared Python logic (cleaners, builders, utils)
│   └── py/pipeline/        # Modular processing pipeline
│
├── tests/                  # E2E Playwright tests and Python unit tests
├── scripts/                # Build and maintenance scripts
├── check_types.sh          # Static type checking script (Mypy + TSC)
├── tsconfig.json           # TypeScript configuration
└── package.json            # Node dependencies and scripts
```

## Quick Start (Local Development)

### 1. Install Dependencies
```bash
npm install
pip install -r requirements-test.txt
```

### 2. Build and Type Check
This script compiles TypeScript, generates manifest files, and runs both Mypy and TSC.
```bash
./check_types.sh
```

### 3. Launch Server
```bash
npx http-server docs
```
Visit `http://localhost:8080` in your browser.

## Development

### Useful Commands
- `npm run build`: Compiles TS and generates Python/Config manifests.
- `npm test`: Runs Playwright E2E tests.
- `npm run watch`: Automatically rebuilds on file changes.
- `./check_types.sh`: Full validation (Build + Mypy + TSC).

## Deployment

The app is hosted via GitHub Pages from the `docs/` folder. A GitHub Action automatically builds and verifies every push to `main`. To manually prepare a deployment, ensure you have run `npm run build`.

---
**Internal TEGNA tool.** Not for public distribution.
