# Newscast Audit — Quick start

These instructions make it easy for a new contributor to set up the project, register a Jupyter kernel tied to the project's virtual environment, and render the Quarto report.

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
