"""Suno Automation - Song Generation Utilities V2

This module provides enhanced song download functionality with pg1_song_id based naming.
It includes both legacy (for backward compatibility) and v2 versions of the download function.
"""

import os
import datetime
from typing import Dict, Any, Optional
from slugify import slugify
from camoufox import AsyncCamoufox
from playwright.async_api import Page, Locator
import traceback

# Import the config from the existing location
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from configs.browser_config import config


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


async def download_song_handler_legacy(
    strTitle: str, intIndex: int, download_path: str
) -> Dict[str, Any]:
    """
    LEGACY VERSION - Downloads a song using title-based naming convention.
    
    This is the original download function that uses title_index_timestamp naming.
    Kept for backward compatibility.

    Args:
        strTitle (str): Exact title of song to download
        intIndex (int): Song position (positive: 1-based from start, negative: from end)
        download_path (str): Directory to save downloaded MP3

    Returns:
        Dict[str, Any]: Result dictionary with success status and file path
    """
    # Import the original function from api/song/utils.py
    from api.song.utils import download_song_handler as original_download
    return await original_download(strTitle, intIndex, download_path)


async def download_song_handler_v2(
    strTitle: str, 
    intIndex: int, 
    download_path: str,
    pg1_song_id: Optional[int] = None,
    suno_song_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    V2 VERSION - Downloads a song using pg1_song_id based naming convention.
    
    This enhanced version prioritizes pg1_song_id for file naming, providing
    better database correlation and tracking. Falls back to suno_song_id or
    title-based naming if pg1_song_id is not available.

    Naming priority:
    1. pg1_{pg1_song_id}_{timestamp}.mp3 (if pg1_song_id provided)
    2. suno_{suno_song_id}_{timestamp}.mp3 (if suno_song_id provided)
    3. {slug_title}_index_{intIndex}_{timestamp}.mp3 (fallback)

    Args:
        strTitle (str): Exact title of song to download
        intIndex (int): Song position (positive: 1-based from start, negative: from end)
        download_path (str): Directory to save downloaded MP3
        pg1_song_id (int, optional): Database ID from tblprogress_v1
        suno_song_id (str, optional): Suno platform song ID

    Returns:
        Dict[str, Any]: Result dictionary with:
            - success (bool): Download status
            - file_path (str): Saved file path if successful
            - error (str): Failure reason if applicable
            - song_title (str): Original song title
            - song_index (int): Original song index
            - pg1_song_id (int): Database ID if provided
            - naming_method (str): Which naming convention was used
    """
    result = {
        "success": False,
        "file_path": None,
        "error": None,
        "song_title": strTitle,
        "song_index": intIndex,
        "pg1_song_id": pg1_song_id,
        "naming_method": None
    }

    try:
        # Ensure download directory exists
        os.makedirs(download_path, exist_ok=True)

        print(f"[V2] Starting enhanced download process for: '{strTitle}' at index {intIndex}")
        if pg1_song_id:
            print(f"[V2] Using pg1_song_id: {pg1_song_id} for file naming")
        elif suno_song_id:
            print(f"[V2] Using suno_song_id: {suno_song_id} for file naming")
        else:
            print(f"[V2] No ID provided, will use title-based naming")

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
                print("[V2] Navigating to Suno user songs page...")
                await page.goto(
                    "https://suno.com/me", wait_until="domcontentloaded", timeout=45000
                )
                print(f"[V2] Navigation completed. Current URL: {page.url}")

                # Verify we're on the correct page
                try:
                    await page.wait_for_url("https://suno.com/me**", timeout=30000)
                    print("[V2] Successfully confirmed navigation to /me page")
                except Exception as url_error:
                    raise Exception(f"Failed to reach user songs page: {url_error}")

                # Wait for page content to load
                print("[V2] Waiting for page content to stabilize...")
                try:
                    await page.wait_for_load_state("networkidle", timeout=30000)
                except Exception as load_error:
                    print(f"[V2] Warning: Network idle timeout (continuing anyway): {load_error}")

                await page.wait_for_timeout(3000)  # Additional stability wait

                # Wait for the last song title to be visible
                print("[V2] Waiting for song list to load...")
                try:
                    last_song_locator = page.locator(f'span[title="{strTitle}"]').last
                    await last_song_locator.wait_for(state="visible", timeout=45000)
                    print("[V2] Song list appears to be loaded. Proceeding...")
                except Exception as e:
                    raise Exception(f"Timed out waiting for song list to become visible: {e}")

                # Find song elements
                print(f"[V2] Searching for songs with title: '{strTitle}'")
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
                            print(f"[V2] Found {count} song(s) using pattern: {pattern}")
                            break
                    except Exception:
                        print(f"[V2] Pattern failed: {pattern}")
                        continue

                if not song_elements:
                    raise Exception(f"No songs found with title '{strTitle}' using any search pattern")

                # Validate and calculate target index
                song_count = await song_elements.count()
                print(f"[V2] Total songs found with title '{strTitle}': {song_count}")

                if song_count == 0:
                    raise Exception(f"No songs found with title '{strTitle}'")

                # Handle duplicate hidden elements
                if song_count > 1 and song_count % 2 == 0:
                    visible_song_count = song_count // 2
                    start_index_offset = visible_song_count
                    print(f"[V2] Adjusting for duplicates. Visible songs: {visible_song_count}")
                else:
                    visible_song_count = song_count
                    start_index_offset = 0
                    print("[V2] Assuming all found songs are visible.")

                # Validate and normalize index
                if intIndex == 0:
                    raise Exception("Index cannot be 0. Use positive or negative indexing.")

                target_index = 0
                if intIndex > 0:
                    if not (1 <= intIndex <= visible_song_count):
                        raise Exception(f"Invalid index {intIndex}. Must be between 1 and {visible_song_count}.")
                    target_index = start_index_offset + (intIndex - 1)
                else:  # intIndex < 0
                    if not (-visible_song_count <= intIndex <= -1):
                        raise Exception(f"Invalid index {intIndex}. Must be between -{visible_song_count} and -1.")
                    target_index = start_index_offset + (visible_song_count + intIndex)

                target_song = song_elements.nth(target_index)
                print(f"[V2] Targeting song at index {intIndex} (0-based: {target_index})")

                # Scroll to target song
                print("[V2] Ensuring target song is visible...")
                try:
                    await target_song.scroll_into_view_if_needed(timeout=20000)
                    print("[V2] Scrolled using Playwright scroll_into_view_if_needed")
                except Exception as scroll_error:
                    print(f"[V2] Playwright scroll failed: {scroll_error}. Trying JavaScript scroll...")
                    try:
                        await target_song.evaluate(
                            "element => element.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'smooth' })"
                        )
                        await page.wait_for_timeout(2000)
                        print("[V2] Used JavaScript scrollIntoView")
                    except Exception as js_scroll_error:
                        print(f"[V2] JavaScript scroll also failed: {js_scroll_error}")

                # Verify target song is visible
                try:
                    await target_song.wait_for(state="visible", timeout=15000)
                    print("[V2] Target song element confirmed visible")
                except Exception:
                    raise Exception(f"Target song at index {intIndex} is not visible after scrolling")

                # Right-click to open context menu
                print(f"[V2] Right-clicking on song at index {intIndex}...")
                await teleport_click(page, target_song, button="right")
                await page.wait_for_timeout(1000)

                # Wait for context menu
                print("[V2] Waiting for context menu to appear...")
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
                        print(f"[V2] Context menu found with selector: {selector}")
                        break
                    except Exception:
                        continue

                if not context_menu:
                    raise Exception("Context menu did not appear after right-click")

                await page.wait_for_timeout(500)

                # Find download submenu trigger
                print("[V2] Locating download submenu trigger...")
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
                        print(f"[V2] Found download trigger: {trigger_selector}")
                        break
                    except Exception:
                        continue

                if not download_trigger:
                    raise Exception("Download option not found in context menu")

                # CRITICAL: Use NORMAL hover to ensure menu triggers
                print("[V2] Performing REGULAR (humanized) hover on Download trigger...")
                await download_trigger.hover()  # Use the standard hover to trigger the sub-menu
                await page.wait_for_timeout(1000)

                # Wait for download submenu panel
                print("[V2] Waiting for download submenu panel...")
                download_trigger_id = await download_trigger.get_attribute("id")

                submenu_selectors = []
                if download_trigger_id:
                    submenu_selectors.append(
                        f"div[data-radix-menu-content][data-state='open'][aria-labelledby='{download_trigger_id}']"
                    )
                submenu_selectors.extend([
                    "div[data-radix-menu-content][data-state='open'][role='menu']",
                    "*[role='menu'][data-state='open']",
                ])

                submenu_panel = None
                for selector in submenu_selectors:
                    try:
                        panel = page.locator(selector).last
                        await panel.wait_for(state="visible", timeout=8000)
                        submenu_panel = panel
                        print(f"[V2] Download submenu panel found: {selector}")
                        break
                    except Exception:
                        continue

                if not submenu_panel:
                    raise Exception("Download submenu panel did not appear")

                # Find MP3 Audio option
                print("[V2] Locating MP3 Audio download option...")
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
                        print(f"[V2] Found MP3 option: {selector}")
                        break
                    except Exception:
                        continue

                if not mp3_option:
                    raise Exception("MP3 Audio download option not found")

                # Initiate download
                print("[V2] Starting download process...")
                download_successful = False
                final_file_path = None

                try:
                    async with page.expect_download(timeout=60000) as download_info:
                        # Hover over MP3 option
                        print("[V2] Hovering over MP3 download option...")
                        await teleport_hover(page, mp3_option)
                        await page.wait_for_timeout(500)
                        
                        # Click MP3 option
                        print("[V2] Clicking MP3 download option...")
                        await teleport_click(page, mp3_option)
                        print("[V2] Clicked MP3 Audio option.")

                        # Check for "Download Anyway" button
                        try:
                            download_anyway_selectors = [
                                'button:has(span:has-text("Download Anyway"))',
                                'button:has-text("Download Anyway")',
                                '*:has-text("Download Anyway")',
                            ]

                            for selector in download_anyway_selectors:
                                try:
                                    anyway_btn = page.locator(selector)
                                    await anyway_btn.wait_for(state="visible", timeout=10000)
                                    await teleport_click(page, anyway_btn)
                                    print("[V2] Clicked 'Download Anyway' button.")
                                    break
                                except Exception:
                                    continue
                        except Exception:
                            print("[V2] No 'Download Anyway' button needed - proceeding with direct download")

                    download = await download_info.value

                    if download:
                        # Enhanced V2 Naming Logic with pg1_song_id priority
                        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                        
                        if pg1_song_id:
                            # Priority 1: Use pg1_song_id for database correlation
                            filename = f"pg1_{pg1_song_id}_{timestamp}.mp3"
                            result["naming_method"] = "pg1_song_id"
                            print(f"[V2] Using pg1_song_id naming: {filename}")
                        elif suno_song_id:
                            # Priority 2: Use suno_song_id if available
                            filename = f"suno_{suno_song_id}_{timestamp}.mp3"
                            result["naming_method"] = "suno_song_id"
                            print(f"[V2] Using suno_song_id naming: {filename}")
                        else:
                            # Priority 3: Fallback to title-based naming
                            slug_title = slugify(strTitle)
                            filename = f"{slug_title}_index_{intIndex}_{timestamp}.mp3"
                            result["naming_method"] = "title_based"
                            print(f"[V2] Using title-based naming: {filename}")
                        
                        final_file_path = os.path.join(download_path, filename)

                        # Save the download
                        await download.save_as(final_file_path)
                        download_successful = True
                        print(f"[V2] Download completed successfully: {final_file_path}")

                except Exception as download_error:
                    raise Exception(f"Download process failed: {download_error}")

                if download_successful and final_file_path:
                    result.update({"success": True, "file_path": final_file_path})
                    print(f"[V2] Song '{strTitle}' (index {intIndex}) downloaded successfully to: {final_file_path}")
                else:
                    raise Exception("Download completed but file path not set")

            except Exception as page_error:
                raise Exception(f"Page operation failed: {page_error}")

    except Exception as e:
        error_msg = f"[V2] Download failed for '{strTitle}' (index {intIndex}): {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        result.update({"success": False, "error": error_msg})

    return result


# Default export - use v2 version as the main handler
download_song_handler = download_song_handler_v2


async def download_both_songs_v2(title: str, temp_dir: str, pg1_ids: list = None) -> Dict[str, Any]:
    """
    Enhanced version of download_both_songs that uses pg1_ids for file naming.
    
    Downloads both songs generated by Suno (which creates 2 songs per request),
    using pg1_ids when available for better database tracking.
    
    Args:
        title (str): Song title
        temp_dir (str): Directory to save downloads
        pg1_ids (list, optional): List of pg1_ids from database [id1, id2]
        
    Returns:
        Dict[str, Any]: Download results with file paths and metadata
    """
    try:
        downloaded_songs = []
        
        # Prepare pg1_ids for each song
        pg1_id_1 = pg1_ids[0] if pg1_ids and len(pg1_ids) > 0 else None
        pg1_id_2 = pg1_ids[1] if pg1_ids and len(pg1_ids) > 1 else None
        
        # Download song at index -1 (last/newest song)
        print(f"[V2] Downloading song at index -1 with pg1_id: {pg1_id_1}")
        download_1 = await download_song_handler_v2(
            strTitle=title,
            intIndex=-1,
            download_path=temp_dir,
            pg1_song_id=pg1_id_1
        )
        
        if download_1["success"]:
            downloaded_songs.append({
                "file_path": download_1["file_path"],
                "index": -1,
                "title": title,
                "pg1_id": pg1_id_1,
                "naming_method": download_1.get("naming_method")
            })
            print(f"[V2] Successfully downloaded song -1: {download_1['file_path']}")
        else:
            print(f"[V2] Failed to download song -1: {download_1.get('error')}")
        
        # Download song at index -2 (second to last song)
        print(f"[V2] Downloading song at index -2 with pg1_id: {pg1_id_2}")
        download_2 = await download_song_handler_v2(
            strTitle=title,
            intIndex=-2,
            download_path=temp_dir,
            pg1_song_id=pg1_id_2
        )
        
        if download_2["success"]:
            downloaded_songs.append({
                "file_path": download_2["file_path"],
                "index": -2,
                "title": title,
                "pg1_id": pg1_id_2,
                "naming_method": download_2.get("naming_method")
            })
            print(f"[V2] Successfully downloaded song -2: {download_2['file_path']}")
        else:
            print(f"[V2] Failed to download song -2: {download_2.get('error')}")
        
        if len(downloaded_songs) == 0:
            return {
                "success": False,
                "error": "Failed to download any songs",
                "downloads": []
            }
        elif len(downloaded_songs) == 1:
            print(f"[V2] Warning: Only downloaded 1 of 2 songs")
            
        return {
            "success": True,
            "downloads": downloaded_songs,
            "message": f"Downloaded {len(downloaded_songs)} of 2 songs using enhanced naming"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Download process failed: {str(e)}",
            "downloads": []
        }