"""
System: Suno Automation
Module: Song Download V2
Purpose: Download songs from Suno with browser automation and return file path and song ID.

Suno Song Download Module V2

This module provides a reusable class for downloading songs from Suno.com
using automated browser interactions with enhanced error handling and
teleport techniques for faster, more reliable downloads.
"""

import os
import traceback
from datetime import datetime
from typing import Dict, Any
from slugify import slugify
from camoufox import AsyncCamoufox
from playwright.async_api import Page, Locator
from configs.browser_config import config
from configs.suno_selectors import SunoSelectors


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

        options_selectors = SunoSelectors.OPTIONS_BUTTON["selectors"]
        timeout = SunoSelectors.OPTIONS_BUTTON.get("timeout", 5000)

        for selector in options_selectors:
            try:
                button = page.locator(selector).first
                await button.wait_for(state="visible", timeout=timeout)
                print(f"Found options button with selector: {selector}")
                return button
            except Exception:
                continue

        print("Could not find options button with any known selector")
        return None

    async def _click_options_button(self, page: Page, options_button: Locator):
        """
        Reliably clicks the options button with multiple fallback methods.

        The options button often has data-mouseover-id attribute requiring hover first.

        Args:
            page (Page): Playwright Page instance
            options_button (Locator): The options button locator

        Returns:
            bool: True if click succeeded, False otherwise
        """
        try:
            # First, always hover to activate any mouseover handlers
            print("🔄 Hovering over options button to activate handlers...")
            await self.teleport_hover(page, options_button, delay=200)

            # Try regular click first
            try:
                print("🔄 Attempting regular click on options button...")
                await options_button.click(timeout=5000)
                print("✅ Options button clicked successfully (regular click)")
                return True
            except Exception as click_error:
                print(f"⚠️ Regular click failed: {str(click_error)[:100]}")

                # Try teleport click as first fallback
                try:
                    print("🔄 Trying teleport click as fallback...")
                    await self.teleport_click(page, options_button)
                    print("✅ Options button clicked successfully (teleport click)")
                    return True
                except Exception as teleport_error:
                    print(f"⚠️ Teleport click failed: {str(teleport_error)[:100]}")

                    # Try force click as last resort
                    try:
                        print("🔄 Trying force click as last resort...")
                        await options_button.click(force=True, timeout=5000)
                        print("✅ Options button clicked successfully (force click)")
                        return True
                    except Exception as force_error:
                        print(f"⚠️ Force click failed: {str(force_error)[:100]}")

                        # Final attempt: dispatch click event directly
                        try:
                            print("🔄 Dispatching click event directly...")
                            await options_button.dispatch_event('click')
                            print("✅ Options button clicked successfully (dispatch event)")
                            return True
                        except Exception as dispatch_error:
                            print(f"❌ All click methods failed: {str(dispatch_error)[:100]}")
                            return False
        except Exception as e:
            print(f"❌ Error in _click_options_button: {str(e)}")
            return False
    
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

    async def _is_mp3_enabled(self, mp3_option: Locator) -> tuple[bool, str]:
        """
        Check if MP3 download option is enabled and clickable.

        Returns:
            Tuple of (is_enabled, reason_if_disabled)
        """
        try:
            # Log element details for debugging
            tag_name = await mp3_option.evaluate("el => el.tagName.toLowerCase()")
            aria_label = await mp3_option.get_attribute("aria-label")
            print(f"[DEBUG-MP3] Checking element: tag={tag_name}, aria-label={aria_label}")

            # Check disabled attribute
            disabled_attr = await mp3_option.get_attribute("disabled")
            print(f"[DEBUG-MP3] disabled attribute: {disabled_attr}")
            if disabled_attr is not None:
                return False, f"has [disabled] attribute (value: '{disabled_attr}')"

            # Check aria-disabled
            aria_disabled = await mp3_option.get_attribute("aria-disabled")
            print(f"[DEBUG-MP3] aria-disabled: {aria_disabled}")
            if aria_disabled and aria_disabled.lower() == "true":
                return False, "aria-disabled=true"

            # Check CSS classes for disabled indicators
            class_attr = await mp3_option.get_attribute("class") or ""
            print(f"[DEBUG-MP3] class attribute: {class_attr[:100]}...")  # First 100 chars

            # Split classes and check for actual disabled state classes
            # Avoid matching Tailwind conditional classes like "disabled:opacity-50"
            class_list = class_attr.lower().split()
            disabled_indicators = ["opacity-50", "pointer-events-none", "cursor-not-allowed"]

            # Check for standalone "disabled" class (not as part of "disabled:")
            if "disabled" in class_list:  # Only match if "disabled" is a standalone class
                return False, "has 'disabled' class"

            # Check for other disabled indicators
            for indicator in disabled_indicators:
                if indicator in class_list:  # Check for exact class match
                    return False, f"class suggests disabled: {indicator}"

            # Check computed style for pointer-events
            pointer_events = await mp3_option.evaluate("el => getComputedStyle(el).pointerEvents")
            print(f"[DEBUG-MP3] computed pointer-events: {pointer_events}")
            if pointer_events and pointer_events.lower() == "none":
                return False, "pointer-events: none"

            # Check visibility
            is_visible = await mp3_option.is_visible()
            print(f"[DEBUG-MP3] is_visible: {is_visible}")
            if not is_visible:
                return False, "not visible"

            # Check bounding box
            box = await mp3_option.bounding_box()
            print(f"[DEBUG-MP3] bounding box: {box}")
            if not box or box["width"] < 1 or box["height"] < 1:
                return False, f"zero-size bounding box (box={box})"

            print("[DEBUG-MP3] All checks passed - button is enabled!")
            return True, None

        except Exception as e:
            print(f"[DEBUG-MP3] Exception during check: {type(e).__name__}: {str(e)}")
            return False, f"check failed: {type(e).__name__}: {str(e)}"

    async def _close_menus(self, page: Page):
        """
        Close any open menus by pressing ESC key twice.
        """
        try:
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(200)
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            print("🔄 Menus closed")
        except Exception as e:
            print(f"⚠️ Could not close menus: {e}")

    async def _wait_for_mp3_ready(
        self,
        page: Page,
        options_button: Locator,
        max_wait_seconds: int = 180,
        check_interval_seconds: int = 5
    ) -> Locator:
        """
        Wait for MP3 option to become enabled by repeatedly opening menu and checking.

        Args:
            page: Page instance
            options_button: Options button locator
            max_wait_seconds: Maximum time to wait (default 3 minutes)
            check_interval_seconds: Time between checks (default 5 seconds)

        Returns:
            Enabled MP3 option locator

        Raises:
            Exception if MP3 never becomes enabled
        """
        import time
        start_time = time.time()
        attempt = 0
        last_reason = "unknown"

        print(f"⏳ [WAIT-MP3] Waiting up to {max_wait_seconds}s for MP3 to become enabled...")

        while (time.time() - start_time) < max_wait_seconds:
            attempt += 1

            try:
                # Open options menu using the reliable click helper
                print(f"\n🔄 [WAIT-MP3] Attempt {attempt} - Opening menu...")

                # Use the dedicated method that handles all fallback scenarios
                click_success = await self._click_options_button(page, options_button)
                if not click_success:
                    print("⚠️ [WAIT-MP3] Failed to click options button, retrying...")
                    await self._close_menus(page)
                    await page.wait_for_timeout(check_interval_seconds * 1000)
                    continue

                await page.wait_for_timeout(1000)

                # Wait for dropdown menu
                context_menu_selectors = SunoSelectors.CONTEXT_MENU["selectors"]
                context_menu = None

                for selector in context_menu_selectors:
                    try:
                        menu = page.locator(selector).first
                        await menu.wait_for(state="visible", timeout=5000)
                        context_menu = menu
                        break
                    except Exception:
                        continue

                if not context_menu:
                    print("⚠️ [WAIT-MP3] Menu didn't appear, retrying...")
                    await self._close_menus(page)
                    await page.wait_for_timeout(check_interval_seconds * 1000)
                    continue

                # Find download trigger
                download_trigger = None
                for trigger_selector in SunoSelectors.DOWNLOAD_TRIGGER["selectors"]:
                    try:
                        trigger = context_menu.locator(trigger_selector)
                        await trigger.wait_for(state="visible", timeout=3000)
                        download_trigger = trigger
                        break
                    except Exception:
                        continue

                if not download_trigger:
                    print("⚠️ [WAIT-MP3] Download trigger not found, retrying...")
                    await self._close_menus(page)
                    await page.wait_for_timeout(check_interval_seconds * 1000)
                    continue

                # Hover to open submenu (keep humanized hover)
                print("🔄 [WAIT-MP3] Opening download submenu...")
                await download_trigger.hover()
                await page.wait_for_timeout(1000)

                # Find submenu panel
                download_trigger_id = await download_trigger.get_attribute("id")
                submenu_selectors = []
                if download_trigger_id:
                    submenu_selectors.append(
                        f"div[data-radix-menu-content][data-state='open'][aria-labelledby='{download_trigger_id}']"
                    )
                submenu_selectors.extend(SunoSelectors.DOWNLOAD_SUBMENU["selectors"])

                submenu_panel = None
                for selector in submenu_selectors:
                    try:
                        panel = page.locator(selector).last
                        await panel.wait_for(state="visible", timeout=3000)
                        submenu_panel = panel
                        break
                    except Exception:
                        continue

                if not submenu_panel:
                    print("⚠️ [WAIT-MP3] Submenu didn't appear, retrying...")
                    await self._close_menus(page)
                    await page.wait_for_timeout(check_interval_seconds * 1000)
                    continue

                # Find MP3 option
                mp3_option = None
                for selector in SunoSelectors.MP3_OPTION["selectors"]:
                    try:
                        option = submenu_panel.locator(selector)
                        await option.wait_for(state="visible", timeout=3000)

                        # Verify we found an actual button element, not a parent container
                        tag_name = await option.evaluate("el => el.tagName.toLowerCase()")
                        if tag_name != "button":
                            print(f"⚠️ [WAIT-MP3] Selector matched {tag_name} instead of button, trying next selector...")
                            continue

                        mp3_option = option
                        print(f"✅ [WAIT-MP3] Found MP3 button element with selector: {selector}")
                        break
                    except Exception:
                        continue

                if not mp3_option:
                    print("⚠️ [WAIT-MP3] MP3 option not found, retrying...")
                    await self._close_menus(page)
                    await page.wait_for_timeout(check_interval_seconds * 1000)
                    continue

                # Check if MP3 is enabled
                is_enabled, reason = await self._is_mp3_enabled(mp3_option)

                if is_enabled:
                    elapsed = int(time.time() - start_time)
                    print(f"✅ [WAIT-MP3] MP3 is now enabled! (after {elapsed}s, {attempt} attempts)")
                    return mp3_option
                else:
                    last_reason = reason or "unknown"
                    print(f"⚠️ [WAIT-MP3] MP3 still disabled: {last_reason}")

                # Close menu and wait before retry
                await self._close_menus(page)

            except Exception as e:
                print(f"⚠️ [WAIT-MP3] Error during check: {e}")
                last_reason = str(e)
                await self._close_menus(page)

            # Wait before next check
            await page.wait_for_timeout(check_interval_seconds * 1000)

        # Timeout reached
        elapsed = int(time.time() - start_time)
        raise Exception(
            f"MP3 option did not become enabled within {max_wait_seconds}s "
            f"(checked {attempt} times, last reason: {last_reason})"
        )

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
            "song_id": None,
        }

        # Initialize extracted_song_id variable for use throughout the function
        extracted_song_id = None

        try:
            # Ensure download directory exists
            os.makedirs(download_path, exist_ok=True)

            print(f"\n{'='*80}")
            print("📥 [DOWNLOAD-START] Starting enhanced download process")
            print(f"📥 [DOWNLOAD-START] Title: '{strTitle}'")
            print(f"📥 [DOWNLOAD-START] Index: {intIndex}")
            print(f"📥 [DOWNLOAD-START] Song ID: {song_id if song_id else 'None (will navigate to /me)'}")
            print(f"📥 [DOWNLOAD-START] Download path: {download_path}")
            print(f"📥 [DOWNLOAD-START] Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}")

            async with AsyncCamoufox(
                headless=True,
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
                        print("\n📍 [NAVIGATION] Direct song page navigation")
                        print(f"📍 [NAVIGATION] Target URL: https://suno.com/song/{song_id}")
                        print("📍 [NAVIGATION] Starting navigation...")
                        await page.goto(
                            f"https://suno.com/song/{song_id}", wait_until="domcontentloaded", timeout=45000
                        )
                        print("📍 [NAVIGATION] ✅ Navigation completed")
                        print(f"📍 [NAVIGATION] Current URL: {page.url}")


                        # Look for the options/menu button (usually three dots)
                        options_button = await self._find_options_button(page)
                        if not options_button:
                            return {
                                "success": False,
                                "error": "Could not find options button on song page"
                            }

                        # Retry mechanism for download process
                        MAX_DOWNLOAD_RETRIES = 3
                        download_attempt = 0
                        download_successful = False
                        final_file_path = None

                        while download_attempt < MAX_DOWNLOAD_RETRIES and not download_successful:
                            download_attempt += 1
                            print(f"\n🔄 [DOWNLOAD-ATTEMPT] Attempt {download_attempt} of {MAX_DOWNLOAD_RETRIES}")
                            print(f"🔄 [DOWNLOAD-ATTEMPT] Starting download process for '{strTitle}'...")

                            try:
                                # Wait for MP3 to be enabled using our new helper
                                print("📥 [DOWNLOAD] Checking if song is ready for download...")
                                mp3_option = await self._wait_for_mp3_ready(
                                    page=page,
                                    options_button=options_button,
                                    max_wait_seconds=120,  # 2 minutes max per attempt
                                    check_interval_seconds=5
                                )

                                # Use the extracted_song_id if available for filename
                                if 'extracted_song_id' in locals() and extracted_song_id:
                                    song_id_for_filename = extracted_song_id
                                else:
                                    song_id_for_filename = song_id

                                # Initiate download with enhanced handling
                                print("Starting download process...")

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
                                            download_anyway_selectors = SunoSelectors.DOWNLOAD_ANYWAY_BUTTON["selectors"]

                                            download_anyway_timeout = SunoSelectors.DOWNLOAD_ANYWAY_BUTTON.get("timeout", 10000)
                                            for selector in download_anyway_selectors:
                                                try:
                                                    anyway_btn = page.locator(selector)
                                                    await anyway_btn.wait_for(
                                                        state="visible", timeout=download_anyway_timeout
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
                                        print("\n💾 [SAVE] Processing downloaded file...")
                                        # 1. Use slugify for robust, clean title sanitization (removes special chars, spaces->hyphens, lowercase)
                                        slug_title = slugify(strTitle)
                                        print(f"💾 [SAVE] Slugified title: {slug_title}")

                                        # 2. Generate a compact, numeric timestamp (YYYYMMDDHHMMSS format)
                                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                                        print(f"💾 [SAVE] Timestamp: {timestamp}")

                                        # 3. Construct the final filename: title_songId_timestamp.mp3
                                        # Example: "amazing-grace-verse-1-5_abc123def456_20250830143022.mp3"
                                        # Use song_id_for_filename if set (contains extracted_song_id or original song_id)
                                        if 'song_id_for_filename' in locals() and song_id_for_filename:
                                            filename = f"{slug_title}_{song_id_for_filename}_{timestamp}.mp3"
                                            print(f"💾 [SAVE] Using song_id for filename: {song_id_for_filename}")
                                        else:
                                            filename = f"{slug_title}_index_{intIndex}_{timestamp}.mp3"
                                            print(f"💾 [SAVE] No song_id available, using index: {intIndex}")

                                        print(f"💾 [SAVE] Final filename: {filename}")
                                        final_file_path = os.path.join(download_path, filename)
                                        print(f"💾 [SAVE] Full path: {final_file_path}")

                                        # Save the download
                                        print("💾 [SAVE] Saving file...")
                                        await download.save_as(final_file_path)
                                        download_successful = True

                                        # Verify file was saved
                                        if os.path.exists(final_file_path):
                                            file_size = os.path.getsize(final_file_path)
                                            print("💾 [SAVE] ✅ File saved successfully")
                                            print(f"💾 [SAVE] File size: {file_size:,} bytes")
                                            print(f"✅ [DOWNLOAD-ATTEMPT] Attempt {download_attempt} succeeded!")
                                            break  # Exit the retry loop
                                        else:
                                            print("💾 [SAVE] ⚠️ File save reported success but file not found!")
                                    else:
                                        raise Exception("Download object was not returned")

                                except Exception as download_error:
                                    error_msg = str(download_error)
                                    print(f"❌ [DOWNLOAD-ATTEMPT] Attempt {download_attempt} failed: {error_msg}")

                                    # Check if we have retries left
                                    if download_attempt < MAX_DOWNLOAD_RETRIES:
                                        # Close any open menus before retry
                                        await self._close_menus(page)

                                        # Progressive wait based on attempt number
                                        wait_time = min(5 * download_attempt, 15)  # 5s, 10s, 15s max
                                        print(f"⏳ [RETRY] Will retry in {wait_time} seconds (no page refresh)...")
                                        await page.wait_for_timeout(wait_time * 1000)

                                        # Verify options button is still available
                                        options_button = await self._find_options_button(page)
                                        if not options_button:
                                            print("❌ [RETRY] Could not find options button, breaking retry loop")
                                            break
                                    else:
                                        # On last attempt, raise the error
                                        print(f"❌ [DOWNLOAD-ATTEMPT] All {MAX_DOWNLOAD_RETRIES} attempts failed!")
                                        raise Exception(f"Download failed after {MAX_DOWNLOAD_RETRIES} attempts: {download_error}")

                            except Exception as outer_error:
                                # This catches errors from wait_for_mp3_ready or other failures
                                error_msg = str(outer_error)
                                print(f"❌ [DOWNLOAD-ATTEMPT] Error on attempt {download_attempt}: {error_msg}")

                                if download_attempt < MAX_DOWNLOAD_RETRIES:
                                    # Check if it's a specific MP3 not ready error
                                    if "did not become enabled" in error_msg:
                                        print("⚠️ [RETRY] Song still processing, will retry...")
                                    else:
                                        print("🔄 [RETRY] Will retry after error...")

                                    await self._close_menus(page)
                                    await page.wait_for_timeout(3000)

                                    # Verify options button is still available
                                    options_button = await self._find_options_button(page)
                                    if not options_button:
                                        print("❌ [RETRY] Could not find options button, breaking retry loop")
                                        break
                                else:
                                    raise outer_error

                        # After the retry loop, check final status

                        if download_successful and final_file_path:
                            result.update({"success": True, "file_path": final_file_path})
                            print("\n✅ [DOWNLOAD-SUCCESS] ===========")
                            print("✅ [DOWNLOAD-SUCCESS] Download completed successfully!")
                            print(f"✅ [DOWNLOAD-SUCCESS] Song: '{strTitle}'")
                            print(f"✅ [DOWNLOAD-SUCCESS] Index: {intIndex}")
                            print(f"✅ [DOWNLOAD-SUCCESS] Path: {final_file_path}")
                            print(f"✅ [DOWNLOAD-SUCCESS] Song ID in result: {extracted_song_id if 'extracted_song_id' in locals() and extracted_song_id else song_id}")
                            print(f"✅ [DOWNLOAD-SUCCESS] Succeeded on attempt: {download_attempt} of {MAX_DOWNLOAD_RETRIES}")
                            print("✅ [DOWNLOAD-SUCCESS] ===========")
                        else:
                            raise Exception(f"Download failed after {MAX_DOWNLOAD_RETRIES} attempts: File not saved properly")
                        
                        # Verify we're on the correct song page
                        try:
                            await page.wait_for_url(f"https://suno.com/song/{song_id}**", timeout=30000)
                            print(f"Successfully confirmed navigation to song page: {song_id}")
                        except Exception as url_error:
                            raise Exception(f"Failed to reach song page: {url_error}")
                    else:
                        print("\n📍 [NAVIGATION] User songs page navigation")
                        print("📍 [NAVIGATION] Target URL: https://suno.com/me")
                        print("📍 [NAVIGATION] Starting navigation...")
                        await page.goto(
                            "https://suno.com/me", wait_until="domcontentloaded", timeout=45000
                        )
                        print("📍 [NAVIGATION] ✅ Navigation completed")
                        print(f"📍 [NAVIGATION] Current URL: {page.url}")

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

                        # Try to extract song ID from the song element
                        print("\n🔍 [EXTRACT-ID] Attempting to extract song ID from element...")
                        extracted_song_id = None
                        try:
                            # Try to find a link or element with the song ID in href or data attributes
                            song_link = target_song.locator("a[href*='/song/']").first
                            song_href = await song_link.get_attribute("href")
                            if song_href and "/song/" in song_href:
                                extracted_song_id = song_href.split("/song/")[-1].split("?")[0].split("/")[0]
                                print(f"🔍 [EXTRACT-ID] ✅ Extracted song ID from href: {extracted_song_id}")
                            else:
                                print("🔍 [EXTRACT-ID] No song ID found in href attribute")
                        except Exception as e:
                            print(f"🔍 [EXTRACT-ID] Failed to extract from href: {type(e).__name__}")
                            try:
                                # Alternative: Look for data attributes that might contain song ID
                                data_id = await target_song.get_attribute("data-song-id")
                                if data_id:
                                    extracted_song_id = data_id
                                    print(f"🔍 [EXTRACT-ID] ✅ Extracted song ID from data attribute: {extracted_song_id}")
                                else:
                                    print("🔍 [EXTRACT-ID] No data-song-id attribute found")
                            except Exception:
                                print("🔍 [EXTRACT-ID] ⚠️ Could not extract song ID from element")
                                print("🔍 [EXTRACT-ID] Will use index in filename instead")
                        
                        # Right-click to open context menu (INSTANT)
                        print(f"Right-clicking on song at index {intIndex}...")
                        await self.teleport_click(page, target_song, button="right")

                        await page.wait_for_timeout(1000)

                        # Wait for context menu with enhanced detection
                        print("Waiting for context menu to appear...")
                        context_menu_selectors = SunoSelectors.CONTEXT_MENU["selectors"]

                        context_menu = None
                        context_menu_timeout = SunoSelectors.CONTEXT_MENU.get("timeout", 10000)
                        for selector in context_menu_selectors:
                            try:
                                menu = page.locator(selector)
                                await menu.wait_for(state="visible", timeout=context_menu_timeout)
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
                        download_triggers = SunoSelectors.DOWNLOAD_TRIGGER["selectors"]

                        download_trigger = None
                        download_trigger_timeout = SunoSelectors.DOWNLOAD_TRIGGER.get("timeout", 8000)
                        for trigger_selector in download_triggers:
                            try:
                                trigger = context_menu.locator(trigger_selector)
                                await trigger.wait_for(state="visible", timeout=download_trigger_timeout)
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
                        # Add the rest from config
                        submenu_selectors.extend(SunoSelectors.DOWNLOAD_SUBMENU["selectors"])

                        submenu_panel = None
                        submenu_timeout = SunoSelectors.DOWNLOAD_SUBMENU.get("timeout", 8000)
                        for selector in submenu_selectors:
                            try:
                                panel = page.locator(selector).last
                                await panel.wait_for(state="visible", timeout=submenu_timeout)
                                submenu_panel = panel
                                print(f"Download submenu panel found: {selector}")
                                break
                            except Exception:
                                continue

                        if not submenu_panel:
                            raise Exception("Download submenu panel did not appear")

                        # Find MP3 Audio option
                        print("Locating MP3 Audio download option...")
                        mp3_selectors = SunoSelectors.MP3_OPTION["selectors"]

                        mp3_option = None
                        mp3_timeout = SunoSelectors.MP3_OPTION.get("timeout", 8000)
                        for selector in mp3_selectors:
                            try:
                                option = submenu_panel.locator(selector)
                                await option.wait_for(state="visible", timeout=mp3_timeout)

                                # Verify we found an actual button element, not a parent container
                                tag_name = await option.evaluate("el => el.tagName.toLowerCase()")
                                if tag_name != "button":
                                    print(f"⚠️ Selector matched {tag_name} instead of button, trying next selector...")
                                    continue

                                mp3_option = option
                                print(f"Found MP3 button element: {selector}")
                                break
                            except Exception:
                                continue

                        if not mp3_option:
                            raise Exception("MP3 Audio download option not found")

                        # Check if MP3 is enabled before proceeding
                        is_enabled, reason = await self._is_mp3_enabled(mp3_option)

                        # If disabled, wait and retry with right-click
                        retry_count = 0
                        MAX_ENABLE_RETRIES = 10  # Maximum retries for waiting for MP3 to be enabled

                        while not is_enabled and retry_count < MAX_ENABLE_RETRIES:
                            retry_count += 1
                            print(f"⚠️ [WAIT-MP3] MP3 option is disabled: {reason}")
                            print(f"⏳ [WAIT-MP3] Retry {retry_count}/{MAX_ENABLE_RETRIES} - Waiting for song to be ready...")

                            # Close menu and wait
                            await self._close_menus(page)

                            # Progressive wait: 5s, 10s, 15s, then 10s for remaining
                            wait_time = min(5 * min(retry_count, 3), 15)
                            print(f"⏳ [WAIT-MP3] Waiting {wait_time} seconds before retry...")
                            await page.wait_for_timeout(wait_time * 1000)

                            # Right-click again to open fresh menu
                            print("🔄 [WAIT-MP3] Right-clicking on song again...")
                            await self.teleport_click(page, target_song, button="right")
                            await page.wait_for_timeout(1000)

                            # Re-navigate through menu
                            context_menu = None
                            for selector in context_menu_selectors:
                                try:
                                    menu = page.locator(selector)
                                    await menu.wait_for(state="visible", timeout=5000)
                                    context_menu = menu
                                    break
                                except Exception:
                                    continue

                            if not context_menu:
                                print("⚠️ [WAIT-MP3] Context menu didn't appear, will retry...")
                                continue

                            # Find download trigger again
                            download_trigger = None
                            for trigger_selector in download_triggers:
                                try:
                                    trigger = context_menu.locator(trigger_selector)
                                    await trigger.wait_for(state="visible", timeout=3000)
                                    download_trigger = trigger
                                    break
                                except Exception:
                                    continue

                            if not download_trigger:
                                print("⚠️ [WAIT-MP3] Download trigger not found, will retry...")
                                continue

                            # Hover to open submenu
                            await download_trigger.hover()
                            await page.wait_for_timeout(1000)

                            # Find submenu panel
                            download_trigger_id = await download_trigger.get_attribute("id")
                            submenu_selectors = []
                            if download_trigger_id:
                                submenu_selectors.append(
                                    f"div[data-radix-menu-content][data-state='open'][aria-labelledby='{download_trigger_id}']"
                                )
                            submenu_selectors.extend(SunoSelectors.DOWNLOAD_SUBMENU["selectors"])

                            submenu_panel = None
                            for selector in submenu_selectors:
                                try:
                                    panel = page.locator(selector).last
                                    await panel.wait_for(state="visible", timeout=3000)
                                    submenu_panel = panel
                                    break
                                except Exception:
                                    continue

                            if not submenu_panel:
                                print("⚠️ [WAIT-MP3] Submenu didn't appear, will retry...")
                                continue

                            # Find MP3 option again
                            mp3_option = None
                            for selector in mp3_selectors:
                                try:
                                    option = submenu_panel.locator(selector)
                                    await option.wait_for(state="visible", timeout=3000)

                                    # Verify we found an actual button element
                                    tag_name = await option.evaluate("el => el.tagName.toLowerCase()")
                                    if tag_name != "button":
                                        continue

                                    mp3_option = option
                                    break
                                except Exception:
                                    continue

                            if not mp3_option:
                                print("⚠️ [WAIT-MP3] MP3 option not found after retry, will retry...")
                                continue

                            # Check if now enabled
                            is_enabled, reason = await self._is_mp3_enabled(mp3_option)

                            if is_enabled:
                                print(f"✅ [WAIT-MP3] MP3 is now enabled after {retry_count} retries!")
                                break

                        if not is_enabled:
                            raise Exception(f"MP3 option remained disabled after {MAX_ENABLE_RETRIES} retries. Last reason: {reason}")

                        # Use the extracted_song_id if available for filename
                        if 'extracted_song_id' in locals() and extracted_song_id:
                            song_id_for_filename = extracted_song_id
                        else:
                            song_id_for_filename = song_id

                        # Initiate download with enhanced handling
                        print("📥 [DOWNLOAD] Starting download process (MP3 is enabled)...")
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
                                    download_anyway_selectors = SunoSelectors.DOWNLOAD_ANYWAY_BUTTON["selectors"]

                                    download_anyway_timeout = SunoSelectors.DOWNLOAD_ANYWAY_BUTTON.get("timeout", 10000)
                                    for selector in download_anyway_selectors:
                                        try:
                                            anyway_btn = page.locator(selector)
                                            await anyway_btn.wait_for(
                                                state="visible", timeout=download_anyway_timeout
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
                                print("\n💾 [SAVE] Processing downloaded file...")
                                # 1. Use slugify for robust, clean title sanitization (removes special chars, spaces->hyphens, lowercase)
                                slug_title = slugify(strTitle)
                                print(f"💾 [SAVE] Slugified title: {slug_title}")

                                # 2. Generate a compact, numeric timestamp (YYYYMMDDHHMMSS format)
                                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                                print(f"💾 [SAVE] Timestamp: {timestamp}")

                                # 3. Construct the final filename: title_songId_timestamp.mp3
                                # Example: "amazing-grace-verse-1-5_abc123def456_20250830143022.mp3"
                                # Use song_id_for_filename if set (contains extracted_song_id or original song_id)
                                if 'song_id_for_filename' in locals() and song_id_for_filename:
                                    filename = f"{slug_title}_{song_id_for_filename}_{timestamp}.mp3"
                                    print(f"💾 [SAVE] Using song_id for filename: {song_id_for_filename}")
                                else:
                                    filename = f"{slug_title}_index_{intIndex}_{timestamp}.mp3"
                                    print(f"💾 [SAVE] No song_id available, using index: {intIndex}")

                                print(f"💾 [SAVE] Final filename: {filename}")
                                final_file_path = os.path.join(download_path, filename)
                                print(f"💾 [SAVE] Full path: {final_file_path}")

                                # Save the download
                                print("💾 [SAVE] Saving file...")
                                await download.save_as(final_file_path)
                                download_successful = True

                                # Verify file was saved
                                if os.path.exists(final_file_path):
                                    file_size = os.path.getsize(final_file_path)
                                    print("💾 [SAVE] ✅ File saved successfully")
                                    print(f"💾 [SAVE] File size: {file_size:,} bytes")
                                else:
                                    print("💾 [SAVE] ⚠️ File save reported success but file not found!")

                        except Exception as download_error:
                            raise Exception(f"Download process failed: {download_error}")

                        if download_successful and final_file_path:
                            # Determine best-available song_id to return
                            returned_song_id = None
                            try:
                                if 'extracted_song_id' in locals() and extracted_song_id:
                                    returned_song_id = extracted_song_id
                                    print(f"📊 [RESULT] Using extracted song ID: {returned_song_id}")
                                elif song_id:
                                    returned_song_id = song_id
                                    print(f"📊 [RESULT] Using original song ID: {returned_song_id}")
                                else:
                                    print("📊 [RESULT] No song ID available for result")
                            except Exception:
                                pass

                            result.update({
                                "success": True,
                                "file_path": final_file_path,
                                "song_id": returned_song_id,
                            })
                            print("\n✅ [DOWNLOAD-SUCCESS] ===========")
                            print("✅ [DOWNLOAD-SUCCESS] Download completed successfully!")
                            print(f"✅ [DOWNLOAD-SUCCESS] Song: '{strTitle}'")
                            print(f"✅ [DOWNLOAD-SUCCESS] Index: {intIndex}")
                            print(f"✅ [DOWNLOAD-SUCCESS] Path: {final_file_path}")
                            print(f"✅ [DOWNLOAD-SUCCESS] Song ID in result: {returned_song_id}")
                            print("✅ [DOWNLOAD-SUCCESS] ===========")
                        else:
                            raise Exception("Download completed but file path not set")

                except Exception as page_error:
                    raise Exception(f"Page operation failed: {page_error}")

        except Exception as e:
            error_msg = f"Download failed for '{strTitle}' (index {intIndex}): {str(e)}"
            print("\n❌ [DOWNLOAD-ERROR] ===========")
            print("❌ [DOWNLOAD-ERROR] Download failed!")
            print(f"❌ [DOWNLOAD-ERROR] Song: '{strTitle}'")
            print(f"❌ [DOWNLOAD-ERROR] Index: {intIndex}")
            print(f"❌ [DOWNLOAD-ERROR] Error type: {type(e).__name__}")
            print(f"❌ [DOWNLOAD-ERROR] Error message: {str(e)}")
            print("❌ [DOWNLOAD-ERROR] Full traceback:")
            print(traceback.format_exc())
            print("❌ [DOWNLOAD-ERROR] ===========")
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
