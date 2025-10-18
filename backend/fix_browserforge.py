"""
System: Suno Automation Backend
Module: Browserforge Fix
File URL: backend/fix_browserforge.py
Purpose: Download missing browserforge data files before starting the application
"""

import os
import sys
import urllib.request
from pathlib import Path

def fix_browserforge_data():
    """Download missing browserforge data files if they don't exist."""
    try:
        # Find browserforge installation path
        import site
        site_packages = site.getsitepackages()[0]
        browserforge_path = Path(site_packages) / "browserforge"

        if not browserforge_path.exists():
            print(f"[ERROR] Browserforge not found at {browserforge_path}")
            return False

        data_dir = browserforge_path / "headers" / "data"

        # Create data directory if it doesn't exist
        data_dir.mkdir(parents=True, exist_ok=True)

        # Check if input-network.zip exists
        input_network_path = data_dir / "input-network.zip"

        if not input_network_path.exists():
            print(f"[INFO] Downloading missing browserforge data file to {input_network_path}...")
            url = "https://github.com/daijro/browserforge/raw/main/browserforge/headers/data/input-network.zip"
            urllib.request.urlretrieve(url, str(input_network_path))
            print("[SUCCESS] Browserforge data file downloaded successfully")
        else:
            print("[INFO] Browserforge data files already present")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to fix browserforge data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if fix_browserforge_data():
        # Start the main application
        import main
        import uvicorn
        uvicorn.run(main.app, host="0.0.0.0", port=8000)
    else:
        print("[ERROR] Failed to initialize browserforge data files")
        sys.exit(1)