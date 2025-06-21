"""
suno_functions.py
This file sets up the functions that will be used when automating Suno interactions.
"""

from camoufox.async_api import AsyncCamoufox
import traceback
import asyncio
import json
import re

# Import supabase from backend lib
import importlib
import importlib.util
import os

lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lib"))
supabase_utils_path = os.path.join(lib_path, "supabase.py")

spec = importlib.util.spec_from_file_location("supabase_utils", supabase_utils_path)
supabase_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supabase_utils)

supabase = supabase_utils.supabase


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
    try:
        async with AsyncCamoufox(
            headless=True,
            persistent_context=True,
            user_data_dir="user-data-dir",
            os=("windows"),
            config=config,
            humanize=True,
            i_know_what_im_doing=True,
        ) as browser:
            page = await browser.new_page()
            print("Navigating to suno.com for login...")
            await page.goto("https://suno.com")
            await page.wait_for_timeout(2000)
            await page.wait_for_load_state("load")
            print("Page loaded for login check.")

            if await page.locator('button:has(span:has-text("Sign in"))').is_visible():
                print("Sign-in button found. Attempting login process...")
                await page.click('button:has(span:has-text("Sign in"))')
                await page.wait_for_timeout(2000)
                await page.click('button:has(img[alt="Sign in with Google"])')
                await page.wait_for_timeout(2000)

                # Ensure email field is visible and ready
                email_input = page.locator('input[type="email"]')
                await email_input.wait_for(state="visible", timeout=10000)
                print("Typing email...")
                await email_input.type(
                    "pbNJ1sznC2Gr@gmail.com"
                )  # Use environment variables or config for credentials
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)
                await page.wait_for_load_state("load")

                # Ensure password field is visible and ready
                password_input = page.locator('input[type="password"]')
                await password_input.wait_for(state="visible", timeout=10000)
                print("Typing password...")
                await password_input.type(
                    "&!8G26tlbsgO"
                )  # Use environment variables or config for credentials
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(5000)  # Longer wait for login to complete
                await page.wait_for_load_state("load")
                print("Login steps completed.")
                return True
            else:
                print("Sign-in button not visible. Assuming already signed in.")
                return True

    except Exception as e:
        print(f"An error occurred in login_suno: {e}")
        print(traceback.format_exc())
        return False


async def generate_song(strBookName, intBookChapter, strVerseRange, strStyle, strTitle):
    from utils.converter import song_strcture_to_lyrics

    song_structure_dict = (
        supabase.table("song_structure_tbl")
        .select("song_structure")
        .eq("book_name", strBookName)
        .eq("chapter", intBookChapter)
        .eq("verse_range", strVerseRange)
        .execute()
    )

    print(f"Database query result for {strBookName} {intBookChapter}:{strVerseRange}:")
    print(
        f"  Data count: {len(song_structure_dict.data) if song_structure_dict.data else 0}"
    )
    print(f"  Data: {song_structure_dict.data}")

    # Check if data exists
    if not song_structure_dict.data or len(song_structure_dict.data) == 0:
        raise ValueError(
            f"No song structure found for {strBookName} {intBookChapter}:{strVerseRange}"
        )

    song_structure_json_string = song_structure_dict.data[0]["song_structure"]
    print(f"  song_structure field value: {song_structure_json_string}")
    print(f"  song_structure type: {type(song_structure_json_string)}")

    # Check if song_structure field is not None
    if song_structure_json_string is None:
        raise ValueError(
            f"Song structure is None for {strBookName} {intBookChapter}:{strVerseRange}"
        )

    try:
        parsed_song_structure = json.loads(song_structure_json_string)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in song structure for {strBookName} {intBookChapter}:{strVerseRange}: {e}"
        )

    song_structure_verses = song_strcture_to_lyrics(
        parsed_song_structure, strBookName, intBookChapter
    )
    print(f"Converted song structure verses: {song_structure_verses}")

    strLyrics_parts = []
    for section_title, verses_dict in song_structure_verses.items():
        strLyrics_parts.append(f"[{section_title}]:")
        for verse_num, verse_text in verses_dict.items():
            processed_text = verse_text.strip()
            processed_text = re.sub(r"\s*([.;])\s*", r"\1\n\n", processed_text)
            processed_text = re.sub(
                r"^\s+(?=\S)", "", processed_text, flags=re.MULTILINE
            )
            strLyrics_parts.append(processed_text)

    intermediate_strLyrics = "\n".join(strLyrics_parts)
    strLyrics = re.sub(r"\n{3,}", "\n", intermediate_strLyrics)
    strLyrics = re.sub(r"\n", "\n\n", strLyrics)
    strLyrics = re.sub(r"(\[.*?\]:)\n+", r"\1\n", strLyrics)

    try:
        async with AsyncCamoufox(
            headless=False,
            persistent_context=True,
            user_data_dir="user-data-dir",
            os=("windows"),
            config=config,
            humanize=True,
            i_know_what_im_doing=True,
        ) as browser:
            page = await browser.new_page()
            print("Navigating to suno.com...")
            await page.goto("https://suno.com/create")
            print("Waiting for page to load...")
            await page.wait_for_timeout(2000)
            await page.wait_for_load_state("networkidle")
            print("Page loaded.")
            print("Clicking Custom button...")

            print(f"Current URL before Custom button: {page.url}")

            try:
                custom_button = page.locator('button:has(span:has-text("Custom"))')
                await custom_button.wait_for(state="visible", timeout=10000)
                print("Custom button found and visible")
                await custom_button.click()
                await page.wait_for_timeout(2000)
                print("Custom button clicked successfully")
            except Exception as e:
                print(f"Error clicking Custom button: {e}")

                try:
                    alt_custom_button = page.locator('button:has-text("Custom")')
                    await alt_custom_button.wait_for(state="visible", timeout=5000)
                    await alt_custom_button.click()
                    await page.wait_for_timeout(2000)
                    print("Used alternative Custom button selector")
                except Exception as e2:
                    print(f"Alternative Custom button also failed: {e2}")
                    raise Exception("Could not find or click Custom button")

            print("Filling strLyrics...")
            try:
                strLyrics_textarea = page.locator(
                    'textarea[data-testid="lyrics-input-textarea"]'
                )
                await strLyrics_textarea.wait_for(state="visible", timeout=10000)
                await strLyrics_textarea.clear()
                await strLyrics_textarea.type(strLyrics)
                await page.wait_for_timeout(2000)
                print(f"strLyrics filled successfully: {len(strLyrics)} characters")
            except Exception as e:
                print(f"Error filling strLyrics: {e}")
                raise Exception("Could not fill lyrics textarea")

            print("Filling tags...")
            try:
                tags_textarea = page.locator(
                    'textarea[data-testid="tag-input-textarea"]'
                )
                await tags_textarea.wait_for(state="visible", timeout=10000)
                await tags_textarea.clear()
                await tags_textarea.type(strStyle)
                await page.wait_for_timeout(2000)
                print(f"Tags filled successfully: {strStyle}")
            except Exception as e:
                print(f"Error filling tags: {e}")
                raise Exception("Could not fill tags textarea")

            print("Filling title...")
            try:
                title_input = page.locator('input[placeholder="Enter song title"]')
                await title_input.wait_for(state="visible", timeout=10000)
                await title_input.clear()
                await title_input.type(strTitle)
                await page.wait_for_timeout(2000)
                print(f"Title filled successfully: {strTitle}")
            except Exception as e:
                print(f"Error filling title: {e}")
                raise Exception("Could not fill title input")

            print("Creating song...")
            try:
                create_button = page.locator('button:has(span:has-text("Create"))')
                await create_button.wait_for(state="visible", timeout=10000)
                print("Create button found and visible")
                await create_button.click()
                await page.wait_for_timeout(3000)
                print("Create button clicked successfully - song creation initiated")
            except Exception as e:
                print(f"Error clicking Create button: {e}")

                try:
                    alt_create_button = page.locator('button:has-text("Create")')
                    await alt_create_button.wait_for(state="visible", timeout=5000)
                    await alt_create_button.click()
                    await page.wait_for_timeout(3000)
                    print("Used alternative Create button selector")
                except Exception as e2:
                    print(f"Alternative Create button also failed: {e2}")
                    raise Exception("Could not find or click Create button")

            await page.wait_for_timeout(3000)
            return True

    except Exception as e:
        print(f"An error occurred in generate_song: {e}")
        print(traceback.format_exc())
        return False


async def download_song(strTitle, intIndex):
    try:
        async with AsyncCamoufox(
            headless=False,
            persistent_context=True,
            user_data_dir="user-data-dir",
            os=("windows"),
            config=config,
            humanize=True,
            i_know_what_im_doing=True,
        ) as browser:
            page = await browser.new_page()
            print("Navigating to user songs page...")
            try:
                await page.goto(
                    "https://suno.com/me", wait_until="domcontentloaded", timeout=30000
                )
                print("Waiting for page to load...")
                print(f"Navigation to /me initiated. Current URL: {page.url}")
                await page.wait_for_url("https://suno.com/me**", timeout=20000)
                await page.wait_for_timeout(3000)

                # Try to wait for networkidle, but don't fail if it times out
                try:
                    await page.wait_for_load_state("networkidle", timeout=15000)
                except Exception as e:
                    print(
                        f"Warning: Page may still be loading (networkidle timeout): {e}"
                    )

                print("Page loaded.")
            except Exception as e:
                print(f"Error during page navigation: {e}")

                if "suno.com/me" not in page.url:
                    raise Exception("Failed to navigate to the user songs page")

            print(f"Looking for song with title: {strTitle}")
            locator = page.locator(f'span.text-foreground-primary[title="{strTitle}"]')
            await locator.first.wait_for(state="attached", timeout=10000)
            count = await locator.count()
            print(f"Found {count} songs with title '{strTitle}'")
            await page.wait_for_timeout(2000)

            # Validate index
            if intIndex < 1 or intIndex > count:
                raise Exception(
                    f"Invalid song index {intIndex}. Found {count} songs with title '{strTitle}'. Index should be between 1 and {count}."
                )

            print(f"Right-clicking on song index {intIndex} (0-based: {intIndex})...")
            await locator.nth(intIndex - 1).click(button="right")
            await page.wait_for_timeout(2000)

            print("Opening download menu...")
            context_menu_content = page.locator(
                "div[data-radix-menu-content][data-state='open']"
            )
            await context_menu_content.wait_for(state="visible", timeout=15000)
            await page.wait_for_timeout(500)

            download_submenu_trigger = context_menu_content.locator(
                '[data-testid="download-sub-trigger"]'
            )
            await download_submenu_trigger.wait_for(state="visible", timeout=5000)
            await download_submenu_trigger.hover()

            download_trigger_id = await download_submenu_trigger.get_attribute("id")
            if not download_trigger_id:
                raise Exception(
                    "Download trigger item does not have an ID. Cannot reliably locate submenu."
                )

            download_submenu_panel = page.locator(
                f"div[data-radix-menu-content][data-state='open'][aria-labelledby='{download_trigger_id}']"
            )
            await download_submenu_panel.wait_for(state="visible", timeout=10000)

            mp3_audio_item = download_submenu_panel.locator(
                "div[role='menuitem']:has-text('MP3 Audio')"
            )
            await mp3_audio_item.wait_for(state="visible", timeout=5000)
            await mp3_audio_item.click()
            await page.wait_for_timeout(2000)

            print("Song download initiated successfully!")
            return True

    except Exception as e:
        print(f"An error occurred in download_song: {e}")
        print(traceback.format_exc())
        return False


async def download_song_with_page(page, strTitle, intIndex):
    try:
        print(
            f"Inside download_song_with_page for title: '{strTitle}', index: {intIndex}"
        )

        # Check if page is already closed before starting
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
        song_title_locator_str = f'span.text-foreground-primary[title="{strTitle}"]'
        song_elements = page.locator(song_title_locator_str)

        try:
            await song_elements.first.wait_for(state="attached", timeout=30000)
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
        if not (1 <= intIndex <= count):
            print(
                f"Invalid song index {intIndex}. Found {count} songs. Index must be between 1 and {count}."
            )
            return False

        target_song_element = song_elements.nth(intIndex - 1)
        print(f"Targeting song at 0-based index {intIndex - 1}.")

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
        await mp3_audio_item.wait_for(
            state="visible", timeout=10000
        )  # Increased timeout
        print("'MP3 Audio' option located and ready.")

        # CRITICAL FIX: Start expect_download *before* the click that triggers it
        print("Expecting download to start...")
        try:
            async with page.expect_download(timeout=60000) as download_info_manager:
                print("Attempting to click 'MP3 Audio' option to initiate download...")
                # Add small delay for stability
                await page.wait_for_timeout(500)
                await mp3_audio_item.click(timeout=15000)  # Increased click timeout
                print("'MP3 Audio' option clicked.")

                # Handle "Download Anyway" button if it appears AFTER 'MP3 Audio' click
                # This must also be INSIDE the `async with page.expect_download` block
                print("Checking for 'Download Anyway' button...")
                download_anyway_button = page.locator(
                    'button:has(span:has-text("Download Anyway"))'
                )
                try:
                    await download_anyway_button.wait_for(
                        state="visible", timeout=15000  # Increased timeout
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

            download_path = f"./{download.suggested_filename}"
            await download.save_as(download_path)
            print(
                f"Download for '{strTitle}' (index {intIndex}) saved to: {download_path}"
            )

        except Exception as download_expect_err:
            print(f"Error during download expectation or saving: {download_expect_err}")
            print(traceback.format_exc())
            return False

        await page.wait_for_timeout(3000)  # Brief pause after saving

        print(
            f"Song download for '{strTitle}' (index {intIndex}) process completed successfully!"
        )
        return True

    except Exception as e:
        print(
            f"A critical error occurred in download_song_with_page for index {intIndex}, title '{strTitle}': {e}"
        )
        print(traceback.format_exc())

        # Check if page is still available for debugging
        if page and not page.is_closed():
            print("Page is still available after error.")
            # Screenshot could be taken here if needed for debugging
        elif page and page.is_closed():
            print("Page was closed when the critical error was caught.")

        return False


if __name__ == "__main__":

    async def main():
        await generate_song(
            strBookName="Genesis",
            intBookChapter=1,
            strStyle="biblical, creation, inspirational",
            strTitle="Genesis Creation Song",
        )
        print("generate_song() completed.")

    asyncio.run(main())
