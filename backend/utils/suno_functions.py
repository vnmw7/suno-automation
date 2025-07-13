"""
suno_functions.py
This file sets up the functions that will be used when automating Suno interactions.
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


async def download_song_with_page(page, strTitle, intIndex):
    try:
        print(
            f"Inside download_song_with_page for title: '{strTitle}', index: {intIndex}"
        )

        if page.is_closed():
            print(
                f"Page was closed before starting download for song index {intIndex}. Cannot proceed."
            )
            return False

        print("Navigating to user songs page (https://suno.com/me)...")
        await page.goto(
            "https://suno.com/me", wait_until="domcontentloaded", timeout=45000
        )
        print(f"Current URL after navigation attempt: {page.url}")

        try:
            await page.wait_for_url("https://suno.com/me**", timeout=30000)
            print("Successfully landed on /me page.")
        except Exception as e:
            print(f"Failed to confirm navigation to /me page URL: {e}")
            if page.is_closed():
                print("Page closed during URL wait.")
            return False

        print("Waiting for page content to settle (networkidle)...")
        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
        except Exception as e:
            print(f"Warning: Networkidle timeout on /me page: {e}")
            if page.is_closed():
                print("Page closed during networkidle wait.")

        await page.wait_for_timeout(2000)

        print(f"Looking for song elements with title: '{strTitle}'")
        song_title_locator_str = f'span[title="{strTitle}"]'  # More resilient selector
        song_elements = page.locator(song_title_locator_str)

        try:
            await song_elements.first.wait_for(
                state="attached", timeout=60000
            )  # Increased timeout
            print("First song element with matching title is attached.")
        except Exception as e:
            print(
                f"Timeout: No song elements with title '{strTitle}' became attached. Error: {e}"
            )
            return False

        count = await song_elements.count()
        print(f"Found {count} song(s) with title '{strTitle}'.")

        if count == 0:
            print(f"No songs found with title '{strTitle}'. Cannot download.")
            return False

        target_0_based_index = 0
        if intIndex > 0:
            if not (1 <= intIndex <= count):
                print(
                    f"Invalid song index {intIndex}. Found {count} songs. Index must be between 1 and {count}."
                )
                return False
            target_0_based_index = intIndex - 1
        else:  # Handle negative indices from the end of the list
            if not (-count <= intIndex <= -1):
                print(
                    f"Invalid negative song index {intIndex}. Found {count} songs. Index must be between {-count} and -1."
                )
                return False
            target_0_based_index = count + intIndex

        target_song_element = song_elements.nth(target_0_based_index)
        print(f"Targeting song at 0-based index {target_0_based_index}.")

        print("Scrolling target song into view if needed...")
        try:
            await target_song_element.scroll_into_view_if_needed(
                timeout=20000
            )  # Increased timeout
            print(
                "Successfully scrolled using Playwright's scroll_into_view_if_needed."
            )
        except Exception as scroll_err_playwright:
            print(
                f"Playwright scroll_into_view_if_needed failed: {scroll_err_playwright}. Attempting JavaScript scroll."
            )
            try:
                await target_song_element.wait_for(state="attached", timeout=5000)
                is_vis_before_js_scroll = await target_song_element.is_visible()
                if is_vis_before_js_scroll:
                    print(
                        "Element reported as visible before JS scroll attempt; Playwright scroll might have had stability issues."
                    )
                else:
                    print("Element not visible, proceeding with JS scroll.")

                await target_song_element.evaluate(
                    "element => element.scrollIntoView({ block: 'center', inline: 'nearest' })"
                )
                await page.wait_for_timeout(1500)
                print("JavaScript scrollIntoView attempt executed.")

                if not await target_song_element.is_visible(timeout=7000):
                    print(
                        "Warning: Element still not visible after JavaScript scroll and wait."
                    )
                    raise scroll_err_playwright
                else:
                    print("Element confirmed visible after JavaScript scroll attempt.")
            except Exception as scroll_err_js_combined:
                print(
                    f"JavaScript scroll/visibility check also failed: {scroll_err_js_combined}"
                )
                raise scroll_err_playwright

        print(
            "Waiting for target song element to be visible and stable before right-click..."
        )
        try:
            await target_song_element.wait_for(state="visible", timeout=15000)
            print("Target song element is visible.")
        except Exception as e:
            print(
                f"Timeout: Target song (index {intIndex}) did not become visible. Error: {e}"
            )
            return False

        print(f"Attempting to right-click on song index {intIndex}...")
        await target_song_element.click(button="right", timeout=20000)
        print("Right-click successful.")

        await page.wait_for_timeout(1000)

        print("Locating and waiting for context menu...")
        context_menu_content = page.locator(
            "div[data-radix-menu-content][data-state='open']"
        )
        await context_menu_content.wait_for(state="visible", timeout=15000)
        print("Context menu is visible.")

        await page.wait_for_timeout(500)

        print("Locating 'Download' submenu trigger and hovering...")
        download_submenu_trigger = context_menu_content.locator(
            '[data-testid="download-sub-trigger"]'
        )
        await download_submenu_trigger.wait_for(state="visible", timeout=10000)
        await download_submenu_trigger.hover(timeout=5000)
        print("'Download' submenu trigger hovered.")

        await page.wait_for_timeout(500)

        download_trigger_id = await download_submenu_trigger.get_attribute("id")
        download_submenu_panel_locator_str = ""
        if download_trigger_id:
            download_submenu_panel_locator_str = f"div[data-radix-menu-content][data-state='open'][aria-labelledby='{download_trigger_id}']"
        else:
            download_submenu_panel_locator_str = "div[data-radix-menu-content][data-state='open'][role='menu']"  # Fallback

        download_submenu_panel = page.locator(download_submenu_panel_locator_str).last
        await download_submenu_panel.wait_for(state="visible", timeout=10000)
        print("Download submenu panel is visible.")

        print("Locating 'MP3 Audio' option...")
        mp3_audio_item = download_submenu_panel.locator(
            "div[role='menuitem']:has-text('MP3 Audio')"
        )
        await mp3_audio_item.wait_for(state="visible", timeout=10000)
        print("'MP3 Audio' option located and ready.")

        print("Expecting download to start...")
        try:
            async with page.expect_download(timeout=60000) as download_info_manager:
                print("Attempting to click 'MP3 Audio' option to initiate download...")

                await page.wait_for_timeout(500)
                await mp3_audio_item.click(timeout=15000)
                print("'MP3 Audio' option clicked.")

                print("Checking for 'Download Anyway' button...")
                download_anyway_button = page.locator(
                    'button:has(span:has-text("Download Anyway"))'
                )
                try:
                    await download_anyway_button.wait_for(
                        state="visible", timeout=15000
                    )
                    print("'Download Anyway' button is visible. Clicking it...")
                    await download_anyway_button.click(timeout=10000)
                    print("'Download Anyway' button clicked.")
                except Exception:
                    print(
                        "'Download Anyway' button not found/visible when expected. Assuming direct download."
                    )

            print("Download expectation block finished.")
            download = await download_info_manager.value

            if not download:
                print(
                    f"Error: Download was expected but not received for '{strTitle}' index {intIndex}."
                )
                return False

            sanitized_title = strTitle.replace(":", "-")
            download_path = f"./for_song_qa/{sanitized_title.replace(' ', '_')}_index_{intIndex}.mp3"
            await download.save_as(download_path)
            print(
                f"Download for '{strTitle}' (index {intIndex}) saved to: {download_path}"
            )

        except Exception as download_expect_err:
            print(f"Error during download expectation or saving: {download_expect_err}")
            print(traceback.format_exc())
            return False

        await page.wait_for_timeout(3000)

        print(
            f"Song download for '{strTitle}' (index {intIndex}) process completed successfully!"
        )
        return True

    except Exception as e:
        print(
            f"A critical error occurred in download_song_with_page for index {intIndex}, title '{strTitle}': {e}"
        )
        print(traceback.format_exc())

        if page and not page.is_closed():
            print("Page is still available after error.")

        elif page and page.is_closed():
            print("Page was closed when the critical error was caught.")

        return False
