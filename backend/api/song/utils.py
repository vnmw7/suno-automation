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

# Import supabase
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "lib"))
supabase_utils_path = os.path.join(lib_path, "supabase.py")

spec = importlib.util.spec_from_file_location("supabase_utils", supabase_utils_path)
supabase_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supabase_utils)

supabase = supabase_utils.supabase

# Google AI API configuration
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
if not GOOGLE_AI_API_KEY:
    raise ValueError("GOOGLE_AI_API_KEY environment variable is required")

GOOGLE_AI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


async def upload_file_to_google_ai(file_path: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Uploads a file to Google AI Files API using resumable upload protocol.

    This function handles the entire upload process including:
    1. Initializing the resumable upload session
    2. Uploading the file content
    3. Finalizing the upload

    Args:
        file_path (str): Absolute path to the file to upload
        api_key (str): Google AI API key for authentication

    Returns:
        Optional[Dict[str, Any]]: Dictionary containing file metadata (name, uri, mimeType)
        on success, None on failure

    Raises:
        None: Errors are caught and logged internally
    """
    try:
        # Get file info
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        # Determine MIME type
        mime_type = "audio/mpeg" if file_path.endswith(".mp3") else "audio/wav"
        
        async with aiohttp.ClientSession() as session:
            # Step 1: Initialize resumable upload
            init_url = f"{GOOGLE_AI_API_BASE}/files?key={api_key}"
            init_headers = {
                "X-Goog-Upload-Protocol": "resumable",
                "X-Goog-Upload-Command": "start",
                "X-Goog-Upload-Header-Content-Length": str(file_size),
                "X-Goog-Upload-Header-Content-Type": mime_type,
                "Content-Type": "application/json"
            }
            init_data = {
                "file": {
                    "display_name": file_name
                }
            }
            
            async with session.post(init_url, headers=init_headers, json=init_data) as resp:
                if resp.status != 200:
                    print(f"Failed to initialize upload: {resp.status}")
                    return None
                    
                upload_url = resp.headers.get("X-Goog-Upload-URL")
                if not upload_url:
                    print("No upload URL received")
                    return None
            
            # Step 2: Upload the file
            upload_headers = {
                "Content-Length": str(file_size),
                "X-Goog-Upload-Offset": "0",
                "X-Goog-Upload-Command": "upload, finalize"
            }
            
            with open(file_path, "rb") as f:
                file_data = f.read()
                
            async with session.put(upload_url, headers=upload_headers, data=file_data) as resp:
                if resp.status != 200:
                    print(f"Failed to upload file: {resp.status}")
                    return None
                    
                result = await resp.json()
                return result.get("file")
                
    except Exception as e:
        print(f"Error uploading file to Google AI: {e}")
        return None


async def send_prompt_to_google_ai(
    prompt: str, 
    file_uri: Optional[str] = None,
    mime_type: Optional[str] = None,
    api_key: str = None,
    previous_messages: Optional[list] = None
) -> Optional[str]:
    """
    Sends a prompt to Google AI API with optional file attachment and conversation history.

    This function constructs a request to Google's Gemini model that may include:
    - Text prompts
    - Attached files (audio/images)
    - Conversation history for contextual interactions

    Args:
        prompt (str): Text prompt to send to the AI model
        file_uri (str, optional): URI of previously uploaded file for multimodal input
        mime_type (str, optional): MIME type of attached file (required if file_uri provided)
        api_key (str): Google AI API key for authentication
        previous_messages (list, optional): Conversation history in Google AI format

    Returns:
        Optional[str]: AI-generated text response on success, None on failure

    Raises:
        None: Errors are caught and logged internally
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{GOOGLE_AI_API_BASE}/models/gemini-1.5-flash:generateContent?key={api_key}"
            
            # Build contents array
            contents = []
            
            # Add previous messages if provided
            if previous_messages:
                contents.extend(previous_messages)
            
            # Build current message parts
            parts = []
            
            # Add file if provided
            if file_uri and mime_type:
                parts.append({
                    "file_data": {
                        "mime_type": mime_type,
                        "file_uri": file_uri
                    }
                })
            
            # Add text prompt
            parts.append({"text": prompt})
            
            # Add current message
            contents.append({
                "role": "user",
                "parts": parts
            })
            
            # Prepare request data
            data = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 8192,
                }
            }
            
            async with session.post(url, json=data) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"Failed to get AI response: {resp.status} - {error_text}")
                    return None
                    
                result = await resp.json()
                
                # Extract text from response
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if len(parts) > 0 and "text" in parts[0]:
                            return parts[0]["text"]
                
                return None
                
    except Exception as e:
        print(f"Error sending prompt to Google AI: {e}")
        return None


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


async def review_song_with_ai(
    audio_file_path: str, song_structure_id: int
) -> Dict[str, Any]:
    """
    Reviews generated song quality using Google AI API in a two-step process.

    Step 1: Audio transcription and initial quality assessment
    Step 2: Comparison between transcribed lyrics and original structure

    Args:
        audio_file_path (str): Absolute path to generated audio file (MP3/WAV)
        song_structure_id (int): Database ID of song structure

    Returns:
        Dict[str, Any]: Dictionary containing:
            - success (bool): Review process completion status
            - error (str): Error message if any step fails
            - first_response (str): AI's initial transcription and evaluation
            - second_response (str): Lyrics comparison results
            - verdict (str): Final quality decision ('re-roll' or 'continue')
            - audio_file (str): Path to reviewed audio file

    Raises:
        None: All exceptions are caught and returned in result dictionary
    """
    try:
        # Validate audio file exists
        if not os.path.exists(audio_file_path):
            return {
                "success": False,
                "error": f"Audio file not found at path: {audio_file_path}",
                "verdict": "error",
            }

        # Fetch song data using SupabaseService
        service = SupabaseService()
        try:
            song_data = service.get_song_with_lyrics(song_structure_id)
            if not song_data or not song_data.get('lyrics'):
                return {
                    "success": False,
                    "error": f"No lyrics data found for song_structure_id: {song_structure_id}",
                    "verdict": "error",
                }
            
            # Extract original song structure from song_structure_tbl
            original_song_structure = song_data['song_structure']
            if not original_song_structure or not original_song_structure.get('song_structure'):
                return {
                    "success": False,
                    "error": f"No song_structure found for song_structure_id: {song_structure_id}",
                    "verdict": "error",
                }
            
            # Parse the original song_structure JSON if it's a string
            song_structure = original_song_structure['song_structure']
            if isinstance(song_structure, str):
                try:
                    # Handle potential escape sequence issues in JSON
                    cleaned_json = song_structure.replace('\\', '\\\\')
                    song_structure = json.loads(cleaned_json)
                except json.JSONDecodeError as e:
                    # Try alternative parsing methods
                    try:
                        # Try raw string parsing
                        song_structure = json.loads(song_structure.encode().decode('unicode_escape'))
                    except (json.JSONDecodeError, UnicodeDecodeError) as e2:
                        return {
                            "success": False,
                            "error": f"Failed to parse song_structure JSON: {e}. Alternative method also failed: {e2}",
                            "verdict": "error",
                        }
            
            # Get the most recent lyrics entry (first in the list since ordered by created_at DESC)
            latest_lyrics = song_data['lyrics'][0]
            pg1_lyrics = latest_lyrics.get('pg1_lyrics')
            
            if not pg1_lyrics:
                return {
                    "success": False,
                    "error": f"No pg1_lyrics found for song_structure_id: {song_structure_id}",
                    "verdict": "error",
                }
            
            # If pg1_lyrics is a JSON string, parse it with robust error handling
            if isinstance(pg1_lyrics, str):
                try:
                    # Try to parse as JSON (in case it contains structured data)
                    parsed_lyrics = json.loads(pg1_lyrics)
                    pg1_lyrics = parsed_lyrics
                except json.JSONDecodeError:
                    # If it's not JSON, treat as plain text (which is expected for lyrics)
                    pass
        
        finally:
            service.close_connection()

        # Upload audio file to Google AI
        print(f"Uploading audio file to Google AI: {audio_file_path}")
        file_metadata = await upload_file_to_google_ai(audio_file_path, GOOGLE_AI_API_KEY)
        
        if not file_metadata:
            return {
                "success": False,
                "error": "Failed to upload audio file to Google AI",
                "verdict": "error",
            }
        
        file_uri = file_metadata.get("uri")
        mime_type = file_metadata.get("mimeType", "audio/mpeg")
        print(f"File uploaded successfully. URI: {file_uri}")
        
        # First prompt - transcription and initial review
        first_prompt = """This is a song generated by AI and we need to check it's quality. The AI has a tendency of making a few common mistakes. Please write out the lyrics that you hear and note what is spoken and what is rapped, and what is sung. If the song is unclear or sounds messy and unmusical, the song needs to be deleted and remade. If it is more than 30% spoken it needs to be deleted and remade. If it cuts off abruptly and doesnt resolve naturally, it needs to be deleted and remade, and if the song feels like it ends, but then it picks back up again, it needs to be deleted and remade. Please write out the lyrics as requested and let me know if any red flags require the song to be deleted and remade. Don't attempt to recognize the lyrics source and infer what they should be, just write what you hear without inference or adjustment. If a word doesn't make sense, just spell it out phonetically. Add final verdict by ending with 'Final Verdict: [re-roll] or [continue]'."""
        
        print("Sending first prompt for transcription and initial review...")
        first_response = await send_prompt_to_google_ai(
            prompt=first_prompt,
            file_uri=file_uri,
            mime_type=mime_type,
            api_key=GOOGLE_AI_API_KEY
        )
        
        if not first_response:
            return {
                "success": False,
                "error": "Failed to get first AI response",
                "verdict": "error",
            }
        
        print("First AI response received")
        
        # Prepare conversation history for second prompt
        conversation_history = [
            {
                "role": "user",
                "parts": [
                    {
                        "file_data": {
                            "mime_type": mime_type,
                            "file_uri": file_uri
                        }
                    },
                    {"text": first_prompt}
                ]
            },
            {
                "role": "model",
                "parts": [{"text": first_response}]
            }
        ]
        
        # Second prompt - compare with intended lyrics
        second_prompt = f"""You are our primary proofreader, and we need to confirm the AI has not made any mistakes with our lyrics while singing. Below, I will give you the intended lyrics for the song, please compare them to the lyrics you transcribed above for inaccuracies.

Original song structure: {song_structure}

Actual lyrics used in generation:
{pg1_lyrics}

We are looking for things that don't match which indicates the song must be deleted and remade. Our goal is to go verse by verse and stay perfectly in order without skipping or adjusting or repeating. If the song has adlibs near the start, this is acceptable. If the song repeats a single sentence or a few words directly after that sentence or phrase has been said, this is an acceptable creative decision. If the song fully completes the lyrics, any repetition that comes after is acceptable as long as the lyrics were completely sung through at least once fully in order. Since some words may not have been recognized by you, if you notice that a word is spelled differently, but with similar phonetics, assume that the word is correct and you just misheard before. Please tell me if the song needs to be deleted and remade, or if it is safe to keep.

Add final verdict by ending with 'Final Verdict: [re-roll] or [continue]'."""
        
        print("Sending second prompt for comparison with original lyrics...")
        second_response = await send_prompt_to_google_ai(
            prompt=second_prompt,
            api_key=GOOGLE_AI_API_KEY,
            previous_messages=conversation_history
        )
        
        if not second_response:
            return {
                "success": False,
                "error": "Failed to get second AI response",
                "first_response": first_response,
                "verdict": "error",
            }
        
        print("Second AI response received")
        
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
        print(f"Review process failed: {str(e)}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": f"Review process failed: {str(e)}",
            "verdict": "error",
        }

async def teleport_click(page: Page, locator: Locator, button: str = "left", delay: int = 30):
    """
    Performs instantaneous 'teleport' click without visible mouse movement.

    This technique is useful for bypassing bot detection that monitors mouse movements.
    It combines:
    1. Instant mouse positioning
    2. Programmatic click events

    Args:
        page (Page): Playwright Page instance
        locator (Locator): Playwright Locator for target element
        button (str): Mouse button ('left'/'right'/'middle') - defaults to 'left'
        delay (int): Milliseconds between mouse down/up events (default: 30ms)

    Raises:
        Exception: If bounding box can't be determined for element
    """
    print("Performing teleport click on element.")
    await locator.scroll_into_view_if_needed(timeout=10000)
    box = await locator.bounding_box()
    if not box:
        raise Exception("Could not get bounding box for locator to perform teleport click.")

    dest_x = box['x'] + box['width'] / 2
    dest_y = box['y'] + box['height'] / 2

    # 1. Move the mouse instantly to the target coordinates.
    await page.mouse.move(dest_x, dest_y)
    
    # 2. Perform the click using low-level down/up events at the new location.
    await page.mouse.down(button=button)
    await page.wait_for_timeout(delay)  # A small delay makes the click more reliable
    await page.mouse.up(button=button)
    
    print("Teleport click completed.")

async def teleport_hover(page: Page, locator: Locator):
    """
    Performs instantaneous 'teleport' hover without visible mouse movement.

    Args:
        page (Page): Playwright Page instance
        locator (Locator): Playwright Locator for target element

    Raises:
        Exception: If bounding box can't be determined for element
    """
    print("Performing teleport hover on element.")
    await locator.scroll_into_view_if_needed(timeout=10000)
    box = await locator.bounding_box()
    if not box:
        raise Exception("Could not get bounding box for locator to perform teleport hover.")
    
    dest_x = box['x'] + box['width'] / 2
    dest_y = box['y'] + box['height'] / 2

    # Instantly move the mouse to the target coordinates.
    await page.mouse.move(dest_x, dest_y)
    print("Teleport hover completed.")

async def download_song_handler(
    strTitle: str, intIndex: int, download_path: str
) -> Dict[str, Any]:
    """
    Downloads a song from Suno.com using automated browser interactions.

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

                # Right-click to open context menu
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

                await teleport_hover(page, download_trigger)
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
                        print("Starting download with teleport click...")
                        await teleport_click(page, mp3_option)
                        print("Clicked MP3 Audio option with teleport click.")

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
