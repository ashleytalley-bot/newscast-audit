"""
Bootstrap module for Newscast Audit App.

This module handles the initialization of the Python environment within Pyodide,
specifically fetching assets (Python files, configs) from the web server and
installing them into the local virtual filesystem.
"""

import os
import json
import time
from pyodide.http import pyfetch

async def install_assets(manifest_path: str = "py-files.json") -> None:
    """
    Fetch the manifest and install all listed files into the Pyodide filesystem.
    
    Args:
        manifest_path: Path to the JSON manifest relative to the web root.
    """
    print(f"Bootstrap: Fetching manifest from {manifest_path}...")
    
    # Add cache-busting for manifest
    timestamp = int(time.time())
    manifest_url = f"{manifest_path}?t={timestamp}"
    
    response = await pyfetch(manifest_url)
    if not response.ok:
        raise RuntimeError(f"Failed to fetch manifest: {response.status} {response.status_text}")
    
    files = await response.json()
    print(f"Bootstrap: Found {len(files)} files in manifest.")
    
    for file_path in files:
        # Create parent directories
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
            
        # Fetch file content with cache busting
        file_url = f"{file_path}?t={timestamp}"
        
        # print(f"Bootstrap: Installing {file_path}...")
        file_res = await pyfetch(file_url)
        
        if not file_res.ok:
             print(f"Warning: Failed to fetch {file_path}: {file_res.status}")
             continue
             
        # Read content (text)
        # Note: If we ever have binary files, we need to check extension and use .bytes()
        try:
            content = await file_res.string()
            
            # Write to FS
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            
    print("Bootstrap: Asset installation complete.")
