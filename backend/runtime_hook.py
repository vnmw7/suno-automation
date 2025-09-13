"""
System: Suno Automation
Module: Runtime Hook
Purpose: Initialize Camoufox browser during runtime for bundled executable
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_camoufox():
    """Setup Camoufox browser paths for bundled executable"""
    try:
        import camoufox

        # Get the path where the bundled app is running
        if getattr(sys, 'frozen', False):
            # Running as bundled executable
            app_dir = Path(sys.executable).parent

            # PRIORITY 1: Check for bundled .camoufox directory (distributed with exe)
            bundled_camoufox = app_dir / ".camoufox"
            if bundled_camoufox.exists():
                # Use bundled browser - this is the preferred path for distribution
                os.environ['CAMOUFOX_CACHE_DIR'] = str(bundled_camoufox)
                print(f"✓ Using bundled Camoufox browser (ready to run)")
            else:
                # PRIORITY 2: Try to create and fetch browser in app directory
                print("Camoufox browser not found in distribution.")
                print("ERROR: The distribution is incomplete. The .camoufox folder is missing.")
                print("Please contact the distributor or rebuild with 'camoufox fetch' first.")
                sys.exit(1)

            # Set the session data path
            session_data_dir = app_dir / "camoufox_session_data"
            session_data_dir.mkdir(exist_ok=True)
            os.environ['CAMOUFOX_SESSION_DATA'] = str(session_data_dir)
        else:
            # Running as script - use default locations
            print("Running in development mode - using default Camoufox paths")

    except ImportError:
        print("ERROR: Camoufox not found. Please ensure it's installed.")
        sys.exit(1)
    except Exception as e:
        print(f"Error setting up Camoufox: {e}")
        # Don't exit, let the app try to continue

# Run the setup when the module is imported
if __name__ == "__main__" or getattr(sys, 'frozen', False):
    setup_camoufox()