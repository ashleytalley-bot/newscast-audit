# Newscast Audit — Web Application

A browser-based tool for analyzing newscast quality audit survey data from TEGNA broadcasting. Upload your Microsoft Forms Excel export and get instant analysis with interactive charts and exportable reports.

## Features

- **Drag-and-drop Excel upload** - No installation required, runs entirely in your browser
- **Comprehensive analysis** - Overall metrics, per-newscast breakdowns, weekly trends
- **Data quality tracking** - Completeness metrics to identify gaps
- **Export options** - Download results as Excel workbook or PowerPoint presentation
- **Privacy-first** - All processing happens client-side; your data never leaves your computer

## Quick Start

### Live Web App

Visit the live site: **https://[your-username].github.io/newscast-audit/**

1. Open the site in your browser
2. Drag and drop your Microsoft Forms Excel export
3. View results: summary stats, tables, and interactive charts
4. Export to Excel or PowerPoint as needed

### Local Development

To test the web app locally:

```bash
cd docs
python3 -m http.server 8000
# Open http://localhost:8000 in your browser
```

## Project Structure

```
newscast-audit/
├── docs/                      # Web application (GitHub Pages)
│   ├── index.html            # Main web UI
│   ├── css/style.css         # TEGNA branding and styles
│   ├── js/app.js             # Client-side application logic
│   └── py/processing.py      # Main processing orchestrator
│
├── lib/                       # Shared Python library
│   ├── __init__.py           # Package exports
│   ├── config.py             # Configuration constants
│   ├── cleaners.py           # Data validation and cleaning
│   ├── builders.py           # Metric calculations
│   └── utils.py              # Helper functions
│
└── README.md                  # This file
```

## Technology Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Python Runtime**: Pyodide 0.24.1 (Python in WebAssembly)
- **Data Processing**: Pandas 2.3.3, NumPy
- **Visualization**: Plotly 5.24.1
- **Excel I/O**: SheetJS (client-side parsing)
- **PowerPoint Export**: PptxGenJS 3.12.0

## How It Works

1. **User uploads Excel file** - Parsed client-side with SheetJS
2. **Pyodide loads** - Python interpreter runs in browser via WebAssembly
3. **Data processing** - Python cleans, validates, and analyzes survey data
4. **Results rendered** - Interactive charts and tables displayed
5. **Export** - Generate Excel workbook or PowerPoint presentation

All processing happens in your browser - no server required, no data uploaded anywhere.

## Configuration

Edit configuration values in `lib/config.py`:

- **COLUMN_MAPPING** - Maps Excel columns to internal names
- **METRIC_COLUMNS** - The 10 audit questions tracked
- **THRESHOLDS** - Performance bands (80% good, 40% poor)
- **NEWSCAST_ORDER** - Timeslot sorting order
- **PALETTE** - TEGNA brand colors

## Development

### Modifying Processing Logic

The codebase uses a modular architecture:

- **lib/config.py** - Change constants, thresholds, color palette
- **lib/cleaners.py** - Modify data cleaning and normalization logic
- **lib/builders.py** - Adjust metric calculations
- **lib/utils.py** - Update helpers (formatting, sorting, JSON serialization)
- **docs/py/processing.py** - Orchestrates the pipeline (rarely needs changes)

### Testing Changes

1. Make changes to library files
2. Reload `http://localhost:8000` in browser
3. Upload a test Excel file
4. Verify results in browser console and UI

## GitHub Pages Deployment

The web app is automatically deployed from the `/docs` folder.

### Setup

1. Go to repository **Settings** > **Pages**
2. Under "Source", select **Deploy from a branch**
3. Select the `main` branch and `/docs` folder
4. Click Save
5. Site will be available at `https://[your-username].github.io/newscast-audit/`

### Updating

Simply commit and push changes to the `main` branch. GitHub Pages will automatically rebuild and deploy.

## Data Format

The app expects a Microsoft Forms Excel export with these columns:

- **Which newscast are you auditing?** - Free text newscast name
- **Date of newscast:** - Date of the audited newscast
- **10 audit question columns** - Yes/No/N/A responses

See `lib/config.py` for full column mapping.

## Metrics Tracked

The tool analyzes 10 editorial quality metrics:

1. Urgency and why now
2. Streaming teases every 30min
3. Streaming/mobile shorts usage
4. Maps & graphics within 30min
5. Clear weather story
6. Weather new/now/next focus
7. Audience ("you") language & call-to-action
8. Anchor shots & name supers
9. File video properly referenced
10. Local context & community stories

## Support

For issues or questions, please open a GitHub issue in this repository.

## License

Internal TEGNA tool - not for public distribution.
