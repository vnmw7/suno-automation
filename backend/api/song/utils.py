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
    strTitle: str
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
    audio_file_path: str,
    song_structure: Dict[str, Any]
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
