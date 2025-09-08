"""Suno Song Download Module V2

This module provides a reusable class for downloading songs from Suno.com
using automated browser interactions with enhanced error handling and
teleport techniques for faster, more reliable downloads.
"""

import os
import datetime
import traceback
from typing import Dict, Any
from slugify import slugify
from camoufox import AsyncCamoufox
from playwright.async_api import Page, Locator
from configs.browser_config import config


class SunoDownloader:
    """
    A reusable class for downloading songs from Suno.com with advanced browser automation.
    
    Features:
    - Teleport techniques for fast, bot-resistant interactions
    - Robust error handling and element location
    - Configurable download paths
    - Duplicate song handling
    - Premium content warning bypass
    """
    
    def __init__(self, browser_config=None):
        """
        Initialize the SunoDownloader with optional browser configuration.
        
        Args:
            browser_config: Optional browser configuration to override defaults
        """
        self.config = browser_config or config
        
    async def _find_options_button(self, page: Page):
        """
        Finds the options/menu button (usually three dots) on the song page.
        
        Args:
            page (Page): Playwright Page instance
            
        Returns:
            Locator: The options button locator if found, None otherwise
        """
        print("Looking for options/menu button...")
        
        options_selectors = [
            'button[aria-label*="options"]',
            'button[aria-label*="menu"]',
            'button[aria-label*="More"]',
            'button[data-testid*="options"]',
            'button[data-testid*="menu"]',
            'button:has(svg[data-testid*="dots"])',
            'button:has(svg[class*="dots"])',
            '[role="button"]:has(svg)',
            'button svg[viewBox*="0 0 24 24"]'
        ]
        
        for selector in options_selectors:
            try:
                button = page.locator(selector).first
                await button.wait_for(state="visible", timeout=5000)
                print(f"Found options button with selector: {selector}")
                return button
            except Exception:
                continue
                
        print("Could not find options button with any known selector")
        return None
    
    async def teleport_click(self, page: Page, locator: Locator, button: str = "left", delay: int = 50):
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

    async def teleport_hover(self, page: Page, locator: Locator, delay: int = 50):
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

    async def download_song(
        self, 
        strTitle: str, 
        intIndex: int, 
        download_path: str,
        song_id: str = None
    ) -> Dict[str, Any]:
        """
        Downloads a song from Suno.com using automated browser interactions.

        Uses instantaneous "teleport" actions for speed, except for a regular 
        humanized hover on the download sub-menu trigger to ensure it opens correctly.

        Args:
            strTitle (str): Exact title of song to download
            intIndex (int): Song position (positive: 1-based from start, negative: from end)
            download_path (str): Directory to save downloaded MP3
            song_id (str, optional): Specific song ID to navigate to directly

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
                config=self.config,
                humanize=True,  # IMPORTANT: Keep this True for the one special hover to work
                i_know_what_im_doing=True,
            ) as browser:
                page = await browser.new_page()

                try:
                    # Validate page is available
                    if page.is_closed():
                        raise Exception("Browser page was closed before starting download")

                    # Navigate to specific song page or user's songs page
                    if song_id:
                        print(f"Navigating to specific song page: {song_id}")
                        await page.goto(
                            f"https://suno.com/song/{song_id}", wait_until="domcontentloaded", timeout=45000
                        )
                        print(f"Navigation completed. Current URL: {page.url}")


                        # Look for the options/menu button (usually three dots)
                        options_button = await self._find_options_button(page)
                        if not options_button:
                            return {
                                "success": False,
                                "error": "Could not find options button on song page"
                            }
                        
                        # Click the options button to open the dropdown menu
                        print("Clicking options button to open menu...")
                        await options_button.click()
                        await page.wait_for_timeout(1000)

                        # Wait for dropdown menu with enhanced detection
                        print("Waiting for dropdown menu to appear...")
                        context_menu_selectors = [
                            "div[data-radix-menu-content]",
                            "div[role='menu']",
                            "[data-radix-popper-content-wrapper]",
                            "div.radix-menu-content",
                            "[role='menu'][data-state='open']",
                        ]

                        context_menu = None
                        for selector in context_menu_selectors:
                            try:
                                menu = page.locator(selector).first
                                await menu.wait_for(state="visible", timeout=10000)
                                context_menu = menu
                                print(f"Dropdown menu found with selector: {selector}")
                                break
                            except Exception:
                                continue

                        if not context_menu:
                            raise Exception("Dropdown menu did not appear after clicking options button")

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
                                await self.teleport_hover(page, mp3_option)
                                await page.wait_for_timeout(500)
                                
                                # Click MP3 option (INSTANT)
                                print("Clicking MP3 download option with teleport click...")
                                await self.teleport_click(page, mp3_option)
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
                                            await self.teleport_click(page, anyway_btn)
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
                                # Song Renaming Logic:
                                # 1. Use slugify for robust, clean title sanitization (removes special chars, spaces->hyphens, lowercase)
                                slug_title = slugify(strTitle)

                                # 2. Generate a compact, numeric timestamp (YYYYMMDDHHMMSS format)
                                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

                                # 3. Construct the final filename: title_index_timestamp.mp3
                                # Example: "amazing-grace-verse-1-5_index_-1_20250830143022.mp3"
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
                        
                        # Verify we're on the correct song page
                        try:
                            await page.wait_for_url(f"https://suno.com/song/{song_id}**", timeout=30000)
                            print(f"Successfully confirmed navigation to song page: {song_id}")
                        except Exception as url_error:
                            raise Exception(f"Failed to reach song page: {url_error}")
                    else:
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
                    await self.teleport_click(page, target_song, button="right")

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
                            await self.teleport_hover(page, mp3_option)
                            await page.wait_for_timeout(500)
                            
                            # Click MP3 option (INSTANT)
                            print("Clicking MP3 download option with teleport click...")
                            await self.teleport_click(page, mp3_option)
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
                                        await self.teleport_click(page, anyway_btn)
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
                            # Song Renaming Logic:
                            # 1. Use slugify for robust, clean title sanitization (removes special chars, spaces->hyphens, lowercase)
                            slug_title = slugify(strTitle)

                            # 2. Generate a compact, numeric timestamp (YYYYMMDDHHMMSS format)
                            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

                            # 3. Construct the final filename: title_index_timestamp.mp3
                            # Example: "amazing-grace-verse-1-5_index_-1_20250830143022.mp3"
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


# Create a default instance for backward compatibility
default_downloader = SunoDownloader()

# Export the main download function for easy import
async def download_song_v2(
    strTitle: str, 
    intIndex: int, 
    download_path: str,
    song_id: str = None
) -> Dict[str, Any]:
    """
    Convenience function that uses the default downloader instance.
    
    Args:
        strTitle (str): Exact title of song to download
        intIndex (int): Song position (positive: 1-based from start, negative: from end)
        download_path (str): Directory to save downloaded MP3

    Returns:
        Dict[str, Any]: Result dictionary with download status and details
    """
    return await default_downloader.download_song(strTitle, intIndex, download_path, song_id)