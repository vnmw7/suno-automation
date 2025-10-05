"""
System: Suno Automation
Module: Song Utilities
File URL: backend/api/song/utils.py
Purpose: Automate song creation and review workflows against the Suno web interface.
"""

import os
import sys
import json
import re
import importlib.util
import traceback
import time
from typing import Dict, Any, Union
from camoufox import AsyncCamoufox
from configs.browser_config import config
from configs.suno_selectors import SunoSelectors

# Add path for download module import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils.download_song_v2 import download_song_v2

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

async def generate_song_handler(
    strBookName: str,
    intBookChapter: int,
    strVerseRange: str,
    strStyle: str,
    strTitle: str,
    blnCloseModal: bool = True,
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
        blnCloseModal (bool, optional): Close any blocking modal before typing lyrics. Defaults to True.

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
        blnCloseModal=blnCloseModal,
    )


async def close_modal_if_present(page) -> bool:
    """Ensure the Suno create page has no blocking modal before form entry."""
    print("[ACTION] Checking for blocking modals before lyric entry")
    arrSelectors = SunoSelectors.MODAL_CLOSE_BUTTON.get("selectors", [])
    intMaxCycles = SunoSelectors.MODAL_CLOSE_BUTTON.get("max_cycles", 1)
    blnClosedAny = False

    for intCycle in range(intMaxCycles):
        blnClosedThisCycle = False
        for strSelector in arrSelectors:
            try:
                locator = page.locator(strSelector)
                intCount = await locator.count()
            except Exception as err:
                print(f"[WARNING] Error evaluating modal close selector '{strSelector}': {err}")
                continue
            if intCount == 0:
                continue
            for intIndex in range(intCount):
                objButton = locator.nth(intIndex)
                try:
                    if not await objButton.is_visible():
                        continue
                    await objButton.click()
                    print(f"[SUCCESS] Closed modal via selector '{strSelector}'")
                    await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["short"])
                    blnClosedAny = True
                    blnClosedThisCycle = True
                except Exception as err:
                    print(f"[WARNING] Unable to click modal close button '{strSelector}': {err}")
            if blnClosedThisCycle:
                break
        if not blnClosedThisCycle:
            break

    if not blnClosedAny:
        print("[INFO] No blocking modal detected before lyric entry")
    else:
        print("[INFO] Modal cleanup completed before lyric entry")
    return blnClosedAny

async def generate_song(
    strBookName: str,
    intBookChapter: int,
    strVerseRange: str,
    strStyle: str,
    strTitle: str,
    blnCloseModal: bool = True,
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
        blnCloseModal (bool, optional): When True, dismiss any open modal dialog before entering lyrics. Defaults to True.

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
            headless=SunoSelectors.BROWSER_CONFIG["headless"],
            persistent_context=SunoSelectors.BROWSER_CONFIG["persistent_context"],
            user_data_dir=SunoSelectors.BROWSER_CONFIG["user_data_dir"],
            os=SunoSelectors.BROWSER_CONFIG["os"],
            config=config,
            humanize=SunoSelectors.BROWSER_CONFIG["humanize"],
            i_know_what_im_doing=SunoSelectors.BROWSER_CONFIG["i_know_what_im_doing"],
        ) as browser:
            page = await browser.new_page()
            print("[INFO] Navigating to suno.com...")
            await page.goto(SunoSelectors.CREATE_URL)
            print("[INFO] Waiting for page to load...")
            print("[SUCCESS] Page loaded.")
            print("[ACTION] Clicking Custom button...")

            print(f"[INFO] Current URL before Custom button: {page.url}")

            try:
                custom_button = page.locator(SunoSelectors.CUSTOM_BUTTON["primary"])
                await custom_button.wait_for(state="visible", timeout=SunoSelectors.CUSTOM_BUTTON["timeout"])
                print("[INFO] Custom button found and visible")
                await custom_button.click()
                await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["medium"])
                print("[SUCCESS] Custom button clicked successfully")
            except Exception as e:
                print(f"[WARNING] Error clicking Custom button: {e}")

                try:
                    alt_custom_button = page.locator(SunoSelectors.CUSTOM_BUTTON["fallback"])
                    await alt_custom_button.wait_for(state="visible", timeout=5000)
                    await alt_custom_button.click()
                    await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["medium"])
                    print("[SUCCESS] Used alternative Custom button selector")
                except Exception as e2:
                    print(f"[ERROR] Alternative Custom button also failed: {e2}")
                    raise Exception("Could not find or click Custom button")

            if blnCloseModal:
                await close_modal_if_present(page)

            # Get initial song count using a more specific, robust XPath selector
            initial_song_count = 0
            try:
                # Use specific parent container to avoid selector conflicts
                song_count_locator = page.locator("//div[contains(@class, 'e1qr1dqp4')]//div[contains(text(), 'songs')]")
                await song_count_locator.wait_for(state="visible", timeout=10000)
                count_text = await song_count_locator.inner_text()
                match = re.search(r'\d+', count_text)
                if match:
                    initial_song_count = int(match.group(0))
                print(f"[INFO] Initial song count: {initial_song_count}")
            except Exception as e:
                print(f"[WARNING] Could not determine initial song count: {e}. Assuming 0.")

            print("[ACTION] Filling strLyrics...")
            try:
                # Try the primary selector first (new UI)
                strLyrics_textarea = page.locator(SunoSelectors.LYRICS_INPUT["primary"])
                await strLyrics_textarea.wait_for(state="visible", timeout=SunoSelectors.LYRICS_INPUT["timeout"])
                await strLyrics_textarea.fill(strLyrics)
                print(f"[SUCCESS] strLyrics filled successfully: {len(strLyrics)} characters")
            except Exception as e:
                print(f"[WARNING] Primary lyrics selector failed: {e}, trying fallback...")
                try:
                    # Try fallback selector (old UI)
                    strLyrics_textarea = page.locator(SunoSelectors.LYRICS_INPUT["fallback"])
                    await strLyrics_textarea.wait_for(state="visible", timeout=5000)
                    await strLyrics_textarea.fill(strLyrics)
                    print(f"[SUCCESS] strLyrics filled successfully using fallback: {len(strLyrics)} characters")
                except Exception as e2:
                    print(f"[ERROR] Fallback lyrics selector also failed: {e2}")
                    raise Exception("Could not fill lyrics textarea")

            print("[ACTION] Filling style of music...")
            try:
                # Try the primary selector first (new UI)
                style_textarea = page.locator(SunoSelectors.STYLE_INPUT["primary"])
                await style_textarea.wait_for(state="visible", timeout=SunoSelectors.STYLE_INPUT["timeout"])
                await style_textarea.clear()
                await style_textarea.type(strStyle)
                print(f"[SUCCESS] Style filled successfully: {strStyle}")
            except Exception as e:
                print(f"[WARNING] Primary style selector failed: {e}, trying fallback...")
                try:
                    # Try fallback selector (old UI with data-testid)
                    style_textarea = page.locator(SunoSelectors.STYLE_INPUT["fallback"])
                    await style_textarea.wait_for(state="visible", timeout=5000)
                    await style_textarea.clear()
                    await style_textarea.type(strStyle)
                    print(f"[SUCCESS] Style filled successfully using fallback: {strStyle}")
                except Exception as e2:
                    print(f"[WARNING] Fallback style selector failed: {e2}, trying secondary fallback...")
                    try:
                        # Try secondary fallback (maxlength attribute)
                        style_textarea = page.locator(SunoSelectors.STYLE_INPUT["secondary_fallback"])
                        await style_textarea.wait_for(state="visible", timeout=5000)
                        await style_textarea.clear()
                        await style_textarea.type(strStyle)
                        print(f"[SUCCESS] Style filled successfully using secondary fallback: {strStyle}")
                    except Exception as e3:
                        print(f"[ERROR] All style selectors failed: {e3}")
                        raise Exception("Could not fill style textarea")

            print("[ACTION] Filling title...")
            try:
                # Try the primary selector first (new UI)
                title_input = page.locator(SunoSelectors.TITLE_INPUT["primary"])
                await title_input.wait_for(state="visible", timeout=SunoSelectors.TITLE_INPUT["timeout"])
                await title_input.clear()
                await title_input.type(strTitle)
                print(f"[SUCCESS] Title filled successfully: {strTitle}")
            except Exception as e:
                print(f"[WARNING] Primary title selector failed: {e}, trying fallback...")
                try:
                    # Try fallback selector (old placeholder text)
                    title_input = page.locator(SunoSelectors.TITLE_INPUT["fallback"])
                    await title_input.wait_for(state="visible", timeout=5000)
                    await title_input.clear()
                    await title_input.type(strTitle)
                    print(f"[SUCCESS] Title filled successfully using fallback: {strTitle}")
                except Exception as e2:
                    print(f"[WARNING] Fallback title selector failed: {e2}, trying secondary fallback...")
                    try:
                        # Try secondary fallback (partial placeholder match)
                        title_input = page.locator(SunoSelectors.TITLE_INPUT["secondary_fallback"])
                        await title_input.wait_for(state="visible", timeout=5000)
                        await title_input.clear()
                        await title_input.type(strTitle)
                        print(f"[SUCCESS] Title filled successfully using secondary fallback: {strTitle}")
                    except Exception as e3:
                        print(f"[ERROR] All title selectors failed: {e3}")
                        raise Exception("Could not fill title input")

            print("[ACTION] Creating song...")
            # Initialize suno_song_id early to avoid UnboundLocalError
            suno_song_id = None
            song_ids = []
            pg1_id = None
            pg1_ids = []

            try:
                create_button = None
                # Try primary selector
                try:
                    primary_selector = SunoSelectors.CREATE_BUTTON["primary"]
                    button = page.locator(primary_selector)
                    await button.wait_for(state="visible", timeout=SunoSelectors.CREATE_BUTTON["timeout"])
                    create_button = button
                    print(f"[INFO] Found create button with primary selector: {primary_selector}")
                except Exception as e:
                    print(f"[WARNING] Primary create button selector failed: {e}")

                    # Try fallback selector
                    try:
                        fallback_selector = SunoSelectors.CREATE_BUTTON["fallback"]
                        button = page.locator(fallback_selector)
                        await button.wait_for(state="visible", timeout=SunoSelectors.CREATE_BUTTON["timeout"])
                        create_button = button
                        print(f"[INFO] Found create button with fallback selector: {fallback_selector}")
                    except Exception as e2:
                        print(f"[WARNING] Fallback create button selector failed: {e2}")

                        # Try secondary fallback
                        try:
                            secondary_selector = SunoSelectors.CREATE_BUTTON["secondary_fallback"]
                            button = page.locator(secondary_selector)
                            await button.wait_for(state="visible", timeout=SunoSelectors.CREATE_BUTTON["timeout"])
                            create_button = button
                            print(f"[INFO] Found create button with secondary fallback: {secondary_selector}")
                        except Exception as e3:
                            print(f"[ERROR] All create button selectors failed: {e3}")

                if not create_button:
                    raise Exception("Could not find a visible create button.")

                print(f"[INFO] Using initial song count from before form filling: {initial_song_count}")

                await create_button.click()
                print("[ACTION] Create button clicked. Waiting for new songs to appear...")

                # Use hardened JavaScript with XPath to wait for the song count to increase
                wait_expression = f"""
                ((initialCount) => {{
                    const element = document.evaluate("//div[contains(@class, 'e1qr1dqp4')]//div[contains(text(), 'songs')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (!element || !element.innerText) {{
                        return false;
                    }}
                    const match = element.innerText.match(/\d+/);
                    if (!match) {{
                        return false;
                    }}
                    const newCount = parseInt(match[0], 10);
                    return newCount > initialCount;
                }})({initial_song_count})
                """

                try:
                    print(f"[INFO] Waiting for song count to become greater than {initial_song_count}...")
                    await page.wait_for_function(wait_expression, timeout=90000)  # 90-second timeout for generation
                    
                    # Get final count for logging
                    song_count_locator = page.locator("//div[contains(@class, 'e1qr1dqp4')]//div[contains(text(), 'songs')]")
                    final_count_text = await song_count_locator.inner_text()
                    final_match = re.search(r'\d+', final_count_text)
                    final_song_count = int(final_match.group(0)) if final_match else initial_song_count
                    new_songs_created = final_song_count - initial_song_count

                    print(f"[SUCCESS] Song generation confirmed. New count: {final_song_count}. New songs: {new_songs_created}")

                except Exception as e:
                    print(f"[ERROR] Timeout or error while waiting for new songs: {e}")
                    
                    # Take screenshot for debugging
                    screenshot_path = os.path.join("logs", f"failure_screenshot_{int(time.time())}.png")
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"[DEBUG] Screenshot saved to {screenshot_path}")

                    # Re-check count one last time to be sure
                    try:
                        final_count_text = await page.locator("//div[contains(@class, 'e1qr1dqp4')]//div[contains(text(), 'songs')]").inner_text()
                        final_match = re.search(r'\d+', final_count_text)
                        final_song_count = int(final_match.group(0)) if final_match else initial_song_count
                    except Exception:
                        final_song_count = initial_song_count

                    error_message = f"No new songs detected. Initial count: {initial_song_count}, Final count: {final_song_count}"
                    print(f"[ERROR] {error_message}")
                    raise Exception(error_message) from e

                print("[SUCCESS] Song creation initiated and page loaded.")

                #  wait additional time to ensure song is fully created
                await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["long"])

                #  get the song id from the newly generated songs
                #  NOTE: Suno creates 1-2 songs per request, positioned at the TOP of the list

                # Extract song IDs from the TOP of the song list (newest first)
                print("[INFO] Extracting song IDs from top of feed (newest first)...")

                song_ids = []
                try:
                    # Wait for song cards to be visible
                    await page.wait_for_selector(SunoSelectors.SONG_CARD, timeout=10000)

                    # Get all song elements (newest are at the top)
                    all_song_elements = []
                    for selector in SunoSelectors.SONG_ELEMENT_SELECTORS:
                        all_song_elements = await page.query_selector_all(selector)
                        if all_song_elements:
                            print(f"[DEBUG] Found song elements using selector: {selector}")
                            break

                    print(f"[DEBUG] Total song elements found: {len(all_song_elements)}")

                    # Check the top 4 songs (Suno typically generates 1-2, but may create up to 4)
                    # We check extra to ensure we catch all new songs even if some are premium
                    candidate_elements = all_song_elements[:4] if len(all_song_elements) >= 4 else all_song_elements
                    print(f"[DEBUG] Examining top {len(candidate_elements)} songs for new non-premium songs")

                    non_premium_songs = []

                    for idx, element in enumerate(candidate_elements):
                        # Check for premium preview indicator
                        is_premium = False
                        premium_indicator = await element.query_selector('span.css-1mqmbav.er4jr4i10')

                        if premium_indicator:
                            text_content = await premium_indicator.text_content()
                            if text_content and "v5 Preview" in text_content:
                                print(f"[DEBUG] Song {idx+1} is a premium preview - skipping")
                                is_premium = True

                        if not is_premium:
                            non_premium_songs.append(element)
                            print(f"[DEBUG] Song {idx+1} is a standard song - will extract ID")

                            # Stop after finding 2 non-premium songs (or whatever was created)
                            if len(non_premium_songs) >= 2:
                                break

                    print(f"[INFO] Found {len(non_premium_songs)} non-premium songs from top of list")

                    # Extract song IDs from the non-premium songs
                    for i, element in enumerate(non_premium_songs):
                        song_id = None

                        # Method 1: Try extracting from href (most reliable)
                        song_link = await element.query_selector('a[href^="/song/"]')
                        if song_link:
                            href = await song_link.get_attribute('href')
                            if href and href.startswith('/song/'):
                                song_id = href.split('/song/')[1].split('/')[0]
                                if song_id:
                                    song_ids.append(song_id)
                                    print(f"[SUCCESS] Extracted song ID {i+1} from href: {song_id}")

                        # Method 2: Fallback to data-key attribute
                        if not song_id:
                            song_id = await element.get_attribute('data-key')
                            if song_id:
                                song_ids.append(song_id)
                                print(f"[SUCCESS] Extracted song ID {i+1} from data-key: {song_id}")

                        # Method 3: Final fallback to other attributes
                        if not song_id:
                            song_id = await element.get_attribute(SunoSelectors.SONG_ID_ATTRIBUTES["primary"])
                            if not song_id:
                                song_id = await element.get_attribute(SunoSelectors.SONG_ID_ATTRIBUTES["fallback"])

                            if song_id:
                                song_ids.append(song_id)
                                print(f"[SUCCESS] Extracted song ID {i+1} from fallback attribute: {song_id}")

                        if not song_id:
                            print(f"[WARNING] Could not extract song ID from non-premium song {i+1}")

                    if song_ids:
                        suno_song_id = song_ids[0]
                        print(f"[SUCCESS] Primary song ID: {suno_song_id}")
                        if len(song_ids) > 1:
                            print(f"[SUCCESS] Secondary song ID: {song_ids[1]}")
                    else:
                        print("[WARNING] No valid song IDs found in top songs")

                except Exception as e:
                    print(f"[ERROR] Failed to extract song IDs: {e}")
                    traceback.print_exc()

                # Fallback logic if no IDs were extracted
                if not song_ids:
                    print("[FALLBACK] Using temporary ID for database tracking")
                    temp_id = f"pending_{int(time.time())}"
                    suno_song_id = temp_id
                    print(f"[DEBUG] Generated temporary ID: {suno_song_id}")
                else:
                    suno_song_id = song_ids[0]

                # Save both song IDs to progress_v1_tbl for tracking
                # Suno creates 1-2 songs per request, we should save all created songs
                print("[DATABASE] Attempting to save both songs to tblprogress_v1...")
                
                # Prepare data for both songs
                songs_to_save = []
                for idx, song_id in enumerate(song_ids):  # Process all extracted song IDs (1-2 songs)
                    print(f"[DATABASE] Data to save for song {idx + 1}:")
                    print(f"  - pg1_song_struct_id: {song_structure_id}")
                    print(f"  - pg1_song_id: {song_id}")
                    print(f"  - pg1_style: {strStyle}")
                    print(f"  - pg1_lyrics length: {len(strLyrics) if strLyrics else 0} chars")
                    
                    songs_to_save.append({
                        "pg1_song_struct_id": song_structure_id,
                        "pg1_lyrics": strLyrics,
                        "pg1_status": 0,
                        "pg1_reviews": 0,
                        "pg1_song_id": song_id,
                        "pg1_style": strStyle,
                    })
                
                # If we only have one song ID (fallback case), still save it
                if not songs_to_save and suno_song_id:
                    songs_to_save.append({
                        "pg1_song_struct_id": song_structure_id,
                        "pg1_lyrics": strLyrics,
                        "pg1_status": 0,
                        "pg1_reviews": 0,
                        "pg1_song_id": suno_song_id,
                        "pg1_style": strStyle,
                    })
                
                try:
                    # Insert all songs in a single batch operation
                    response = (
                        supabase.table("tblprogress_v1")
                        .insert(songs_to_save)
                        .execute()
                    )
                    
                    # DEBUG: Log the full response structure
                    print("[DATABASE] Full response from Supabase:")
                    print("  - response.data: {}".format(response.data))
                    print("  - response.data type: {}".format(type(response.data)))
                    print(f"[DATABASE] Number of records inserted: {len(response.data) if response.data else 0}")
                    
                    # Store all pg1_ids from the response
                    pg1_ids = []
                    if response.data:
                        print("[DATABASE] response.data exists, extracting pg1_ids...")
                        for i, record in enumerate(response.data):
                            print("[DATABASE] Record {}: {}".format(i + 1, record))
                            
                            # Try to get pg1_id from the response
                            record_pg1_id = record.get('pg1_id')
                            if record_pg1_id is None:
                                # Try alternative column names
                                record_pg1_id = record.get('id')
                                if record_pg1_id:
                                    print(f"[DATABASE] Found pg1_id under 'id' column for record {i + 1}: {record_pg1_id}")
                            else:
                                print(f"[DATABASE] Successfully extracted pg1_id for record {i + 1}: {record_pg1_id}")
                            
                            if record_pg1_id:
                                pg1_ids.append(record_pg1_id)
                        
                        # Use the first pg1_id for backward compatibility
                        pg1_id = pg1_ids[0] if pg1_ids else None
                        
                        # Log all available keys for debugging
                        if response.data:
                            print(f"[DATABASE] Available keys in first record: {response.data[0].keys()}")
                            print("[DATABASE] All pg1_ids saved: {}".format(pg1_ids))
                    else:
                        print("[DATABASE] WARNING: response.data is empty or None")
                        pg1_id = None
                        
                except Exception as db_error:
                    print(f"[DATABASE] ERROR saving to Supabase: {db_error}")
                    print(f"[DATABASE] Error type: {type(db_error).__name__}")
                    print("[DATABASE] Traceback: {}".format(traceback.format_exc()))
                    # Continue without pg1_id but log the issue
                    pg1_id = None
                
                # Validate pg1_id before returning
                if not pg1_id:
                    print("[WARNING] pg1_id is missing or invalid (value: {})".format(pg1_id))
                    print("[WARNING] This means:")
                    print("[WARNING]   1. Songs were created on Suno.com successfully")
                    print("[WARNING]   2. Database save may have failed OR")
                    print("[WARNING]   3. pg1_id was not returned in the response")
                    print("[WARNING]   4. Review process will use fallback method")
                else:
                    print("[SUCCESS] pg1_ids successfully obtained: {}".format(pg1_ids if 'pg1_ids' in locals() else pg1_id))
                    print("[SUCCESS] Both songs saved to database for AI review")

                # Return both song IDs and all pg1_ids if available
                return {
                    "success": True,
                    "song_id": suno_song_id,  # First song ID for backward compatibility
                    "song_ids": song_ids if song_ids else [suno_song_id],  # All song IDs
                    "lyrics": strLyrics,
                    "style": strStyle,
                    "title": strTitle,
                    "pg1_id": pg1_id,  # First pg1_id for backward compatibility
                    "pg1_ids": pg1_ids if 'pg1_ids' in locals() and pg1_ids else [pg1_id] if pg1_id else None,  # All pg1_ids
                }

            except Exception as e:
                print(f"[ERROR] Error clicking Create button: {e}")
                raise Exception("Could not click Create button")

    except Exception as e:
        print(f"[ERROR] An error occurred in generate_song: {e}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": f"Song generation failed: {str(e)}",
            "song_id": suno_song_id if 'suno_song_id' in locals() else None,
            "lyrics": strLyrics if 'strLyrics' in locals() else None,
            "style": strStyle,
            "title": strTitle
        }

# Download module already imported at top of file

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
    strTitle: str, intIndex: int, download_path: str, song_id: str = None
) -> Dict[str, Any]:
    """
    Downloads a song from Suno.com using the v2 download module.
    
    This function delegates to the download_song_v2 module which provides:
    - Enhanced error handling for common failure points
    - Robust element location with multiple fallback strategies
    - Configurable download paths
    - Duplicate song handling
    - Premium content warning bypass
    - Teleport techniques for fast, bot-resistant interactions

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
    """
    return await download_song_v2(strTitle, intIndex, download_path, song_id)


