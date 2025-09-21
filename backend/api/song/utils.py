"""Suno Automation - Song Utilities Module

This module provides utility functions for generating songs using Suno's API
and reviewing generated songs with Google AI Studio. It handles the entire
song creation workflow from lyric generation to quality review.
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

                song_card_selector = SunoSelectors.SONG_CARD
                initial_song_count = await page.locator(song_card_selector).count()
                print(f"[INFO] Initial song count: {initial_song_count}")

                await create_button.click()
                print("[ACTION] Create button clicked. Waiting for new songs to appear...")

                expected_song_count = initial_song_count + 2
                
                try:
                    # Wait for the number of songs to increase by 2
                    # Escape quotes in selector for JavaScript expression
                    escaped_selector = song_card_selector.replace('"', '\\"').replace("'", "\\'")
                    expression = f"() => document.querySelectorAll('{escaped_selector}').length >= {expected_song_count}"
                    print(f"[DEBUG] Waiting for songs with expression: {expression}")
                    await page.wait_for_function(expression, timeout=5000)

                    new_song_count = await page.locator(song_card_selector).count()
                    print(f"[SUCCESS] New songs detected. Current song count: {new_song_count} (Expected: {expected_song_count})")
                except Exception as e:
                    new_song_count = await page.locator(song_card_selector).count()
                    error_message = f"Timeout waiting for new songs. Initial: {initial_song_count}, Current: {new_song_count}. Error: {e}"
                    print(f"[ERROR] {error_message}")
                    print(f"[DEBUG] Song card selector used: {song_card_selector}")
                    print(f"[DEBUG] Expression attempted: {expression if 'expression' in locals() else 'Not generated'}")
                    raise Exception(error_message)

                print("[SUCCESS] Song creation initiated and page loaded.")

                #  wait additional time to ensure song is fully created
                await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["long"])

                #  get the song id from the newly generated 2 songs
                #  NOTE: Suno creates 2 songs per request, we will take the first 2 in the index

                # Extract song IDs from the song list elements
                # The song IDs are in the data-key attribute of the row elements
                print("[INFO] Attempting to extract song IDs from page elements...")
                
                song_ids = []
                try:
                    # Wait for song cards to be visible (clip-row elements)
                    await page.wait_for_selector(SunoSelectors.SONG_CARD, timeout=10000)

                    # Try multiple selectors to find song elements
                    song_elements = None
                    for selector in SunoSelectors.SONG_ELEMENT_SELECTORS:
                        song_elements = await page.query_selector_all(selector)
                        if song_elements:
                            print(f"Found song elements using selector: {selector}")
                            break
                    
                    if song_elements:
                        # Get the first 2 song IDs (indices 0 and 1)
                        for i, element in enumerate(song_elements[:2]):
                            # Extract song ID from the href attribute of the anchor tag
                            # Format: /song/{song_id}
                            song_link = await element.query_selector('a[href^="/song/"]')
                            if song_link:
                                href = await song_link.get_attribute('href')
                                if href and href.startswith('/song/'):
                                    song_id = href.split('/song/')[1].split('/')[0]
                                    if song_id:
                                        song_ids.append(song_id)
                                        print(f"[DEBUG] Extracted song ID at index {i} from href: {song_id}")

                            # Fallback to old method if href extraction fails
                            if not song_link or len(song_ids) <= i:
                                # Try to get song ID from primary attribute first
                                song_id = await element.get_attribute(SunoSelectors.SONG_ID_ATTRIBUTES["primary"])

                                # If not found, try fallback attribute
                                if not song_id:
                                    song_id = await element.get_attribute(SunoSelectors.SONG_ID_ATTRIBUTES["fallback"])

                                if song_id:
                                    song_ids.append(song_id)
                                    print(f"[DEBUG] Extracted song ID at index {i} from attribute: {song_id}")

                        if len(song_ids) >= 1:
                            suno_song_id = song_ids[0]  # Use the first song ID
                            print(f"[SUCCESS] Using first song ID: {suno_song_id}")
                            if len(song_ids) >= 2:
                                print(f"[INFO] Second song ID available: {song_ids[1]}")
                        else:
                            print("[WARNING] No song IDs found in href links or attributes")
                    else:
                        print("[WARNING] No song elements found on page")
                        
                except Exception as e:
                    print(f"[ERROR] Failed to extract song IDs from page: {e}")
                
                # Fallback: Check URL (unlikely to work with current Suno behavior)
                if not song_ids:
                    current_url = page.url
                    print(f"[DEBUG] Current URL after song creation: {current_url}")
                    
                    if "suno.com/song/" in current_url:
                        # This path is rarely taken since Suno doesn't redirect anymore
                        suno_song_id = current_url.split("suno.com/song/")[1].split("/")[0]
                        print(f"[RARE] Extracted suno_song_id from URL: {suno_song_id}")
                    else:
                        # Generate a temporary ID as last resort
                        print("[FALLBACK] Using temporary ID for database tracking")
                        temp_id = f"pending_{int(time.time())}"
                        suno_song_id = temp_id
                        print(f"[DEBUG] Generated temporary ID: {suno_song_id}")
                else:
                    suno_song_id = song_ids[0]

                # Save both song IDs to progress_v1_tbl for tracking
                # Suno creates 2 songs per request, we should save both
                print("[DATABASE] Attempting to save both songs to tblprogress_v1...")
                
                # Prepare data for both songs
                songs_to_save = []
                for idx, song_id in enumerate(song_ids[:2]):  # Take up to 2 song IDs
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
