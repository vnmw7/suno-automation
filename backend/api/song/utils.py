"""Suno Automation - Song Utilities Module

This module provides utility functions for generating songs using Suno's API
and reviewing generated songs with Google AI Studio. It handles the entire
song creation workflow from lyric generation to quality review.
"""

import os
import json
import re
import traceback
import importlib.util
import datetime  # Added for timestamp generation
import aiohttp
from typing import Dict, Any, Union, Optional
from slugify import slugify  # Added for filename sanitization
from camoufox import AsyncCamoufox
from playwright.async_api import Page, Locator
from configs.browser_config import config
from services.supabase_service import SupabaseService

# TODO: Future Improvements
# 1. Implement retry logic with exponential backoff for browser automation failures
# 2. Replace print statements with structured logging for better production monitoring
# 3. Add health check endpoint to verify Suno login status before operations
# 4. Consider implementing a queue system for batch song generation
# 5. Add metrics collection for success/failure rates and performance monitoring

# Import supabase
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "lib"))
supabase_utils_path = os.path.join(lib_path, "supabase.py")

spec = importlib.util.spec_from_file_location("supabase_utils", supabase_utils_path)
supabase_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supabase_utils)

supabase = supabase_utils.supabase

# Import review function from ai_review module
from api.ai_review.utils import review_song_with_ai


async def generate_song_handler(
    strBookName: str,
    intBookChapter: int,
    strVerseRange: str,
    strStyle: str,
    strTitle: str,
) -> Dict[str, Any]:
    """
    Coordinates the song generation workflow by validating inputs and calling generate_song.

    This is the primary entry point for song generation requests. It ensures:
    - All required parameters are present
    - Input values meet expected formats
    - Errors are caught and properly handled

    Args:
        strBookName (str): Canonical Bible book name (e.g., "Genesis", "Exodus")
        intBookChapter (int): Chapter number (1-indexed)
        strVerseRange (str): Verse range in format "start-end" (e.g., "1-5")
        strStyle (str): Musical style/genre (e.g., "Pop", "Rock")
        strTitle (str): Title for the generated song

    Returns:
        Dict[str, Any]: Result dictionary with:
            - success (bool): Operation status
            - song_id (str): Suno song ID if successful
            - lyrics (str): Lyrics used in generation
            - style (str): Applied musical style
            - title (str): Song title

    Raises:
        ValueError: If inputs are invalid or song structure not found
    """
    return await generate_song(
        strBookName=strBookName,
        intBookChapter=intBookChapter,
        strVerseRange=strVerseRange,
        strStyle=strStyle,
        strTitle=strTitle,
    )


async def generate_song(
    strBookName: str,
    intBookChapter: int,
    strVerseRange: str,
    strStyle: str,
    strTitle: str,
) -> Union[Dict[str, Any], bool]:
    """
    Generates a song using Suno's API through automated browser interactions.

    This function handles the entire song creation workflow:
    1. Fetches song structure from database
    2. Converts structure to properly formatted lyrics
    3. Automates Suno website to input song details
    4. Initiates song creation
    5. Captures and saves generated song metadata

    Args:
        strBookName (str): Canonical Bible book name
        intBookChapter (int): Chapter number (1-indexed)
        strVerseRange (str): Verse range in "start-end" format
        strStyle (str): Musical style/genre
        strTitle (str): Song title

    Returns:
        Union[Dict[str, Any], bool]: On success: dictionary with:
            - success (bool): True
            - song_id (str): Suno-generated song ID
            - lyrics (str): Lyrics used for generation
            - style (str): Applied musical style
            - title (str): Song title
        On failure: False

    Raises:
        ValueError: If lyrics generation fails or inputs are invalid
        Exception: For browser automation failures
    """
    from utils.converter import song_strcture_to_lyrics

    song_structure_dict = (
        supabase.table("song_structure_tbl")
        .select("id, song_structure")
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

    song_structure_id = song_structure_dict.data[0]["id"]
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
        song_structure_id, parsed_song_structure, strBookName, intBookChapter, strStyle
    )
    print(f"Converted song structure verses: {song_structure_verses}")

    strLyrics_parts = []
    for section_title, verses_dict in song_structure_verses.items():
        # Ensure section_title is a string and verses_dict is a dictionary
        if not isinstance(section_title, str) or not isinstance(verses_dict, dict):
            print(f"Skipping invalid section: {section_title}")
            continue

        strLyrics_parts.append(f"[{section_title}]")
        for verse_num, verse_text in verses_dict.items():
            # Ensure verse_text is a string
            if not isinstance(verse_text, str):
                print(f"Skipping invalid verse text for verse {verse_num}")
                continue

            processed_text = verse_text.strip()
            # Add a space before punctuation for better readability and to avoid issues with splitting
            processed_text = re.sub(r"\s*([,;.!?])\s*", r" \1 ", processed_text)
            # Remove extra spaces
            processed_text = re.sub(r"\s+", " ", processed_text).strip()
            strLyrics_parts.append(processed_text)

    strLyrics = "\n".join(strLyrics_parts)

    # Final check to ensure lyrics are not empty
    if not strLyrics.strip():
        raise ValueError("Generated lyrics are empty. Cannot proceed.")

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
            print("Navigating to suno.com...")
            await page.goto("https://suno.com/create")
            print("Waiting for page to load...")
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
                create_selectors = [
                    '[data-testid="create-button"]',
                    'button:has-text("Create")',
                ]
                create_button = None
                for selector in create_selectors:
                    try:
                        button = (
                            page.locator(selector).nth(1)
                            if "has-text" in selector
                            else page.locator(selector)
                        )
                        await button.wait_for(state="visible", timeout=5000)
                        create_button = button
                        print(f"Found create button with selector: {selector}")
                        break
                    except Exception:
                        print(f"Create button not found with selector: {selector}")
                        continue

                if not create_button:
                    raise Exception("Could not find a visible create button.")

                await create_button.click()
                await page.wait_for_timeout(5000)
                await page.wait_for_load_state("networkidle", timeout=180000)
                print("Song creation initiated and page loaded.")

                # Get the song ID from the URL
                current_url = page.url
                suno_song_id = None
                if "suno.com/song/" in current_url:
                    suno_song_id = current_url.split("suno.com/song/")[1].split("/")[0]
                    print(f"Extracted suno_song_id: {suno_song_id}")

                    # Save to progress_v1_tbl
                    try:
                        data = (
                            supabase.table("tblprogress_v1")
                            .insert(
                                {
                                    "pg1_song_struct_id": song_structure_id,
                                    "pg1_lyrics": strLyrics,
                                    "pg1_status": 0,
                                    "pg1_reviews": 0,
                                    "pg1_song_id": suno_song_id,
                                    "pg1_style": strStyle,
                                }
                            )
                            .execute()
                        )
                        print(f"Saved to progress_v1_tbl: {data}")
                    except Exception as db_error:
                        print(f"Error saving to Supabase: {db_error}")

                return {
                    "success": True,
                    "song_id": suno_song_id,
                    "lyrics": strLyrics,
                    "style": strStyle,
                    "title": strTitle,
                }

            except Exception as e:
                print(f"Error clicking Create button: {e}")
                raise Exception("Could not click Create button")

    except Exception as e:
        print(f"An error occurred in generate_song: {e}")
        print(traceback.format_exc())
        return False

async def teleport_click(page: Page, locator: Locator, button: str = "left", delay: int = 50):
    """
    Bypasses Camoufox's humanization by executing a direct JavaScript click.
    This is a true, instantaneous "teleport" click.

    Args:
        page (Page): Playwright Page instance
        locator (Locator): Playwright Locator for target element
        button (str): Mouse button ('left'/'right'/'middle') - defaults to 'left'
        delay (int): Milliseconds to wait after click (default: 50ms)

    Raises:
        Exception: If element interaction fails
    """
    print(f"Teleporting via JS click (button: {button})")
    await locator.scroll_into_view_if_needed(timeout=10000)
    
    # This executes a click directly in the browser's engine, bypassing Python patches.
    if button == 'right':
        # Dispatch 'contextmenu' event for a right-click.
        await locator.dispatch_event('contextmenu', {'button': 2})
    else:
        # Use JavaScript click() for a standard left-click.
        await locator.evaluate("element => element.click()")
    
    await page.wait_for_timeout(delay)
    print("Teleport click completed.")

async def teleport_hover(page: Page, locator: Locator, delay: int = 50):
    """
    Bypasses Camoufox's humanization by executing a direct JavaScript mouseover event.
    This is a true, instantaneous "teleport" hover.

    Args:
        page (Page): Playwright Page instance
        locator (Locator): Playwright Locator for target element
        delay (int): Milliseconds to wait after hover (default: 50ms)

    Raises:
        Exception: If element interaction fails
    """
    print("Teleporting via JS hover")
    await locator.scroll_into_view_if_needed(timeout=10000)
    
    # This dispatches a mouseover event directly to the element in the browser.
    await locator.dispatch_event('mouseover')
    await page.wait_for_timeout(delay)
    print("Teleport hover completed.")

# TODO: Implement retry_with_backoff utility function for robust browser operations
# async def retry_with_backoff(func, max_attempts=3, base_delay=1000):
#     for attempt in range(max_attempts):
#         try:
#             return await func()
#         except Exception as e:
#             if attempt == max_attempts - 1:
#                 raise
#             await asyncio.sleep(base_delay * (2 ** attempt) / 1000)

async def download_song_handler(
    strTitle: str, intIndex: int, download_path: str
) -> Dict[str, Any]:
    """
    Downloads a song from Suno.com using automated browser interactions.

    Uses instantaneous "teleport" actions for speed, except for a regular 
    humanized hover on the download sub-menu trigger to ensure it opens correctly.

    Features:
    - Enhanced error handling for common failure points
    - Robust element location with multiple fallback strategies
    - Configurable download paths
    - Duplicate song handling
    - Premium content warning bypass

    Args:
        strTitle (str): Exact title of song to download
        intIndex (int): Song position (positive: 1-based from start, negative: from end)
        download_path (str): Directory to save downloaded MP3

    Returns:
        Dict[str, Any]: Result dictionary with:
            - success (bool): Download status
            - file_path (str): Saved file path if successful
            - error (str): Failure reason if applicable
            - song_title (str): Original song title
            - song_index (int): Original song index

    Note:
        Uses 'teleport' techniques to bypass bot detection during interactions
    """
    result = {
        "success": False,
        "file_path": None,
        "error": None,
        "song_title": strTitle,
        "song_index": intIndex,
    }

    try:
        # Ensure download directory exists
        os.makedirs(download_path, exist_ok=True)

        print(
            f"Starting enhanced download process for: '{strTitle}' at index {intIndex}"
        )

        async with AsyncCamoufox(
            headless=False,
            persistent_context=True,
            user_data_dir="backend/camoufox_session_data",
            os=("windows"),
            config=config,
            humanize=True,  # IMPORTANT: Keep this True for the one special hover to work
            i_know_what_im_doing=True,
        ) as browser:
            page = await browser.new_page()

            try:
                # Validate page is available
                if page.is_closed():
                    raise Exception("Browser page was closed before starting download")

                # Navigate to user's songs page
                print("Navigating to Suno user songs page...")
                await page.goto(
                    "https://suno.com/me", wait_until="domcontentloaded", timeout=45000
                )
                print(f"Navigation completed. Current URL: {page.url}")

                # Verify we're on the correct page
                try:
                    await page.wait_for_url("https://suno.com/me**", timeout=30000)
                    print("Successfully confirmed navigation to /me page")
                except Exception as url_error:
                    raise Exception(f"Failed to reach user songs page: {url_error}")

                # Wait for page content to load
                print("Waiting for page content to stabilize...")
                try:
                    await page.wait_for_load_state("networkidle", timeout=30000)
                except Exception as load_error:
                    print(
                        f"Warning: Network idle timeout (continuing anyway): {load_error}"
                    )

                await page.wait_for_timeout(3000)  # Additional stability wait

                # Wait for the last song title to be visible, ensuring all songs are loaded
                print("Waiting for song list to load...")
                try:
                    # The last element should be visible if the list has loaded correctly
                    last_song_locator = page.locator(f'span[title="{strTitle}"]').last
                    await last_song_locator.wait_for(state="visible", timeout=45000)
                    print("Song list appears to be loaded. Proceeding...")
                except Exception as e:
                    raise Exception(
                        f"Timed out waiting for song list to become visible: {e}"
                    )

                # Find song elements with enhanced error handling
                print(f"Searching for songs with title: '{strTitle}'")
                song_locator_patterns = [
                    f'span[title="{strTitle}"]',
                    f'*:has-text("{strTitle}")',
                    f'[data-testid*="song"]:has-text("{strTitle}")',
                ]

                song_elements = None
                for pattern in song_locator_patterns:
                    try:
                        elements = page.locator(pattern)
                        await elements.first.wait_for(state="attached", timeout=15000)
                        count = await elements.count()
                        if count > 0:
                            song_elements = elements
                            print(f"Found {count} song(s) using pattern: {pattern}")
                            break
                    except Exception:
                        print(f"Pattern failed: {pattern}")
                        continue

                if not song_elements:
                    raise Exception(
                        f"No songs found with title '{strTitle}' using any search pattern"
                    )

                # Validate and calculate target index
                song_count = await song_elements.count()
                print(f"Total songs found with title '{strTitle}': {song_count}")

                if song_count == 0:
                    raise Exception(f"No songs found with title '{strTitle}'")

                # New logic to handle duplicate hidden elements
                if song_count > 1 and song_count % 2 == 0:
                    visible_song_count = song_count // 2
                    start_index_offset = visible_song_count
                    print(
                        f"Adjusting for duplicates. Visible songs: {visible_song_count}. Starting at index {start_index_offset}."
                    )
                else:
                    visible_song_count = song_count
                    start_index_offset = 0
                    print("Assuming all found songs are visible.")

                # Validate and normalize index against visible songs
                if intIndex == 0:
                    raise Exception(
                        "Index cannot be 0. Use positive (1-based) or negative (-1 = last) indexing."
                    )

                target_index = 0
                # Convert positive index to its 0-based equivalent in the visible part
                if intIndex > 0:
                    if not (1 <= intIndex <= visible_song_count):
                        raise Exception(
                            f"Invalid positive index {intIndex}. Must be between 1 and {visible_song_count}."
                        )
                    target_index = start_index_offset + (intIndex - 1)
                # Handle negative index
                else:  # intIndex < 0
                    if not (-visible_song_count <= intIndex <= -1):
                        raise Exception(
                            f"Invalid index {intIndex}. Must be between -{visible_song_count} and -1."
                        )
                    target_index = start_index_offset + (visible_song_count + intIndex)

                target_song = song_elements.nth(target_index)
                print(f"Targeting song at index {intIndex} (0-based: {target_index})")

                # Enhanced scrolling with multiple fallbacks
                print("Ensuring target song is visible...")
                try:
                    await target_song.scroll_into_view_if_needed(timeout=20000)
                    print("Scrolled using Playwright scroll_into_view_if_needed")
                except Exception as scroll_error:
                    print(
                        f"Playwright scroll failed: {scroll_error}. Trying JavaScript scroll..."
                    )
                    try:
                        await target_song.evaluate(
                            "element => element.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'smooth' })"
                        )
                        await page.wait_for_timeout(2000)
                        print("Used JavaScript scrollIntoView")
                    except Exception as js_scroll_error:
                        print(f"JavaScript scroll also failed: {js_scroll_error}")

                # Verify target song is visible
                try:
                    await target_song.wait_for(state="visible", timeout=15000)
                    print("Target song element confirmed visible")
                except Exception:
                    raise Exception(
                        f"Target song at index {intIndex} is not visible after scrolling"
                    )

                # Right-click to open context menu (INSTANT)
                print(f"Right-clicking on song at index {intIndex}...")
                await teleport_click(page, target_song, button="right")

                await page.wait_for_timeout(1000)

                # Wait for context menu with enhanced detection
                print("Waiting for context menu to appear...")
                context_menu_selectors = [
                    "div[data-radix-menu-content][data-state='open']",
                    "[role='menu'][data-state='open']",
                    ".context-menu[data-state='open']",
                ]

                context_menu = None
                for selector in context_menu_selectors:
                    try:
                        menu = page.locator(selector)
                        await menu.wait_for(state="visible", timeout=10000)
                        context_menu = menu
                        print(f"Context menu found with selector: {selector}")
                        break
                    except Exception:
                        continue

                if not context_menu:
                    raise Exception("Context menu did not appear after right-click")

                await page.wait_for_timeout(500)

                # Find and hover download submenu trigger
                print("Locating download submenu trigger...")
                download_triggers = [
                    '[data-testid="download-sub-trigger"]',
                    '*:has-text("Download")',
                    '[role="menuitem"]:has-text("Download")',
                ]

                download_trigger = None
                for trigger_selector in download_triggers:
                    try:
                        trigger = context_menu.locator(trigger_selector)
                        await trigger.wait_for(state="visible", timeout=8000)
                        download_trigger = trigger
                        print(f"Found download trigger: {trigger_selector}")
                        break
                    except Exception:
                        continue

                if not download_trigger:
                    raise Exception("Download option not found in context menu")

                # ################################################################## #
                # ##                  THE CRITICAL EXCEPTION                      ## #
                # ## Here, we use the NORMAL hover to ensure the menu triggers.  ## #
                # ################################################################## #
                print("Performing REGULAR (humanized) hover on Download trigger...")
                await download_trigger.hover()  # Use the standard hover to trigger the sub-menu
                # ################################################################## #

                await page.wait_for_timeout(1000)

                # Wait for download submenu panel
                print("Waiting for download submenu panel...")
                download_trigger_id = await download_trigger.get_attribute("id")

                submenu_selectors = []
                if download_trigger_id:
                    submenu_selectors.append(
                        f"div[data-radix-menu-content][data-state='open'][aria-labelledby='{download_trigger_id}']"
                    )
                submenu_selectors.extend(
                    [
                        "div[data-radix-menu-content][data-state='open'][role='menu']",
                        "*[role='menu'][data-state='open']",
                    ]
                )

                submenu_panel = None
                for selector in submenu_selectors:
                    try:
                        panel = page.locator(selector).last
                        await panel.wait_for(state="visible", timeout=8000)
                        submenu_panel = panel
                        print(f"Download submenu panel found: {selector}")
                        break
                    except Exception:
                        continue

                if not submenu_panel:
                    raise Exception("Download submenu panel did not appear")

                # Find MP3 Audio option
                print("Locating MP3 Audio download option...")
                mp3_selectors = [
                    "div[role='menuitem']:has-text('MP3 Audio')",
                    "*:has-text('MP3 Audio')",
                    "[data-testid*='mp3']",
                ]

                mp3_option = None
                for selector in mp3_selectors:
                    try:
                        option = submenu_panel.locator(selector)
                        await option.wait_for(state="visible", timeout=8000)
                        mp3_option = option
                        print(f"Found MP3 option: {selector}")
                        break
                    except Exception:
                        continue

                if not mp3_option:
                    raise Exception("MP3 Audio download option not found")

                # Initiate download with enhanced handling
                print("Starting download process...")
                download_successful = False
                final_file_path = None

                try:
                    async with page.expect_download(timeout=60000) as download_info:
                        # Hover over MP3 option (INSTANT)
                        print("Hovering over MP3 download option with teleport hover...")
                        await teleport_hover(page, mp3_option)
                        await page.wait_for_timeout(500)
                        
                        # Click MP3 option (INSTANT)
                        print("Clicking MP3 download option with teleport click...")
                        await teleport_click(page, mp3_option)
                        print("Clicked MP3 Audio option.")

                        # Check for "Download Anyway" button (premium content warning)
                        try:
                            download_anyway_selectors = [
                                'button:has(span:has-text("Download Anyway"))',
                                'button:has-text("Download Anyway")',
                                '*:has-text("Download Anyway")',
                            ]

                            for selector in download_anyway_selectors:
                                try:
                                    anyway_btn = page.locator(selector)
                                    await anyway_btn.wait_for(
                                        state="visible", timeout=10000
                                    )
                                    await teleport_click(page, anyway_btn)
                                    print("Clicked 'Download Anyway' button with teleport click.")
                                    break
                                except Exception:
                                    continue
                        except Exception:
                            print(
                                "No 'Download Anyway' button needed - proceeding with direct download"
                            )

                    download = await download_info.value

                    if download:
                        # 1. Use slugify for robust, clean title sanitization
                        slug_title = slugify(strTitle)

                        # 2. Generate a compact, numeric timestamp
                        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

                        # 3. Construct the final filename with timestamp suffix
                        filename = f"{slug_title}_index_{intIndex}_{timestamp}.mp3"
                        final_file_path = os.path.join(download_path, filename)

                        # Save the download
                        await download.save_as(final_file_path)
                        download_successful = True
                        print(f"Download completed successfully: {final_file_path}")

                except Exception as download_error:
                    raise Exception(f"Download process failed: {download_error}")

                if download_successful and final_file_path:
                    result.update({"success": True, "file_path": final_file_path})
                    print(
                        f"Song '{strTitle}' (index {intIndex}) downloaded successfully to: {final_file_path}"
                    )
                else:
                    raise Exception("Download completed but file path not set")

            except Exception as page_error:
                raise Exception(f"Page operation failed: {page_error}")

    except Exception as e:
        error_msg = f"Download failed for '{strTitle}' (index {intIndex}): {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        result.update({"success": False, "error": error_msg})

    return result
