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
from playwright.async_api import expect
from configs.browser_config import config

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
    """Handles song generation requests by coordinating with Suno API.

    This function serves as the primary handler for song generation requests.
    It validates input parameters and delegates the song creation process to
    the generate_song function.

    Args:
        strBookName (str): Name of the Bible book (e.g., "Genesis", "Exodus")
        intBookChapter (int): Chapter number within the specified book
        strVerseRange (str): Verse range to include in the song (e.g., "1-5")
        strStyle (str): Musical style/genre for the song (e.g., "Pop", "Rock")
        strTitle (str): Title for the generated song

    Returns:
        Dict[str, Any]: Dictionary containing:
            - 'success': Boolean indicating operation success
            - 'song_id': ID of the generated song (if successful)
            - 'lyrics': Lyrics used for song generation
            - 'style': Musical style applied
            - 'title': Song title
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
    """Generates a song using Suno's API by automating browser interactions.

    This function orchestrates the entire song generation process:
    1. Retrieves song structure from the database
    2. Converts the structure to lyrics
    3. Automates the Suno website to create the song
    4. Saves generation results to the database

    Args:
        strBookName (str): Name of the Bible book
        intBookChapter (int): Chapter number within the book
        strVerseRange (str): Verse range to include in the song
        strStyle (str): Musical style/genre for the song
        strTitle (str): Title for the generated song

    Returns:
        Union[Dict[str, Any], bool]: On success, returns dictionary with:
            - 'success': True
            - 'song_id': Generated song ID
            - 'lyrics': Lyrics used
            - 'style': Applied musical style
            - 'title': Song title
        On failure, returns False
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


async def review_song_with_ai(
    audio_file_path: str, song_structure: Dict[str, Any]
) -> Dict[str, Any]:
    """Reviews a generated song using Google AI Studio for quality assurance.

    This function performs a two-step review process:
    1. Asks AI to transcribe and evaluate the audio for common issues
    2. Compares transcribed lyrics with original structure for accuracy

    Args:
        audio_file_path (str): Path to the generated audio file
        song_structure (Dict[str, Any]): Original song structure with lyrics

    Returns:
        Dict[str, Any]: Review results containing:
            - 'success': Boolean indicating review process success
            - 'error': Error message if review failed
            - 'first_response': AI's initial transcription and evaluation
            - 'second_response': AI's comparison with original lyrics
            - 'verdict': Final quality verdict ('re-roll' or 'continue')
            - 'audio_file': Path to reviewed audio file
    """
    try:
        # Validate audio file exists
        if not os.path.exists(audio_file_path):
            return {
                "success": False,
                "error": f"Audio file not found at path: {audio_file_path}",
                "verdict": "error",
            }

        async with AsyncCamoufox(
            headless=False,
            persistent_context=True,
            user_data_dir="backend/camoufox_session_data",
            os=("windows"),
            config=config,
            humanize=True,
            main_world_eval=True,
            geoip=True,
            i_know_what_im_doing=True,
        ) as browser:
            page = await browser.new_page(locale="en-US")

            # Navigate to AI Studio
            await page.goto(
                "https://aistudio.google.com/prompts/new_chat",
                wait_until="domcontentloaded",
                timeout=30000,
            )

            await page.wait_for_timeout(2000)
            await page.wait_for_load_state("load")

            # Login process
            email_input = page.locator('input[type="email"]')
            await email_input.wait_for(state="visible", timeout=10000)
            await email_input.fill("pbNJ1sznC2Gr@gmail.com")
            await page.keyboard.press("Enter")

            password_input = page.locator('input[name="Passwd"]')
            await password_input.wait_for(state="visible", timeout=10000)
            await password_input.fill("&!8G26tlbsgO")
            await page.keyboard.press("Enter")

            await page.wait_for_url(
                "https://aistudio.google.com/prompts/new_chat", timeout=20000
            )
            await page.mouse.click(10, 10)

            # Wait for prompt textarea
            prompt_textarea_selector = 'textarea[aria-label="Type something or tab to choose an example prompt"]'
            await page.locator(prompt_textarea_selector).wait_for(
                state="visible", timeout=30000
            )

            # Upload audio file
            add_button = page.locator(
                'button[aria-label="Insert assets such as images, videos, files, or audio"]'
            )
            await add_button.wait_for(state="visible", timeout=10000)
            await add_button.click()
            await page.wait_for_timeout(1000)

            try:
                file_input_locator = page.locator('input[type="file"]')
                await file_input_locator.wait_for(state="attached", timeout=5000)
                await file_input_locator.set_input_files(audio_file_path)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to upload audio file: {str(e)}",
                    "verdict": "error",
                }

            # Handle acknowledge button if present
            try:
                acknowledge_bttn = page.locator('span:has-text("Acknowledge")')
                await acknowledge_bttn.wait_for(state="visible", timeout=2000)
                if await acknowledge_bttn.is_visible():
                    await acknowledge_bttn.click()
            except Exception:
                pass  # Acknowledge button may not appear

            # First prompt - transcription and initial review
            prompt_textarea = page.locator(prompt_textarea_selector)
            await prompt_textarea.wait_for(state="visible", timeout=5000)

            first_prompt = """This is a song generated by AI and we need to check it's quality. The AI has a tendency of making a few common mistakes. Please write out the lyrics that you hear and note what is spoken and what is rapped, and what is sung. If the song is unclear or sounds messy and unmusical, the song needs to be deleted and remade. If it is more than 30% spoken it needs to be deleted and remade. If it cuts off abruptly and doesnt resolve naturally, it needs to be deleted and remade, and if the song feels like it ends, but then it picks back up again, it needs to be deleted and remade. Please write out the lyrics as requested and let me know if any red flags require the song to be deleted and remade. Don't attempt to recognize the lyrics source and infer what they should be, just write what you hear without inference or adjustment. If a word doesn't make sense, just spell it out phonetically. Add final verdict by ending with 'Final Verdict: [re-roll] or [continue]'."""

            await prompt_textarea.fill(first_prompt)

            # Focus textarea and run first prompt
            box = await prompt_textarea.bounding_box()
            if box:
                x = box["x"] + box["width"] / 2
                y = box["y"] + box["height"] / 2
                await page.mouse.click(x, y)

            run_bttn = page.locator('button[aria-label="Run"]')
            await expect(run_bttn).to_be_enabled(timeout=20000)

            # Handle overlay if present
            overlay_selector = "div.cdk-overlay-backdrop.cdk-overlay-transparent-backdrop.cdk-overlay-backdrop-showing"
            overlay = page.locator(overlay_selector)
            try:
                await overlay.wait_for(state="hidden", timeout=10000)
            except Exception:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(500)

            await run_bttn.click(timeout=15000)
            await page.wait_for_timeout(60000)

            # Get first AI response
            ai_response = page.locator("ms-text-chunk.ng-star-inserted").last
            await ai_response.wait_for(state="visible", timeout=30000)
            first_response = await ai_response.inner_text()

            # Second prompt - compare with intended lyrics
            try:
                prompt_textarea = page.locator(
                    'textarea[aria-label="Start typing a prompt"]'
                )
                await prompt_textarea.wait_for(state="visible", timeout=20000)

                # Format song structure for comparison
                formatted_lyrics = _format_song_structure_for_prompt(song_structure)

                second_prompt = f"""You are our primary proofreader, and we need to confirm the AI has not made any mistakes with our lyrics while singing. Below, I will give you the intended lyrics for the song, please compare them to the lyrics you transcribed above for inaccuracies.

Converted song structure verses: {song_structure}

{formatted_lyrics}

We are looking for things that don't match which indicates the song must be deleted and remade. Our goal is to go verse by verse and stay perfectly in order without skipping or adjusting or repeating. If the song has adlibs near the start, this is acceptable. If the song repeats a single sentence or a few words directly after that sentence or phrase has been said, this is an acceptable creative decision. If the song fully completes the lyrics, any repetition that comes after is acceptable as long as the lyrics were completely sung through at least once fully in order. Since some words may not have been recognized by you, if you notice that a word is spelled differently, but with similar phonetics, assume that the word is correct and you just misheard before. Please tell me if the song needs to be deleted and remade, or if it is safe to keep.

Add final verdict by ending with 'Final Verdict: [re-roll] or [continue]'."""

                await prompt_textarea.fill(second_prompt)

                run_bttn = page.locator('button[aria-label="Run"]')
                await expect(run_bttn).to_be_enabled(timeout=20000)

                # Handle overlay again
                try:
                    await overlay.wait_for(state="hidden", timeout=10000)
                except Exception:
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(500)

                await run_bttn.click(timeout=15000)
                await page.wait_for_timeout(60000)

                # Get second AI response
                ai_response = page.locator("ms-text-chunk.ng-star-inserted").last
                await ai_response.wait_for(state="visible", timeout=30000)
                second_response = await ai_response.inner_text()

                # Determine final verdict
                verdict = "continue"
                if "[re-roll]" in second_response.lower():
                    verdict = "re-roll"
                elif "[continue]" in second_response.lower():
                    verdict = "continue"

                return {
                    "success": True,
                    "first_response": first_response,
                    "second_response": second_response,
                    "verdict": verdict,
                    "audio_file": audio_file_path,
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Second prompt failed: {str(e)}",
                    "first_response": first_response,
                    "verdict": "error",
                }

    except Exception as e:
        return {
            "success": False,
            "error": f"Review process failed: {str(e)}",
            "verdict": "error",
        }


def _format_song_structure_for_prompt(song_structure: Dict[str, Any]) -> str:
    """Formats song structure into a readable string for AI prompts.

    Converts the structured song data into a plain text format suitable
    for use in AI review prompts by organizing lyrics by section.

    Args:
        song_structure (Dict[str, Any]): Song structure containing:
            - Section names as keys
            - Dictionaries of verse numbers and lyrics as values

    Returns:
        str: Formatted lyrics string with section headers and verses
    """
    formatted_lines = []

    for section_name, verses in song_structure.items():
        formatted_lines.append(f"[{section_name}]:")

        if isinstance(verses, dict):
            for verse_num, lyrics in verses.items():
                formatted_lines.append(lyrics.strip())
        elif isinstance(verses, str):
            formatted_lines.append(verses.strip())

        formatted_lines.append("")  # Add blank line between sections

    return "\n".join(formatted_lines)


async def download_song_handler(
    strTitle: str, intIndex: int, download_path: str
) -> Dict[str, Any]:
    """Downloads a song from Suno by automating browser interactions.

    This function provides an improved song download experience with enhanced
    error handling, robust element finding, and configurable download paths.
    It navigates to the user's Suno songs page, finds the target song by title
    and index, and downloads it as MP3.

    Args:
        strTitle (str): Title of the song to download (must match exactly)
        intIndex (int): Index of the song to download. Positive values (1-based from start)
                        are internally converted to negative indices for consistent processing.
                        Negative values (-1 = last, -2 = second to last) are used directly.
        download_path (str, optional): Directory to save the downloaded file.
                                     Defaults to "backend/downloaded_songs"

    Returns:
        Dict[str, Any]: Download result containing:
            - 'success': Boolean indicating download success
            - 'file_path': Path to downloaded file (if successful)
            - 'error': Error message (if failed)
            - 'song_title': Title of the song
            - 'song_index': Index used for download

    Examples:
        >>> result = await download_song_handler("Amazing Grace", 1)
        >>> if result['success']:
        ...     print(f"Downloaded to: {result['file_path']}")

        >>> result = await download_song_handler("Psalm 23", -1, "custom/path")
        >>> if not result['success']:
        ...     print(f"Download failed: {result['error']}")
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
            humanize=True,
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
                    raise Exception(f"Timed out waiting for song list to become visible: {e}")

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

                # Right-click to open context menu
                print(f"Right-clicking on song at index {intIndex}...")
                await target_song.click(button="right", timeout=20000)
                print("Right-click completed successfully")

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

                await download_trigger.hover(timeout=5000)
                print("Hovered over download trigger")
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
                        await mp3_option.click(timeout=15000)
                        print("Clicked MP3 Audio option")

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
                                    await anyway_btn.click(timeout=8000)
                                    print("Clicked 'Download Anyway' button")
                                    break
                                except Exception:
                                    continue
                        except Exception:
                            print(
                                "No 'Download Anyway' button needed - proceeding with direct download"
                            )

                    download = await download_info.value

                    if download:
                        # Generate sanitized filename
                        sanitized_title = re.sub(r'[<>:"/\\|?*]', "-", strTitle)
                        filename = (
                            f"{sanitized_title.replace(' ', '_')}_index_{intIndex}.mp3"
                        )
                        final_file_path = os.path.join(download_path, filename)

                        # Save the download
                        await download.save_as(final_file_path)
                        download_successful = True
                        print(f"Download completed successfully: {final_file_path}")
                        raise Exception("Download object was None")

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
