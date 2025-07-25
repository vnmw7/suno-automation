"""AI Review Utilities Module

This module provides functions for reviewing generated songs using Google AI Studio.
It handles audio file upload, transcription, and quality assessment.
"""

import os
import json
import traceback
from typing import Dict, Any, Optional
import aiohttp
from services.supabase_service import SupabaseService

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
            url = f"{GOOGLE_AI_API_BASE}/models/gemini-2.5-pro:generateContent?key={api_key}"
            
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
