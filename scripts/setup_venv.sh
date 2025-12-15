#!/usr/bin/env bash
# Quick setup script for new contributors: create venv, install deps, register kernel
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -d .venv ]; then
  echo ".venv already exists — using existing virtual environment"
else
  echo "Creating virtual environment .venv..."
  python3 -m venv .venv
fi

echo "Activating .venv and installing dependencies..."
# shellcheck source=/dev/null
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Registering Jupyter kernel 'newscast-audit-venv'..."
.venv/bin/python -m ipykernel install --user --name=newscast-audit-venv --display-name "newscast-audit (.venv)"

echo
echo "Setup complete. To render the report run:"
echo "  source .venv/bin/activate"
echo "  quarto render opex-newscast-audit.qmd --to html"
