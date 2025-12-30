# Newscast Audit — Quick start

These instructions make it easy for a new contributor to set up the project, register a Jupyter kernel tied to the project's virtual environment, and render the Quarto report.

## Web App (GitHub Pages)

A web-based version is available that allows you to upload Excel files and generate reports directly in the browser:

**Live Site:** https://[your-username].github.io/newscast-audit/

### Features
- Drag-and-drop Excel file upload
- All charts from the Quarto report (overall, per-newscast, weekly trends)
- Data quality tables
- Download Excel export
- Download PowerPoint slides

### GitHub Pages Setup

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Pages**
3. Under "Source", select **Deploy from a branch**
4. Select the `main` branch and `/docs` folder
5. Click Save
6. Your site will be available at `https://[your-username].github.io/newscast-audit/`

### Local Testing

To test the web app locally:

```bash
cd docs
python3 -m http.server 8000
# Open http://localhost:8000 in your browser
```

---

## Quarto Report

1) Create virtual environment, install dependencies, and register kernel (recommended):

```bash
# from repo root
./scripts/setup_venv.sh
```

2) Activate the venv and render the report:

```bash
source .venv/bin/activate
quarto render opex-newscast-audit.qmd --to html
```

Notes:
- The setup script installs packages listed in `requirements.txt` and registers a Jupyter kernel named `newscast-audit-venv`.
- If you prefer Conda, create a conda env, install the same packages, then register the kernel with:

```bash
python -m ipykernel install --user --name=newscast-audit-venv --display-name "newscast-audit (conda)"
```

- Avoid installing packages system-wide; using a virtual environment keeps dependencies isolated.

PDF rendering notes:
- Quarto can render to PDF, but a LaTeX engine is required (TinyTeX, MacTeX, or TeX Live).
- To render a PDF locally, install TinyTeX (recommended for minimal install):

```bash
R -e "install.packages('tinytex'); tinytex::install_tinytex()"
```

or install MacTeX on macOS from: https://tug.org/mactex/

Then render:

```bash
source .venv/bin/activate
quarto render opex-newscast-audit.qmd --to pdf
```

We've added a `Makefile` target `make pdf` to simplify this.

If you want, I can also add a small `Makefile` with targets for `setup` and `render`.
