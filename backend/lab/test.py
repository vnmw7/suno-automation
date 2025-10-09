"""
System: Suno Automation
Module: Browser Testing
File URL: backend/lab/test.py
Purpose: Open Camoufox browser indefinitely for testing purposes
"""

import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from constants.ai_prompts import ai_prompts
from camoufox import AsyncCamoufox

async def open_browser_indefinitely():
    """Open Camoufox browser and keep it running indefinitely"""
    print("[INFO] Starting Camoufox browser indefinitely...")

    try:
        async with AsyncCamoufox(headless=False) as browser:
            print("[SUCCESS] Camoufox browser opened successfully")
            print("[INFO] Browser will remain open. Press Ctrl+C to stop.")

            # Navigate to a blank page to ensure browser is visible
            page = await browser.new_page()
            await page.goto("about:blank")

            print("[INFO] Browser is now visible and running")

            # Keep the browser open indefinitely
            while True:
                await asyncio.sleep(10)

    except KeyboardInterrupt:
        print("\n[INFO] Received keyboard interrupt, closing browser...")
    except Exception as err:
        print(f"[ERROR] Failed to open browser: {err}")

if __name__ == "__main__":
    # Start browser indefinitely
    asyncio.run(open_browser_indefinitely())
