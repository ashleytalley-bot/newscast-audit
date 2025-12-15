#!/usr/bin/env bash
set -euo pipefail

# Render HTML (interactive) and Typst/PDF outputs from the Quarto report.
quarto render opex-newscast-audit-interactive.qmd --to html
quarto render opex-newscast-audit.qmd --to typst
