#!/bin/bash
# -----------------------------------------------------------------------------
# Static Type Checker Script
# -----------------------------------------------------------------------------
# Checks the application's Python code for type safety using Mypy.
#
# This script is automatically run by the `.git/hooks/pre-commit` hook
# before every commit. If it fails, the commit is aborted.
#
# Usage: ./check_types.sh
# Check Rules: Configured in `mypy.ini`
#
# Target Directories:
# - docs/lib: Shared library code (cleaners, builders, config)
# - docs/py/pipeline: Modular pipeline steps (Clean, Aggregate, etc.)

python3 build.py
python3 -m mypy docs/lib docs/py/pipeline
