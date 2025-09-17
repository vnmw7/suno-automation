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
from typing import Dict, Any, Union
from camoufox import AsyncCamoufox
from configs.browser_config import config
from configs.suno_selectors import SunoSelectors

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
            print("Navigating to suno.com...")
            await page.goto(SunoSelectors.CREATE_URL)
            print("Waiting for page to load...")
            print("Page loaded.")
            print("Clicking Custom button...")

            print(f"Current URL before Custom button: {page.url}")

            try:
                custom_button = page.locator(SunoSelectors.CUSTOM_BUTTON["primary"])
                await custom_button.wait_for(state="visible", timeout=SunoSelectors.CUSTOM_BUTTON["timeout"])
                print("Custom button found and visible")
                await custom_button.click()
                await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["medium"])
                print("Custom button clicked successfully")
            except Exception as e:
                print(f"Error clicking Custom button: {e}")

                try:
                    alt_custom_button = page.locator(SunoSelectors.CUSTOM_BUTTON["fallback"])
                    await alt_custom_button.wait_for(state="visible", timeout=5000)
                    await alt_custom_button.click()
                    await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["medium"])
                    print("Used alternative Custom button selector")
                except Exception as e2:
                    print(f"Alternative Custom button also failed: {e2}")
                    raise Exception("Could not find or click Custom button")

            print("Filling strLyrics...")
            try:
                # Try the primary selector first (new UI)
                strLyrics_textarea = page.locator(SunoSelectors.LYRICS_INPUT["primary"])
                await strLyrics_textarea.wait_for(state="visible", timeout=SunoSelectors.LYRICS_INPUT["timeout"])
                await strLyrics_textarea.clear()
                await strLyrics_textarea.type(strLyrics)
                await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["medium"])
                print(f"strLyrics filled successfully: {len(strLyrics)} characters")
            except Exception as e:
                print(f"Primary lyrics selector failed: {e}, trying fallback...")
                try:
                    # Try fallback selector (old UI)
                    strLyrics_textarea = page.locator(SunoSelectors.LYRICS_INPUT["fallback"])
                    await strLyrics_textarea.wait_for(state="visible", timeout=5000)
                    await strLyrics_textarea.clear()
                    await strLyrics_textarea.type(strLyrics)
                    await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["medium"])
                    print(f"strLyrics filled successfully using fallback: {len(strLyrics)} characters")
                except Exception as e2:
                    print(f"Fallback lyrics selector also failed: {e2}")
                    raise Exception("Could not fill lyrics textarea")

            print("Filling tags...")
            try:
                tags_textarea = page.locator(SunoSelectors.TAGS_INPUT["primary"])
                await tags_textarea.wait_for(state="visible", timeout=SunoSelectors.TAGS_INPUT["timeout"])
                await tags_textarea.clear()
                await tags_textarea.type(strStyle)
                await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["medium"])
                print(f"Tags filled successfully: {strStyle}")
            except Exception as e:
                print(f"Primary tags selector failed: {e}, trying fallback...")
                try:
                    tags_textarea = page.locator(SunoSelectors.TAGS_INPUT["fallback"])
                    await tags_textarea.wait_for(state="visible", timeout=5000)
                    await tags_textarea.clear()
                    await tags_textarea.type(strStyle)
                    await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["medium"])
                    print(f"Tags filled successfully using fallback: {strStyle}")
                except Exception as e2:
                    print(f"Fallback tags selector also failed: {e2}")
                    raise Exception("Could not fill tags textarea")

            print("Filling title...")
            try:
                title_input = page.locator(SunoSelectors.TITLE_INPUT["primary"])
                await title_input.wait_for(state="visible", timeout=SunoSelectors.TITLE_INPUT["timeout"])
                await title_input.clear()
                await title_input.type(strTitle)
                await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["medium"])
                print(f"Title filled successfully: {strTitle}")
            except Exception as e:
                print(f"Primary title selector failed: {e}, trying fallback...")
                try:
                    title_input = page.locator(SunoSelectors.TITLE_INPUT["fallback"])
                    await title_input.wait_for(state="visible", timeout=5000)
                    await title_input.clear()
                    await title_input.type(strTitle)
                    await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["medium"])
                    print(f"Title filled successfully using fallback: {strTitle}")
                except Exception as e2:
                    print(f"Fallback title selector also failed: {e2}")
                    raise Exception("Could not fill title input")

            print("Creating song...")
            try:
                create_button = None
                for selector in SunoSelectors.CREATE_BUTTON["selectors"]:
                    try:
                        button = (
                            page.locator(selector).nth(1)
                            if "has-text" in selector
                            else page.locator(selector)
                        )
                        await button.wait_for(state="visible", timeout=SunoSelectors.CREATE_BUTTON["timeout"])
                        create_button = button
                        print(f"Found create button with selector: {selector}")
                        break
                    except Exception:
                        print(f"Create button not found with selector: {selector}")
                        continue

                if not create_button:
                    raise Exception("Could not find a visible create button.")

                song_play_button_selector = SunoSelectors.SONG_PLAY_BUTTON
                initial_song_count = await page.locator(song_play_button_selector).count()
                print(f"Initial song count: {initial_song_count}")

                await create_button.click()
                print("Create button clicked. Waiting for new songs to appear...")

                expected_song_count = initial_song_count + 2
                
                try:
                    # Wait for the number of songs to increase by 2
                    expression = f"() => document.querySelectorAll(\"{song_play_button_selector}\").length >= {expected_song_count}"
                    await page.wait_for_function(expression, timeout=5000)
                    
                    new_song_count = await page.locator(song_play_button_selector).count()
                    print(f"New songs detected. Current song count: {new_song_count}")
                except Exception as e:
                    new_song_count = await page.locator(song_play_button_selector).count()
                    error_message = f"Timeout waiting for new songs. Initial: {initial_song_count}, Current: {new_song_count}. Error: {e}"
                    print(error_message)
                    raise Exception(error_message)

                print("Song creation initiated and page loaded.")

                #  wait additional time to ensure song is fully created
                await page.wait_for_timeout(SunoSelectors.WAIT_TIMES["long"])

                #  get the song id from the newly generated 2 songs
                #  NOTE: Suno creates 2 songs per request, we will take the first 2 in the index

                # Extract song IDs from the song list elements
                # The song IDs are in the data-key attribute of the row elements
                print("[DEBUG] Attempting to extract song IDs from page elements...")
                
                song_ids = []
                try:
                    # Wait for song rows to be visible
                    await page.wait_for_selector(SunoSelectors.SONG_ROW, timeout=10000)

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
                            # Try to get song ID from primary attribute first
                            song_id = await element.get_attribute(SunoSelectors.SONG_ID_ATTRIBUTES["primary"])

                            # If not found, try fallback attribute
                            if not song_id:
                                song_id = await element.get_attribute(SunoSelectors.SONG_ID_ATTRIBUTES["fallback"])
                            
                            if song_id:
                                song_ids.append(song_id)
                                print(f"[DEBUG] Extracted song ID at index {i}: {song_id}")
                        
                        if len(song_ids) >= 1:
                            suno_song_id = song_ids[0]  # Use the first song ID
                            print(f"[SUCCESS] Using first song ID: {suno_song_id}")
                            if len(song_ids) >= 2:
                                print(f"[INFO] Second song ID available: {song_ids[1]}")
                        else:
                            print("[WARNING] No song IDs found in data-clip-id or data-key attributes")
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
                        print(f"[FALLBACK] Using temporary ID for database tracking")
                        import time
                        temp_id = f"pending_{int(time.time())}"
                        suno_song_id = temp_id
                        print(f"[DEBUG] Generated temporary ID: {suno_song_id}")
                else:
                    suno_song_id = song_ids[0]
                
                pg1_id = None  # Initialize pg1_id

                # Save both song IDs to progress_v1_tbl for tracking
                # Suno creates 2 songs per request, we should save both
                print(f"[DATABASE] Attempting to save both songs to tblprogress_v1...")
                
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
                    print(f"[DATABASE] Full response from Supabase:")
                    print(f"  - response.data: {response.data}")
                    print(f"  - response.data type: {type(response.data)}")
                    print(f"[DATABASE] Number of records inserted: {len(response.data) if response.data else 0}")
                    
                    # Store all pg1_ids from the response
                    pg1_ids = []
                    if response.data:
                        print(f"[DATABASE] response.data exists, extracting pg1_ids...")
                        for i, record in enumerate(response.data):
                            print(f"[DATABASE] Record {i + 1}: {record}")
                            
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
                            print(f"[DATABASE] All pg1_ids saved: {pg1_ids}")
                    else:
                        print(f"[DATABASE] WARNING: response.data is empty or None")
                        pg1_id = None
                        
                except Exception as db_error:
                    print(f"[DATABASE] ERROR saving to Supabase: {db_error}")
                    print(f"[DATABASE] Error type: {type(db_error).__name__}")
                    import traceback
                    print(f"[DATABASE] Traceback: {traceback.format_exc()}")
                    # Continue without pg1_id but log the issue
                    pg1_id = None
                
                # Validate pg1_id before returning
                if not pg1_id:
                    print(f"[WARNING] pg1_id is missing or invalid (value: {pg1_id})")
                    print(f"[WARNING] This means:")
                    print(f"[WARNING]   1. Songs were created on Suno.com successfully")
                    print(f"[WARNING]   2. Database save may have failed OR")
                    print(f"[WARNING]   3. pg1_id was not returned in the response")
                    print(f"[WARNING]   4. Review process will use fallback method")
                else:
                    print(f"[SUCCESS] pg1_ids successfully obtained: {pg1_ids if 'pg1_ids' in locals() else pg1_id}")
                    print(f"[SUCCESS] Both songs saved to database for AI review")

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
                print(f"Error clicking Create button: {e}")
                raise Exception("Could not click Create button")

    except Exception as e:
        print(f"An error occurred in generate_song: {e}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": f"Song generation failed: {str(e)}",
            "song_id": None,
            "lyrics": None,
            "style": strStyle,
            "title": strTitle
        }

# Import the download module
import sys
import os as os_module
sys.path.insert(0, os_module.path.abspath(os_module.path.join(os_module.path.dirname(__file__), '..', '..')))
from utils.download_song_v2 import download_song_v2

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
