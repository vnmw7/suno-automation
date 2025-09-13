"""AI Review Utilities Module

This module provides functions for reviewing generated songs using Google AI Studio.
It handles audio file upload, transcription, and quality assessment.
"""

from datetime import datetime
import os
import json
import traceback
import logging
import shutil
import asyncio
from typing import Dict, Any, Optional
import aiohttp
from services.supabase_service import SupabaseService
from middleware.gemini import model_pro, model_flash, api_key
try:
    from config.ai_review_config import (
        USE_FLASH_MODEL, DELAY_BETWEEN_API_CALLS, 
        PROCESS_SEQUENTIALLY
    )
except ImportError:
    # Fallback if config file doesn't exist
    USE_FLASH_MODEL = False
    DELAY_BETWEEN_API_CALLS = 30
    PROCESS_SEQUENTIALLY = True

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create logs directory if it doesn't exist
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.log")

# Create file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


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
            init_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={api_key}"
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
    previous_messages: Optional[list] = None,
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
        previous_messages (list, optional): Conversation history in Google AI format

    Returns:
        Optional[str]: AI-generated text response on success, None on failure

    Raises:
        None: Errors are caught and logged internally
    """
    try:
        # Build contents array
        contents = []

        # Add previous messages if provided
        if previous_messages:
            contents.extend(previous_messages)

        # Build current message parts
        parts = []

        # Add file if provided
        if file_uri and mime_type:
            parts.append(
                {"file_data": {"mime_type": mime_type, "file_uri": file_uri}}
            )

        # Add text prompt
        parts.append({"text": prompt})

        # Add current message
        contents.append({"role": "user", "parts": parts})

        # Prepare request data
        generation_config = {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
        }

        # Add rate limiting based on configuration
        print(f"\n🕒 [API-CALL] Preparing to call Gemini API...")
        print(f"🕒 [API-CALL] Model: {'Gemini Flash' if USE_FLASH_MODEL else 'Gemini Pro'}")
        print(f"🕒 [API-CALL] Rate limit delay: {DELAY_BETWEEN_API_CALLS}s")
        print(f"🕒 [API-CALL] Has file attachment: {'Yes' if file_uri else 'No'}")
        print(f"🕒 [API-CALL] Has conversation history: {'Yes' if previous_messages else 'No'}")
        
        await asyncio.sleep(DELAY_BETWEEN_API_CALLS)
        
        # Select model based on configuration
        model = model_flash if USE_FLASH_MODEL else model_pro
        
        print(f"🚀 [API-CALL] Sending request to Gemini API...")
        start_time = datetime.now()
        
        response = await model.generate_content_async(
            contents, generation_config=generation_config
        )
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ [API-CALL] Response received in {elapsed_time:.2f} seconds")
        print(f"📝 [API-CALL] Response text length: {len(response.text) if response.text else 0} characters")

        return response.text

    except Exception as e:
        print(f"\n❌ [API-CALL-ERROR] Failed to call Gemini API!")
        print(f"❌ [API-CALL-ERROR] Error: {str(e)}")
        
        # Provide specific guidance for common errors
        if '429' in str(e) or 'quota' in str(e).lower():
            print(f"🚫 [API-CALL-ERROR] RATE LIMIT EXCEEDED")
            print(f"🚫 [API-CALL-ERROR] Wait time before retry: Check error message above")
        elif '401' in str(e) or 'unauthorized' in str(e).lower():
            print(f"🔐 [API-CALL-ERROR] AUTHENTICATION ERROR")
            print(f"🔐 [API-CALL-ERROR] Check your GEMINI_API_KEY in .env file")
        elif '400' in str(e) or 'invalid' in str(e).lower():
            print(f"⚠️ [API-CALL-ERROR] INVALID REQUEST")
            print(f"⚠️ [API-CALL-ERROR] Check prompt format or file URI")
            
        return None


async def review_song_with_ai(
    audio_file_path: str, pg1_id: int
) -> Dict[str, Any]:
    """
    Reviews generated song quality using Google AI API in a two-step process.

    Step 1: Audio transcription and initial quality assessment
    Step 2: Comparison between transcribed lyrics and original structure

    Args:
        audio_file_path (str): Absolute path to generated audio file (MP3/WAV)
        pg1_id (int): Database ID of tblprogress

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
        logger.info(f"Starting review for pg1_id: {pg1_id}")
        logger.info(f"Audio file path: {audio_file_path}")
        
        if not os.path.exists(audio_file_path):
            error_msg = f"Audio file not found at path: {audio_file_path}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "verdict": "error",
            }

        # Fetch song data using SupabaseService
        service = SupabaseService()
        try:
            logger.debug(f"Fetching song data for ID: {pg1_id}")
            song_data = service.get_song_with_lyrics(pg1_id)
            if not song_data or not song_data.get('lyrics'):
                error_msg = f"No lyrics data found for pg1_id: {pg1_id}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "verdict": "error",
                }
            
            # Extract original song structure from song_structure_tbl
            original_song_structure = song_data['song_structure']
            if not original_song_structure or not original_song_structure.get('song_structure'):
                return {
                    "success": False,
                    "error": f"No song_structure found for pg1_id: {pg1_id}",
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
                    "error": f"No pg1_lyrics found for pg1_id: {pg1_id}",
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
        
        except Exception as e:
            logger.error(f"Error during song data retrieval: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": f"Error during song data retrieval: {str(e)}",
                "verdict": "error",
            }
        # Note: We don't close the service here anymore - it will be closed later

        print(f"\n📤 [AI-UPLOAD] Uploading audio file to Google AI...")
        print(f"📤 [AI-UPLOAD] File: {os.path.basename(audio_file_path)}")
        print(f"📤 [AI-UPLOAD] Size: {os.path.getsize(audio_file_path):,} bytes")
        
        logger.info(f"Uploading audio file to Google AI: {audio_file_path}")
        file_metadata = await upload_file_to_google_ai(audio_file_path, api_key)
        
        if not file_metadata:
            error_msg = "Failed to upload audio file to Google AI"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "verdict": "error",
            }
        
        file_uri = file_metadata.get("uri")
        mime_type = file_metadata.get("mimeType", "audio/mpeg")
        
        print(f"✅ [AI-UPLOAD] Upload successful!")
        print(f"📤 [AI-UPLOAD] File URI: {file_uri[:50]}..." if file_uri else "[AI-UPLOAD] No URI received")
        print(f"📤 [AI-UPLOAD] MIME type: {mime_type}")
        
        # TODO: Consider security implications of logging partial URIs
        # TODO: Change to debug level or remove entirely in production
        logger.debug(f"File uploaded successfully. URI: {file_uri[:30]}...")  # Truncate for security
        
        # First prompt - transcription and initial review
        first_prompt = """This is a song generated by AI and we need to check it's quality. The AI has a tendency of making a few common mistakes. Please write out the lyrics that you hear and note what is spoken and what is rapped, and what is sung. If the song is unclear or sounds messy and unmusical, the song needs to be deleted and remade. If it is more than 30% spoken it needs to be deleted and remade. If it cuts off abruptly and doesnt resolve naturally, it needs to be deleted and remade, and if the song feels like it ends, but then it picks back up again, it needs to be deleted and remade. Please write out the lyrics as requested and let me know if any red flags require the song to be deleted and remade. Don't attempt to recognize the lyrics source and infer what they should be, just write what you hear without inference or adjustment. If a word doesn't make sense, just spell it out phonetically. Add final verdict by ending with 'Final Verdict: [re-roll] or [continue]'."""
        
        print(f"\n🤖 [AI-PROMPT-1] Sending first prompt for transcription and review...")
        print(f"🤖 [AI-PROMPT-1] Prompt length: {len(first_prompt)} characters")
        print(f"🤖 [AI-PROMPT-1] Timestamp: {datetime.now().strftime('%H:%M:%S')}")
        
        logger.info("Sending first prompt for transcription and review")
        first_response = await send_prompt_to_google_ai(
            prompt=first_prompt,
            file_uri=file_uri,
            mime_type=mime_type,
        )
        
        if not first_response:
            error_msg = "Failed to get first AI response"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "verdict": "error",
            }
        
        print(f"✅ [AI-RESPONSE-1] First response received!")
        print(f"📝 [AI-RESPONSE-1] Response length: {len(first_response) if first_response else 0} characters")
        print(f"\n📝 [AI-RESPONSE-1] Transcription and Quality Check:")
        print(f"{'-'*60}")
        print(first_response[:1000] + '...' if first_response and len(first_response) > 1000 else first_response or 'No response')
        print(f"{'-'*60}\n")
        
        # Extract verdict from first response
        first_verdict = 'unknown'
        if first_response:
            if '[re-roll]' in first_response.lower():
                first_verdict = 're-roll'
            elif '[continue]' in first_response.lower():
                first_verdict = 'continue'
        print(f"🎯 [AI-VERDICT-1] Initial verdict from transcription: {first_verdict}")
        
        logger.info("First AI response received successfully")
        logger.debug(f"First AI response content:\n{first_response}")
        
        # Add delay to avoid rate limiting based on configuration
        print(f"\n⏳ [RATE-LIMIT] Waiting {DELAY_BETWEEN_API_CALLS} seconds before second API call...")
        logger.info(f"Waiting {DELAY_BETWEEN_API_CALLS} seconds before second API call to avoid rate limits...")
        await asyncio.sleep(DELAY_BETWEEN_API_CALLS)
        
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
        
        print(f"\n🤖 [AI-PROMPT-2] Sending second prompt for lyrics comparison...")
        print(f"🤖 [AI-PROMPT-2] Prompt length: {len(second_prompt)} characters")
        print(f"🤖 [AI-PROMPT-2] Including conversation history: Yes")
        print(f"🤖 [AI-PROMPT-2] Timestamp: {datetime.now().strftime('%H:%M:%S')}")
        
        logger.info("Sending second prompt for lyrics comparison")
        second_response = await send_prompt_to_google_ai(
            prompt=second_prompt,
            previous_messages=conversation_history
        )
        
        if not second_response:
            error_msg = "Failed to get second AI response"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "first_response": first_response,
                "verdict": "error",
            }
        
        print(f"✅ [AI-RESPONSE-2] Second response received!")
        print(f"📝 [AI-RESPONSE-2] Response length: {len(second_response) if second_response else 0} characters")
        print(f"\n📝 [AI-RESPONSE-2] Lyrics Comparison Result:")
        print(f"{'-'*60}")
        print(second_response[:1000] + '...' if second_response and len(second_response) > 1000 else second_response or 'No response')
        print(f"{'-'*60}\n")
        
        logger.info("Second AI response received successfully")
        logger.debug(f"Second AI response content:\n{second_response}")
        
        # Determine final verdict
        verdict = "continue"
        if second_response and "[re-roll]" in second_response.lower():
            verdict = "re-roll"
            print(f"⚠️ [AI-VERDICT-FINAL] 🔄 RE-ROLL required for pg1_id: {pg1_id}")
            print(f"⚠️ [AI-VERDICT-FINAL] Reason: AI detected issues with lyrics or quality")
            logger.warning(f"Verdict: RE-ROLL required for ID: {pg1_id}")
        elif second_response and "[continue]" in second_response.lower():
            verdict = "continue"
            print(f"✅ [AI-VERDICT-FINAL] ✓ CONTINUE approved for pg1_id: {pg1_id}")
            print(f"✅ [AI-VERDICT-FINAL] Song passed quality checks")
            logger.info(f"Verdict: CONTINUE approved for ID: {pg1_id}")
        else:
            print(f"⚠️ [AI-VERDICT-FINAL] No clear verdict tag found, defaulting to CONTINUE")
            logger.warning("Verdict tag not found in response, defaulting to CONTINUE")
        
        # Handle file operations based on verdict
        deletion_message = None
        move_message = None
        new_audio_path = audio_file_path
        
        if verdict == "re-roll":
            # Delete the database entry for this song
            deletion_db_success = service.delete_song(pg1_id)
            if deletion_db_success:
                logger.info(f"Deleted database entry for pg1_id: {pg1_id}")
            else:
                logger.error(f"Failed to delete database entry for pg1_id: {pg1_id}")
                # TODO: Consider whether to abort process if DB deletion fails
                # TODO: Add retry logic for transient errors
            
            # Also delete the audio file
            try:
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
                    deletion_message = f"Deleted file: {audio_file_path}"
                    logger.info(deletion_message)
                    new_audio_path = None
                else:
                    deletion_message = f"File not found: {audio_file_path}"
                    logger.warning(deletion_message)
            except Exception as e:
                deletion_message = f"Deletion failed: {str(e)}"
                logger.error(deletion_message)
                # TODO: Add metrics to track deletion failure rates
                
        elif verdict == "continue":
            try:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                target_dir = os.path.join(base_dir, "songs", "final_review")
                os.makedirs(target_dir, exist_ok=True)
                
                if os.path.exists(audio_file_path):
                    filename = os.path.basename(audio_file_path)
                    new_path = os.path.join(target_dir, filename)
                    shutil.move(audio_file_path, new_path)
                    move_message = f"Moved file to: {new_path}"
                    logger.info(move_message)
                    new_audio_path = new_path
                else:
                    move_message = f"File not found: {audio_file_path}"
                    logger.warning(move_message)
            except Exception as e:
                move_message = f"Move failed: {str(e)}"
                logger.error(move_message)

        # Close the service connection now that we're done with database operations
        service.close_connection()

        print(f"\n🎯 [REVIEW-COMPLETE] Final review summary:")
        print(f"  • pg1_id: {pg1_id}")
        print(f"  • File: {os.path.basename(audio_file_path)}")
        print(f"  • Verdict: {verdict.upper()}")
        print(f"  • File action: {deletion_message or move_message or 'No action taken'}")
        print(f"{'-'*60}\n")
        
        logger.info(f"Review completed for ID: {pg1_id}")
        return {
            "success": True,
            "first_response": first_response,
            "second_response": second_response,
            "verdict": verdict,
            "audio_file": new_audio_path,
            "deletion_message": deletion_message,
            "move_message": move_message
        }

    except Exception as e:
        error_msg = f"Review process failed: {str(e)}"
        print(f"\n❌ [AI-REVIEW-ERROR] Critical failure in review process!")
        print(f"❌ [AI-REVIEW-ERROR] Error type: {type(e).__name__}")
        print(f"❌ [AI-REVIEW-ERROR] Error message: {str(e)}")
        print(f"❌ [AI-REVIEW-ERROR] pg1_id: {pg1_id}")
        print(f"❌ [AI-REVIEW-ERROR] Audio file: {audio_file_path}")
        
        # Check if it's a rate limit error
        if '429' in str(e) or 'quota' in str(e).lower():
            print(f"\n🚫 [RATE-LIMIT-ERROR] API RATE LIMIT EXCEEDED!")
            print(f"🚫 [RATE-LIMIT-ERROR] You've hit the Gemini API quota limits")
            print(f"🚫 [RATE-LIMIT-ERROR] Free tier: 2 requests per minute for Gemini Pro")
            print(f"🚫 [RATE-LIMIT-ERROR] Consider:")
            print(f"    1. Waiting before retrying")
            print(f"    2. Switching to Gemini Flash model (15 RPM)")
            print(f"    3. Upgrading to paid tier")
        
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": error_msg,
            "verdict": "error",
        }
