#!/usr/bin/env python3
"""
Build script for Newscast Audit App.

This script:
1. Scans docs/lib and docs/py for Python files → docs/py-files.json
2. Scans docs/config for YAML files → docs/config-files.json

The frontend uses these manifests to know which files to download into 
the browser's virtual filesystem (Pyodide).

Usage:
    python3 build.py
"""
import os
import json
from pathlib import Path

# Configuration
DOCS_DIR = Path("docs")
PY_OUTPUT_FILE = DOCS_DIR / "py-files.json"
CONFIG_OUTPUT_FILE = DOCS_DIR / "config-files.json"
DOCS_CONFIG_DIR = DOCS_DIR / "config"
DIRS_TO_SCAN = ["lib", "py"]

def build_python_manifest():
    """Build manifest of Python files."""
    print("=" * 60)
    print("STEP 1: Scanning for Python files...")
    print("=" * 60)

    file_list = []

    for subdir in DIRS_TO_SCAN:
        target_dir = DOCS_DIR / subdir
        if not target_dir.exists():
            print(f"Warning: Directory {target_dir} not found.")
            continue

        # Walk through directory
        for path in target_dir.rglob("*.py"):
            # Get path relative to docs/
            rel_path = path.relative_to(DOCS_DIR)
            path_str = str(rel_path).replace("\\", "/")

            # Skip __pycache__
            if "__pycache__" in path_str:
                continue

            file_list.append(path_str)
            print(f"  Found: {path_str}")

    # Sort for deterministic output
    file_list.sort()

    # Write manifest
    with open(PY_OUTPUT_FILE, "w") as f:
        json.dump(file_list, f, indent=2)

    print(f"\n✓ Generated {PY_OUTPUT_FILE}")
    print(f"  Total Python files: {len(file_list)}\n")
    return len(file_list)




def build_config_manifest():
    """Build manifest of config files."""
    print("=" * 60)
    print("STEP 2: Building config file manifest...")
    print("=" * 60)

    if not DOCS_CONFIG_DIR.exists():
        print(f"Warning: {DOCS_CONFIG_DIR} not found - skipping manifest")
        return 0

    config_list = []

    # Find all YAML files
    for path in DOCS_CONFIG_DIR.rglob("*.yaml"):
        rel_path = path.relative_to(DOCS_DIR)
        path_str = str(rel_path).replace("\\", "/")
        config_list.append(path_str)
        print(f"  Found: {path_str}")

    # Sort for deterministic output
    config_list.sort()

    # Write manifest
    with open(CONFIG_OUTPUT_FILE, "w") as f:
        json.dump(config_list, f, indent=2)

    print(f"\n✓ Generated {CONFIG_OUTPUT_FILE}")
    print(f"  Total config files: {len(config_list)}\n")
    return len(config_list)


def main():
    print("\n" + "=" * 60)
    print("NEWSCAST AUDIT - BUILD SCRIPT")
    print("=" * 60 + "\n")

    py_count = build_python_manifest()
    config_count = build_config_manifest()

    print("=" * 60)
    print("BUILD SUMMARY")
    print("=" * 60)
    print(f"Python files:  {py_count}")
    print(f"Config files:  {config_count}")
    print(f"Manifest files: 2")
    print("=" * 60)
    print("✓ Build complete!\n")

if __name__ == "__main__":
    main()
