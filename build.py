#!/usr/bin/env python3
"""
Build script for Newscast Audit App.

This script scans the docs/lib and docs/py directories and generates 
a 'py-files.json' manifest in the docs directory. The frontend app.js
uses this manifest to know which Python files to load into Pyodide.

Usage:
    python3 build.py
"""
import os
import json
from pathlib import Path

# Configuration
DOCS_DIR = Path("docs")
OUTPUT_FILE = DOCS_DIR / "py-files.json"
DIRS_TO_SCAN = ["lib", "py"]

def main():
    print(f"Scanning for Python files in {DOCS_DIR}...")
    
    file_list = []
    
    for subdir in DIRS_TO_SCAN:
        target_dir = DOCS_DIR / subdir
        if not target_dir.exists():
            print(f"Warning: Directory {target_dir} not found.")
            continue
            
        # Walk through directory
        for path in target_dir.rglob("*.py"):
            # Get path relative to docs/
            # e.g. docs/lib/config.py -> lib/config.py
            rel_path = path.relative_to(DOCS_DIR)
            
            # Convert to string and force forward slashes for web consistency
            path_str = str(rel_path).replace("\\", "/")
            
            # Skip __init__ if you want, but actually Pyodide usually needs them for packages
            # We skip __pycache__ just in case rglob picked it up
            if "__pycache__" in path_str:
                continue
                
            file_list.append(path_str)
            print(f"  Found: {path_str}")

    # Sort for deterministic output
    file_list.sort()
    
    # Write manifest
    with open(OUTPUT_FILE, "w") as f:
        json.dump(file_list, f, indent=2)
        
    print(f"\nSuccessfully generated {OUTPUT_FILE}")
    print(f"Total files: {len(file_list)}")

if __name__ == "__main__":
    main()
