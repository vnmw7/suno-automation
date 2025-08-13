"""
suno_functions.py
This file sets up the functions that will be used when automating Suno interactions.

TODO: Enhance browser automation robustness. The scripts in this file are functional
but could be made more resilient to changes in the Suno website's layout.
Consider adding more advanced error handling, retry mechanisms with exponential backoff,
and more flexible selectors to make these scripts less likely to break in the future.
"""

from camoufox.async_api import AsyncCamoufox
import traceback
import importlib
import importlib.util
import os
from dotenv import load_dotenv
import sys

lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lib"))
supabase_utils_path = os.path.join(lib_path, "supabase.py")

spec = importlib.util.spec_from_file_location("supabase_utils", supabase_utils_path)
supabase_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supabase_utils)

supabase = supabase_utils.supabase

load_dotenv()

# Validate environment variables at startup
REQUIRED_ENV_VARS = [
    "GOOGLE_EMAIL",
    "GOOGLE_PASSWORD",
    "MICROSOFT_EMAIL",
    "MICROSOFT_PASSWORD",
]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    sys.exit(1)


# Credentials from environment variables
GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")
MICROSOFT_EMAIL = os.getenv("MICROSOFT_EMAIL")
MICROSOFT_PASSWORD = os.getenv("MICROSOFT_PASSWORD")


config = {
    "window.outerHeight": 1056,
    "window.outerWidth": 1920,
    "window.innerHeight": 1008,
    "window.innerWidth": 1920,
    "window.history.length": 4,
    "navigator.userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "navigator.appCodeName": "Mozilla",
    "navigator.appName": "Netscape",
    "navigator.appVersion": "5.0 (Windows)",
    "navigator.oscpu": "Windows NT 10.0; Win64; x64",
    "navigator.language": "en-US",
    "navigator.languages": ["en-US"],
    "navigator.platform": "Win32",
    "navigator.hardwareConcurrency": 12,
    "navigator.product": "Gecko",
    "navigator.productSub": "20030107",
    "navigator.maxTouchPoints": 10,
}


async def login_suno():
    async with AsyncCamoufox(
        headless=False,
        persistent_context=True,
        user_data_dir="backend/camoufox_session_data",
        os=("windows"),
        config=config,
        humanize=True,
        i_know_what_im_doing=True,
    ) as browser:
        page = await browser.new_page()
        try:
            print("Navigating to suno.com for login...")
            await page.goto("https://suno.com")
            await page.wait_for_load_state("load", timeout=30000)
            print("Page loaded for login check.")

            sign_in_button = page.locator('button:has(span:has-text("Sign in"))')
            if await sign_in_button.is_visible(timeout=10000):
                print("Sign-in button found. Attempting login process...")
                await sign_in_button.click()
                await page.wait_for_timeout(2000)
                await page.click('button:has(img[alt="Sign in with Google"])')
                await page.wait_for_load_state("load", timeout=30000)

                # Robustly find and fill email
                email_selectors = [
                    'input[type="email"]',
                    'input[name="identifier"]',
                    "#identifierId",
                ]
                email_input = None
                for selector in email_selectors:
                    try:
                        email_input = page.locator(selector)
                        await email_input.wait_for(state="visible", timeout=5000)
                        print(f"Found email input with selector: {selector}")
                        break
                    except Exception:
                        print(f"Email input not found with selector: {selector}")
                        continue

                if not email_input or not await email_input.is_visible():
                    raise Exception("Could not find a visible email input field.")

                # TOFIX: Secure Credential Management.
                # The credentials should not be hardcoded. They should be loaded
                # from environment variables or a secure secret management service.
                print("Typing email...")
                await email_input.type("pbNJ1sznC2Gr@gmail.com", delay=50)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("load", timeout=30000)

                # Robustly find and fill password
                password_selectors = [
                    'input[type="password"]',
                    'input[name="Passwd"]',
                    'input[name="password"]',
                ]
                password_input = None
                for selector in password_selectors:
                    try:
                        password_input = page.locator(selector)
                        await password_input.wait_for(state="visible", timeout=5000)
                        print(f"Found password input with selector: {selector}")
                        break
                    except Exception:
                        print(f"Password input not found with selector: {selector}")
                        continue

                if not password_input or not await password_input.is_visible():
                    raise Exception("Could not find a visible password input field.")

                print("Typing password...")
                await password_input.type("&!8G26tlbsgO", delay=50)
                await page.keyboard.press("Enter")
                await page.wait_for_load_state("load", timeout=60000)
                print("Login steps completed.")
                return True
            else:
                print("Sign-in button not visible. Assuming already signed in.")
                return True

        except Exception as e:
            print(f"An error occurred in login_suno: {e}")
            print(traceback.format_exc())
            # Capture a screenshot for debugging
            screenshot_path = "backend/logs/ss_login_error.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            return False

async def delete_suno_song(song_title: str, intIndex: int = -1):
    """
    Deletes a song from Suno.com using browser automation.
    """
    try:
        async with AsyncCamoufox(
            headless=False,
            persistent_context=True,
            user_data_dir="backend/camoufox_session_data",
            os=("windows"),
            config=config,
            humanize=True,
            i_know_what_im_doing=True,
        ) as browser:
            page = await browser.new_page()
            await page.goto("https://suno.com/me", wait_until="domcontentloaded", timeout=45000)

            # This is a simplified version of the logic in download_song_handler
            # In a real scenario, you'd want the same robust locator strategies
            song_elements = page.locator(f'span[title="{song_title}"]')
            await song_elements.first.wait_for(state="visible", timeout=30000)

            target_song = song_elements.nth(intIndex)
            await target_song.scroll_into_view_if_needed()

            # Right click to open context menu
            await target_song.click(button="right")

            # Click the delete option
            delete_option = page.locator('div[role="menuitem"]:has-text("Delete")')
            await delete_option.wait_for(state="visible", timeout=10000)
            await delete_option.click()

            # Handle confirmation dialog
            # This assumes the confirmation button has a data-testid or a specific text
            confirm_button = page.locator('button:has-text("Delete")').last
            await confirm_button.wait_for(state="visible", timeout=10000)
            await confirm_button.click()

            await page.wait_for_load_state("networkidle", timeout=30000)
            print(f"Successfully deleted song: {song_title}")
            return True

    except Exception as e:
        print(f"An error occurred in delete_suno_song: {e}")
        print(traceback.format_exc())
        return False
