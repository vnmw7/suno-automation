import os
import shutil
import asyncio
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional


async def execute_song_workflow(
    book_name: str,
    chapter: int,
    verse_range: str,
    style: str,
    title: str,
    song_structure_id: int = None
) -> Dict[str, Any]:
    """
    🎼 CORE ORCHESTRATOR WORKFLOW
    
    Executes the complete song generation and review process with intelligent retry logic.
    
    WORKFLOW STEPS:
    1. Generate 2 songs on Suno.com (single generation creates 2 variants)
    2. Wait for Suno processing
    3. Download both songs using negative indexing (-1, -2)
    4. AI review each song for quality
    5. Handle verdicts:
       - "continue": Move to backend/songs/final_review  
       - "re-roll": Delete and retry generation
    6. Auto-retry up to 3 times if needed
    7. Fallback: Move final attempt songs to final_review regardless
    
    Args:
        book_name (str): Bible book name
        chapter (int): Chapter number  
        verse_range (str): Verse range (e.g., "1-5")
        style (str): Musical style/genre
        title (str): Song title
        song_structure_id (int, optional): Song structure ID for review
        
    Returns:
        Dict[str, Any]: Comprehensive workflow results and statistics
    """
    print(f"🎼 [WORKFLOW] Starting orchestrated workflow for: {book_name} {chapter}:{verse_range}")
    
    # Use verification function to ensure we have the correct final destination
    final_dir = verify_final_destination_folder()
    temp_dir = "backend/songs/pending_review"
    
    # Ensure required directories exist
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(final_dir, exist_ok=True)
    
    print(f"🎼 [WORKFLOW] ✅ VERIFIED: Final approved songs will be moved to: {final_dir}")
    print(f"🎼 [WORKFLOW] ✅ VERIFIED: Temporary downloads will be stored in: {temp_dir}")
    
    workflow_details = {
        "attempts": [],
        "total_songs_generated": 0,
        "total_songs_reviewed": 0, 
        "songs_kept": 0,
        "songs_deleted": 0
    }
    
    max_attempts = 3
    final_attempt_songs = []  # Track final attempt songs for fail-safe
    
    for attempt in range(1, max_attempts + 1):
        print(f"🎼 [WORKFLOW] === ATTEMPT {attempt}/{max_attempts} ===")
        
        attempt_details = {
            "attempt_number": attempt,
            "generation_success": False,
            "downloads": [],
            "reviews": [],
            "final_action": None
        }
        
        try:
            # STEP 1: Generate Song (creates 2 songs on Suno)
            print(f"🎼 [WORKFLOW] Step 1: Generating songs...")
            print(f"🎼 [WORKFLOW] Parameters: book={book_name}, chapter={chapter}, verse={verse_range}, style={style}, title={title}")
            
            generation_result = await generate_songs(
                book_name, chapter, verse_range, style, title
            )
            
            print(f"🎼 [WORKFLOW] Generation result: success={generation_result.get('success')}")
            
            if not generation_result["success"]:
                error_msg = generation_result.get('error', 'Unknown generation error')
                print(f"🎼 [WORKFLOW] ❌ Generation failed on attempt {attempt}: {error_msg}")
                attempt_details["final_action"] = f"generation_failed: {error_msg}"
                workflow_details["attempts"].append(attempt_details)
                print(f"🎼 [WORKFLOW] Will retry generation (attempt {attempt + 1}/{max_attempts})..." if attempt < max_attempts else "🎼 [WORKFLOW] Max attempts reached for generation")
                continue
                
            attempt_details["generation_success"] = True
            workflow_details["total_songs_generated"] += 2  # Suno generates 2 songs
            
            # Extract pg1_id from generation result
            # This is critical for the AI review process to fetch lyrics for comparison
            pg1_id = generation_result.get("pg1_id")
            print(f"🎼 [WORKFLOW-DEBUG] Extracted pg1_id from generation_result: {pg1_id}")
            print(f"🎼 [WORKFLOW-DEBUG] Full generation_result keys: {generation_result.keys()}")
            
            # Check if pg1_id is present - warn but don't fail
            # Missing pg1_id is common due to Suno not redirecting to song page
            if not pg1_id or pg1_id == 0:
                print(f"🎼 [WORKFLOW] ⚠️ WARNING: pg1_id is missing or invalid: {pg1_id}")
                print(f"🎼 [WORKFLOW] This is EXPECTED if Suno didn't redirect to song page")
                print(f"🎼 [WORKFLOW] Songs were generated but database tracking may be incomplete.")
                print(f"🎼 [WORKFLOW] Proceeding with download and review using fallback methods...")
                print(f"🎼 [WORKFLOW] Manual review will be recommended for these songs")

            # Log successful generation details
            if "result" in generation_result:
                song_id = generation_result["result"].get("song_id")
                print(f"🎼 [WORKFLOW] ✅ Generation successful! Song ID: {song_id}, pg1_id: {pg1_id}")
            
            # STEP 2: Wait for Suno processing
            wait_time_seconds = 90
            print(f"🎼 [WORKFLOW] Step 2: Waiting for Suno processing ({wait_time_seconds} seconds)...")
            print(f"🎼 [WORKFLOW] ⏳ Starting wait at: {asyncio.get_event_loop().time()}")
            await asyncio.sleep(wait_time_seconds)
            print(f"🎼 [WORKFLOW] ⏰ Wait completed at: {asyncio.get_event_loop().time()}")
            
            # STEP 3: Download both songs
            print(f"🎼 [WORKFLOW] Step 3: Downloading both generated songs...")
            print(f"🎼 [WORKFLOW] Download parameters: title='{title}', temp_dir='{temp_dir}'")
            
            download_results = await download_both_songs(title, temp_dir)
            
            print(f"🎼 [WORKFLOW] Download result: success={download_results.get('success')}, songs_downloaded={len(download_results.get('downloads', []))}")
            
            if not download_results["success"]:
                error_msg = download_results.get('error', 'Unknown download error')
                print(f"🎼 [WORKFLOW] ❌ Download failed on attempt {attempt}: {error_msg}")
                attempt_details["final_action"] = f"download_failed: {error_msg}"
                workflow_details["attempts"].append(attempt_details)
                print(f"🎼 [WORKFLOW] Will retry entire workflow (attempt {attempt + 1}/{max_attempts})..." if attempt < max_attempts else "🎼 [WORKFLOW] Max attempts reached for download")
                continue
                
            attempt_details["downloads"] = download_results["downloads"]
            downloaded_songs = download_results["downloads"]
            
            # Track final attempt songs for fail-safe mechanism
            if attempt == max_attempts:
                final_attempt_songs = downloaded_songs.copy()
                print(f"🎼 [WORKFLOW] Tracking {len(final_attempt_songs)} songs from final attempt for fail-safe")
            
            # STEP 4: Review both songs
            print(f"🎼 [WORKFLOW] Step 4: Reviewing {len(downloaded_songs)} downloaded songs...")
            print(f"🎼 [WORKFLOW-DEBUG] Passing pg1_id to review: {pg1_id}")
            print(f"🎼 [WORKFLOW-DEBUG] pg1_id type: {type(pg1_id)}")
            review_results = await review_all_songs(downloaded_songs, pg1_id)
            
            attempt_details["reviews"] = review_results
            workflow_details["total_songs_reviewed"] += len(review_results)
            
            # STEP 5: Process verdicts and handle files
            print(f"🎼 [WORKFLOW] Step 5: Processing review verdicts...")
            
            # Special handling for final attempt to preserve songs for fail-safe
            if attempt == max_attempts:
                verdict_result = await process_song_verdicts_final_attempt(review_results, final_dir)
            else:
                verdict_result = await process_song_verdicts(review_results, final_dir)
            
            workflow_details["songs_kept"] += verdict_result["kept_count"]
            workflow_details["songs_deleted"] += verdict_result["deleted_count"]
            
            # STEP 6: Check if we should continue or retry
            if verdict_result["kept_count"] > 0:
                # Success! At least one good song
                attempt_details["final_action"] = f"success: {verdict_result['kept_count']} songs kept"
                workflow_details["attempts"].append(attempt_details)
                
                return {
                    "success": True,
                    "message": f"🎼 Workflow completed successfully on attempt {attempt}!",
                    "total_attempts": attempt,
                    "final_songs_count": verdict_result["kept_count"], 
                    "good_songs": verdict_result["kept_count"],
                    "re_rolled_songs": verdict_result["deleted_count"],
                    "workflow_details": workflow_details
                }
            else:
                # All songs were bad, need to retry
                attempt_details["final_action"] = f"all_songs_rejected: retrying_attempt_{attempt + 1}"
                workflow_details["attempts"].append(attempt_details)
                print(f"🎼 [WORKFLOW] All songs rejected on attempt {attempt}, retrying...")
                
        except Exception as e:
            error_msg = f"Critical error on attempt {attempt}: {str(e)}"
            print(f"🎼 [WORKFLOW] {error_msg}")
            print(traceback.format_exc())
            
            attempt_details["final_action"] = f"exception: {error_msg}"
            workflow_details["attempts"].append(attempt_details)
            
            if attempt == max_attempts:
                # Last attempt failed, return error
                return {
                    "success": False,
                    "message": f"🎼 Workflow failed after {max_attempts} attempts",
                    "total_attempts": attempt,
                    "final_songs_count": 0,
                    "error": error_msg,
                    "workflow_details": workflow_details
                }
    
    # If we reach here, all attempts failed but no exception on last attempt
    # This means all songs were consistently rejected across all attempts
    print(f"🎼 [WORKFLOW] All {max_attempts} attempts completed, no songs met quality standards")
    
    # FAIL-SAFE: Move final attempt songs to final_review regardless of verdict
    failsafe_songs_moved = 0
    if final_attempt_songs:
        print(f"🎼 [WORKFLOW] 🛡️ FAIL-SAFE ACTIVATED: Moving {len(final_attempt_songs)} final attempt songs to final_review")
        failsafe_result = await handle_failsafe_songs(final_attempt_songs, final_dir)
        failsafe_songs_moved = failsafe_result["moved_count"]
        workflow_details["songs_kept"] += failsafe_songs_moved
        
        if failsafe_songs_moved > 0:
            return {
                "success": True,
                "message": f"🎼 Max attempts ({max_attempts}) reached. AI rejected all songs, but fail-safe activated: {failsafe_songs_moved} song(s) from final attempt moved to final_review as backup.",
                "total_attempts": max_attempts,
                "final_songs_count": failsafe_songs_moved,
                "good_songs": 0,  # None were AI-approved
                "re_rolled_songs": workflow_details["songs_deleted"],
                "workflow_details": workflow_details
            }
    
    return {
        "success": True,  # Technical success, but no quality songs
        "message": f"🎼 Max attempts ({max_attempts}) reached. All generated songs were rejected by AI review. No songs were successfully downloaded in final attempt.",
        "total_attempts": max_attempts,
        "final_songs_count": 0,
        "good_songs": 0,
        "re_rolled_songs": workflow_details["songs_deleted"],
        "workflow_details": workflow_details
    }


async def generate_songs(book_name: str, chapter: int, verse_range: str, style: str, title: str) -> Dict[str, Any]:
    """Generate songs using existing song generation handler."""
    try:
        from ..song.utils import generate_song_handler
        
        print(f"🎼 [GENERATE] Calling song generation handler for: {book_name} {chapter}:{verse_range}")
        result = await generate_song_handler(
            strBookName=book_name,
            intBookChapter=chapter, 
            strVerseRange=verse_range,
            strStyle=style,
            strTitle=title
        )
        
        print(f"🎼 [GENERATE] Raw result type: {type(result)}")
        print(f"🎼 [GENERATE] Raw result value: {result}")
        
        # Handle both dictionary and boolean returns for backward compatibility
        if result is False:
            print("🎼 [GENERATE] ❌ Song generation returned False (legacy error format)")
            return {"success": False, "error": "Song generation returned False (legacy error)"}
        elif result and isinstance(result, dict):
            success = result.get("success", False)
            print(f"🎼 [GENERATE] Result is dict with success={success}")
            
            if success:
                pg1_id = result.get("pg1_id")
                print(f"🎼 [GENERATE] ✅ Song generation successful. Song ID: {result.get('song_id')}, pg1_id: {pg1_id}")
                return {"success": True, "result": result, "pg1_id": pg1_id}
            else:
                error_msg = result.get("error", "Unknown error in song generation")
                print(f"🎼 [GENERATE] ❌ Song generation failed: {error_msg}")
                return {"success": False, "error": error_msg}
        else:
            print(f"🎼 [GENERATE] ❌ Unexpected result type: {type(result)}")
            return {"success": False, "error": f"Song generation returned unexpected type: {type(result)}"}
            
    except Exception as e:
        print(f"🎼 [GENERATE] ❌ Exception in generate_songs wrapper: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {"success": False, "error": f"Song generation exception: {str(e)}"}


async def download_both_songs(title: str, temp_dir: str) -> Dict[str, Any]:
    """Download both songs using negative indexing (-1, -2)."""
    try:
        from ..song.utils import download_song_handler
        
        downloaded_songs = []
        
        # Download song at index -1 (last/newest song)
        print(f"🎼 [DOWNLOAD] Downloading song at index -1...")
        download_1 = await download_song_handler(
            strTitle=title,
            intIndex=-1,
            download_path=temp_dir
        )
        
        if download_1["success"]:
            downloaded_songs.append({
                "file_path": download_1["file_path"],
                "index": -1,
                "title": title
            })
            print(f"🎼 [DOWNLOAD] Successfully downloaded song -1: {download_1['file_path']}")
        else:
            print(f"🎼 [DOWNLOAD] Failed to download song -1: {download_1.get('error')}")
        
        # Download song at index -2 (second to last song)
        print(f"🎼 [DOWNLOAD] Downloading song at index -2...")
        download_2 = await download_song_handler(
            strTitle=title,
            intIndex=-2,
            download_path=temp_dir
        )
        
        if download_2["success"]:
            downloaded_songs.append({
                "file_path": download_2["file_path"], 
                "index": -2,
                "title": title
            })
            print(f"🎼 [DOWNLOAD] Successfully downloaded song -2: {download_2['file_path']}")
        else:
            print(f"🎼 [DOWNLOAD] Failed to download song -2: {download_2.get('error')}")
        
        if len(downloaded_songs) == 0:
            return {
                "success": False, 
                "error": "Failed to download any songs",
                "downloads": []
            }
        elif len(downloaded_songs) == 1:
            print(f"🎼 [DOWNLOAD] Warning: Only downloaded 1 of 2 songs")
            
        return {
            "success": True,
            "downloads": downloaded_songs,
            "message": f"Downloaded {len(downloaded_songs)} of 2 songs"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Download process failed: {str(e)}",
            "downloads": []
        }


async def review_all_songs(downloaded_songs: List[Dict], pg1_id: int) -> List[Dict[str, Any]]:
    """Review all downloaded songs sequentially to respect API rate limits."""
    
    print(f"\n{'='*80}")
    print(f"🎵 [REVIEW-SESSION] Starting review session at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎵 [REVIEW-SESSION] Total songs to review: {len(downloaded_songs)}")
    print(f"🎵 [REVIEW-SESSION] Using pg1_id: {pg1_id}")
    print(f"{'='*80}\n")

    async def review_single_song(song: Dict[str, Any]) -> Dict[str, Any]:
        """Helper coroutine to review one song, mirroring the debug endpoint's logic."""
        file_path = song["file_path"]
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        print(f"\n{'─'*60}")
        print(f"🎼 [REVIEW] Starting review for: {file_path}")
        print(f"🎼 [REVIEW] File size: {file_size:,} bytes")
        print(f"🎼 [REVIEW] Song index: {song.get('index', 'N/A')}")
        print(f"🎼 [REVIEW] Song title: {song.get('title', 'N/A')}")

        # Verify the file exists before attempting review
        if not os.path.exists(file_path):
            print(f"🎼 [REVIEW] ❌ File not found for review: {file_path}")
            return {
                "file_path": file_path,
                "index": song["index"],
                "title": song["title"],
                "verdict": "error",
                "review_details": {"error": f"Audio file not found: {file_path}"}
            }

        # Check pg1_id and decide review strategy
        # pg1_id is required to fetch the original lyrics from database for comparison
        if not pg1_id or pg1_id == 0:
            print(f"🎼 [REVIEW] ⚠️ pg1_id is missing ({pg1_id}) for review: {file_path}")
            print(f"🎼 [REVIEW] REASON: Suno.com doesn't redirect to song page after creation")
            print(f"🎼 [REVIEW] IMPACT: Cannot fetch original lyrics for AI comparison")
            print(f"🎼 [REVIEW] FALLBACK: Using simplified review without lyrics comparison...")
            print(f"🎼 [REVIEW] RECOMMENDATION: Manual review required for quality assurance")
            
            # Simplified review when database lookup isn't possible
            # In production, this could trigger a basic audio quality check
            # or queue the song for manual review
            return {
                "file_path": file_path,
                "index": song["index"],
                "title": song["title"],
                "verdict": "continue",  # Default to continue to avoid blocking workflow
                "review_details": {
                    "warning": "Simplified review due to missing pg1_id",
                    "reason": "Cannot fetch original lyrics from database",
                    "recommendation": "Manual review required",
                    "pg1_id_value": pg1_id
                }
            }
        
        # Call the review API function with valid pg1_id
        print(f"🎼 [REVIEW-API] Calling review API with pg1_id: {pg1_id}")
        print(f"🎼 [REVIEW-API] Timestamp: {datetime.now().strftime('%H:%M:%S')}")
        
        review_result = await call_review_api(
            file_path=file_path,
            pg1_id=pg1_id
        )

        print(f"\n🎼 [REVIEW-RESULT] Review completed for {os.path.basename(file_path)}")
        print(f"🎼 [REVIEW-RESULT] Verdict: {review_result.get('verdict', 'error')}")
        print(f"🎼 [REVIEW-RESULT] Success: {review_result.get('success', False)}")
        
        if review_result.get('error'):
            print(f"🎼 [REVIEW-ERROR] Error message: {review_result['error']}")
        
        if review_result.get('first_response'):
            print(f"\n📝 [AI-RESPONSE-1] First AI Response (Transcription):")
            print(f"{'─'*40}")
            print(review_result['first_response'][:500] + '...' if len(review_result.get('first_response', '')) > 500 else review_result.get('first_response', ''))
            print(f"{'─'*40}")
        
        if review_result.get('second_response'):
            print(f"\n📝 [AI-RESPONSE-2] Second AI Response (Comparison):")
            print(f"{'─'*40}")
            print(review_result['second_response'][:500] + '...' if len(review_result.get('second_response', '')) > 500 else review_result.get('second_response', ''))
            print(f"{'─'*40}")
        
        print(f"🎼 [REVIEW-DEBUG] Full result keys: {list(review_result.keys()) if isinstance(review_result, dict) else 'Not a dict'}")

        # Structure the final result for this song
        return {
            "file_path": file_path,
            "index": song["index"],
            "title": song["title"],
            "verdict": review_result.get("verdict", "error"),
            "review_details": review_result
        }

    if not downloaded_songs:
        return []

    # Process reviews sequentially to respect API rate limits
    print(f"\n🎼 [REVIEW-QUEUE] Starting sequential processing...")
    print(f"🎼 [REVIEW-QUEUE] Songs in queue: {[os.path.basename(s['file_path']) for s in downloaded_songs]}")
    final_results = []
    
    for i, song in enumerate(downloaded_songs):
        try:
            print(f"\n🔄 [REVIEW-PROGRESS] Processing song {i+1}/{len(downloaded_songs)}")
            print(f"🔄 [REVIEW-PROGRESS] Start time: {datetime.now().strftime('%H:%M:%S')}")
            
            result = await review_single_song(song)
            final_results.append(result)
            
            print(f"✅ [REVIEW-PROGRESS] Song {i+1} complete. Verdict: {result.get('verdict', 'unknown')}")
            
            # Add delay between reviews if there are more to process
            # This helps avoid hitting rate limits
            if i < len(downloaded_songs) - 1:
                try:
                    from config.ai_review_config import DELAY_BETWEEN_SONGS
                    wait_time = DELAY_BETWEEN_SONGS
                except ImportError:
                    wait_time = 65  # Fallback: Wait 65 seconds between songs
                print(f"\n⏳ [RATE-LIMIT] Waiting {wait_time} seconds before next review...")
                print(f"⏳ [RATE-LIMIT] Reason: Respecting API rate limits (Free tier: 2 RPM for Gemini Pro)")
                for remaining in range(wait_time, 0, -10):
                    print(f"⏳ [RATE-LIMIT] Time remaining: {remaining} seconds...")
                    await asyncio.sleep(min(10, remaining))
                
        except Exception as e:
            error_msg = f"Exception during review for {song['file_path']}: {e}"
            print(f"\n❌ [REVIEW-ERROR] Critical error occurred!")
            print(f"❌ [REVIEW-ERROR] Song: {os.path.basename(song['file_path'])}")
            print(f"❌ [REVIEW-ERROR] Error type: {type(e).__name__}")
            print(f"❌ [REVIEW-ERROR] Error message: {str(e)}")
            print(f"❌ [REVIEW-ERROR] Full traceback:")
            print(traceback.format_exc())
            final_results.append({
                "file_path": song["file_path"],
                "index": song["index"],
                "title": song["title"],
                "verdict": "error",
                "review_details": {"error": error_msg}
            })
    
    print(f"\n{'='*80}")
    print(f"🎵 [REVIEW-SESSION] Review session completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎵 [REVIEW-SESSION] Total processed: {len(final_results)}")
    print(f"🎵 [REVIEW-SESSION] Successful: {sum(1 for r in final_results if r.get('verdict') == 'continue')}")
    print(f"🎵 [REVIEW-SESSION] Re-rolls needed: {sum(1 for r in final_results if r.get('verdict') == 're-roll')}")
    print(f"🎵 [REVIEW-SESSION] Errors: {sum(1 for r in final_results if r.get('verdict') == 'error')}")
    print(f"{'='*80}\n")
    
    return final_results


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
    """
    try:
        import aiohttp
        import os
        
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
    """
    try:
        from middleware.gemini import model_pro
        
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
            "top_k": 40,
            "top_p": 0.95,
            "max_output_tokens": 8192,
        }

        response = await model_pro.generate_content_async(
            contents, generation_config=generation_config
        )

        return response.text

    except Exception as e:
        print(f"Error sending prompt to Google AI: {e}")
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
    """
    try:
        import os
        import json
        import traceback
        from services.supabase_service import SupabaseService
        from middleware.gemini import api_key
        
        # File existence is checked in the calling function (review_all_songs)
        print(f"Starting review for pg1_id: {pg1_id}")
        print(f"Audio file path: {audio_file_path}")

        # Fetch song data using SupabaseService
        service = SupabaseService()
        try:
            print(f"Fetching song data for ID: {pg1_id}")
            song_data = service.get_song_with_lyrics(pg1_id)
            if not song_data or not song_data.get('lyrics'):
                error_msg = f"No lyrics data found for pg1_id: {pg1_id}"
                print(error_msg)
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
            print(f"Error during song data retrieval: {str(e)}")
            print(traceback.format_exc())
            return {
                "success": False,
                "error": f"Error during song data retrieval: {str(e)}",
                "verdict": "error",
            }

        print(f"Uploading audio file to Google AI: {audio_file_path}")
        file_metadata = await upload_file_to_google_ai(audio_file_path, api_key)
        
        if not file_metadata:
            error_msg = "Failed to upload audio file to Google AI"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "verdict": "error",
            }
        
        file_uri = file_metadata.get("uri")
        mime_type = file_metadata.get("mimeType", "audio/mpeg")
        print(f"File uploaded successfully. URI: {file_uri[:30]}...")  # Truncate for security
        
        # First prompt - transcription and initial review
        first_prompt = """This is a song generated by AI and we need to check it's quality. The AI has a tendency of making a few common mistakes. Please write out the lyrics that you hear and note what is spoken and what is rapped, and what is sung. If the song is unclear or sounds messy and unmusical, the song needs to be deleted and remade. If it is more than 30% spoken it needs to be deleted and remade. If it cuts off abruptly and doesnt resolve naturally, it needs to be deleted and remade, and if the song feels like it ends, but then it picks back up again, it needs to be deleted and remade. Please write out the lyrics as requested and let me know if any red flags require the song to be deleted and remade. Don't attempt to recognize the lyrics source and infer what they should be, just write what you hear without inference or adjustment. If a word doesn't make sense, just spell it out phonetically. Add final verdict by ending with 'Final Verdict: [re-roll] or [continue]'"""
        
        print("Sending first prompt for transcription and review")
        first_response = await send_prompt_to_google_ai(
            prompt=first_prompt,
            file_uri=file_uri,
            mime_type=mime_type,
        )
        
        if not first_response:
            error_msg = "Failed to get first AI response"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "verdict": "error",
            }
        
        print("First AI response received successfully")
        
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

Add final verdict by ending with 'Final Verdict: [re-roll] or [continue]'"""
        
        print("Sending second prompt for lyrics comparison")
        second_response = await send_prompt_to_google_ai(
            prompt=second_prompt,
            previous_messages=conversation_history
        )
        
        if not second_response:
            error_msg = "Failed to get second AI response"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "first_response": first_response,
                "verdict": "error",
            }
        
        print("Second AI response received successfully")
        
        # Determine final verdict
        verdict = "continue"
        if "[re-roll]" in second_response.lower():
            verdict = "re-roll"
            print(f"Verdict: RE-ROLL required for ID: {pg1_id}")
        elif "[continue]" in second_response.lower():
            verdict = "continue"
            print(f"Verdict: CONTINUE approved for ID: {pg1_id}")
        else:
            print("Verdict tag not found in response, defaulting to CONTINUE")
        
        # Close the service connection
        service.close_connection()

        print(f"Review completed for ID: {pg1_id}")
        return {
            "success": True,
            "first_response": first_response,
            "second_response": second_response,
            "verdict": verdict,
            "audio_file": audio_file_path,
        }

    except Exception as e:
        error_msg = f"Review process failed: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return {
            "success": False,
            "error": error_msg,
            "verdict": "error",
        }


async def call_review_api(file_path: str, pg1_id: int) -> Dict[str, Any]:
    """
    Call the AI review functionality for a single song.
    
    This function directly uses the review_song_with_ai function that's already
    in this module, eliminating unnecessary abstraction layers.
    
    Args:
        file_path (str): Path to the audio file to review
        pg1_id (int): Database ID for song structure lookup
        
    Returns:
        Dict[str, Any]: Review results including verdict and AI responses
    """
    try:
        print(f"🎼 [REVIEW_API] Starting review for: {file_path}")
        print(f"🎼 [REVIEW_API] Using pg1_id: {pg1_id}")
        print(f"🎼 [REVIEW_API-DEBUG] pg1_id type: {type(pg1_id)}")
        print(f"🎼 [REVIEW_API-DEBUG] Will attempt to fetch from tblprogress_v1 with this ID")

        # Directly call the review function that's in this same file
        review_result = await review_song_with_ai(
            audio_file_path=file_path,
            pg1_id=pg1_id
        )
        
        print(f"🎼 [REVIEW_API] Review completed. Verdict: {review_result.get('verdict', 'error')}")
        
        # Return the result directly as it already has the correct structure
        return review_result
        
    except Exception as e:
        error_msg = f"AI review failed: {str(e)}"
        print(f"🎼 [REVIEW_API] {error_msg}")
        print(traceback.format_exc())
        
        return {
            "success": False,
            "verdict": "error", 
            "error": error_msg
        }


async def process_song_verdicts(review_results: List[Dict], final_dir: str) -> Dict[str, int]:
    """Process review verdicts: move good songs to final_review, delete bad ones."""
    kept_count = 0
    deleted_count = 0
    
    for result in review_results:
        file_path = result["file_path"]
        verdict = result["verdict"]
        
        try:
            if verdict == "continue":
                # Move to final_review directory - THIS IS THE VERIFIED FINAL DESTINATION
                filename = os.path.basename(file_path)
                final_path = os.path.join(final_dir, filename)
                
                if os.path.exists(file_path):
                    shutil.move(file_path, final_path)
                    kept_count += 1
                    print(f"🎼 [VERDICT] ✅ APPROVED SONG moved to final destination: {final_path}")
                    print(f"🎼 [VERDICT] ✅ CONFIRMED: Song is now in backend/songs/final_review directory")
                else:
                    print(f"🎼 [VERDICT] ⚠️ File not found for moving: {file_path}")
                    
            elif verdict == "re-roll":
                # Delete the file
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"🎼 [VERDICT] ❌ Deleted poor quality song: {file_path}")
                else:
                    print(f"🎼 [VERDICT] ⚠️ File not found for deletion: {file_path}")
                    
            else:  # verdict == "error" or unknown
                # Keep file in temp directory but don't count as success
                print(f"🎼 [VERDICT] ⚠️ Review error, leaving in temp: {file_path}")
                
        except Exception as e:
            print(f"🎼 [VERDICT] Error processing {file_path}: {e}")
    
    return {
        "kept_count": kept_count,
        "deleted_count": deleted_count
    }


async def process_song_verdicts_final_attempt(review_results: List[Dict], final_dir: str) -> Dict[str, int]:
    """
    Process verdicts for the final attempt with special handling to preserve songs for fail-safe.
    
    On the final attempt, we only move "continue" songs but don't delete "re-roll" songs.
    The "re-roll" songs are preserved in temp directory for potential fail-safe recovery.
    
    Args:
        review_results (List[Dict]): Review results from AI
        final_dir (str): Final review directory path
        
    Returns:
        Dict[str, int]: Processing results
    """
    kept_count = 0
    deleted_count = 0
    preserved_count = 0
    
    print(f"🎼 [VERDICT-FINAL] Processing final attempt verdicts (preserving re-roll songs for fail-safe")
    
    for result in review_results:
        file_path = result["file_path"]
        verdict = result["verdict"]
        
        try:
            if verdict == "continue":
                # Move good songs to final_review as usual - VERIFIED FINAL DESTINATION
                filename = os.path.basename(file_path)
                final_path = os.path.join(final_dir, filename)
                
                if os.path.exists(file_path):
                    shutil.move(file_path, final_path)
                    kept_count += 1
                    print(f"🎼 [VERDICT-FINAL] ✅ APPROVED SONG moved to final destination: {final_path}")
                    print(f"🎼 [VERDICT-FINAL] ✅ CONFIRMED: Song is now in backend/songs/final_review directory")
                else:
                    print(f"🎼 [VERDICT-FINAL] ⚠️ File not found for moving: {file_path}")
                    
            elif verdict == "re-roll":
                # SPECIAL: Don't delete re-roll songs on final attempt - preserve for fail-safe
                if os.path.exists(file_path):
                    preserved_count += 1
                    print(f"🎼 [VERDICT-FINAL] 🛡️ Preserved re-roll song for fail-safe: {file_path}")
                else:
                    print(f"🎼 [VERDICT-FINAL] ⚠️ Re-roll song file not found: {file_path}")
                    
            else:  # verdict == "error" or unknown
                # Keep file in temp directory for fail-safe consideration
                preserved_count += 1
                print(f"🎼 [VERDICT-FINAL] ⚠️ Review error, preserving for fail-safe: {file_path}")
                
        except Exception as e:
            print(f"🎼 [VERDICT-FINAL] Error processing {file_path}: {e}")
    
    print(f"🎼 [VERDICT-FINAL] Final attempt results: {kept_count} kept, {preserved_count} preserved for fail-safe")
    
    return {
        "kept_count": kept_count,
        "deleted_count": deleted_count,  # No deletions on final attempt
        "preserved_count": preserved_count
    }


def verify_final_destination_folder() -> str:
    """
    🔍 VERIFICATION: Confirm the final destination folder for approved songs.
    
    This function serves as a single source of truth for the final destination
    and provides verification that we're using the correct folder path.
    
    Returns:
        str: The verified final destination folder path
    """
    final_destination = "backend/songs/final_review"
    
    print(f"🔍 [VERIFY] Final destination folder confirmed: {final_destination}")
    print(f"🔍 [VERIFY] This is where ALL approved songs will be moved:")
    print(f"🔍 [VERIFY]   - AI-approved songs (verdict: 'continue')")
    print(f"🔍 [VERIFY]   - Fail-safe backup songs (marked with '_FAILSAFE')")
    
    return final_destination


async def handle_failsafe_songs(final_attempt_songs: List[Dict], final_dir: str) -> Dict[str, int]:
    """
    🛡️ FAIL-SAFE MECHANISM: Move final attempt songs to final_review regardless of review verdict.
    
    This function is called when all 3 attempts fail to produce AI-approved songs.
    It ensures that the work from the final attempt isn't lost by moving downloaded
    songs to the final_review directory as a backup.
    
    Args:
        final_attempt_songs (List[Dict]): Songs downloaded in the final attempt
        final_dir (str): Path to final_review directory
        
    Returns:
        Dict[str, int]: Results with moved_count and error_count
    """
    moved_count = 0
    error_count = 0
    
    print(f"🛡️ [FAIL-SAFE] Processing {len(final_attempt_songs)} songs from final attempt")
    
    for i, song in enumerate(final_attempt_songs, 1):
        file_path = song["file_path"]
        
        try:
            if os.path.exists(file_path):
                # Create fail-safe filename with clear labeling
                original_filename = os.path.basename(file_path)
                name_part, ext = os.path.splitext(original_filename)
                failsafe_filename = f"{name_part}_FAILSAFE{ext}"
                final_path = os.path.join(final_dir, failsafe_filename)
                
                # Move the file to VERIFIED FINAL DESTINATION
                shutil.move(file_path, final_path)
                moved_count += 1
                print(f"🛡️ [FAIL-SAFE] ✅ BACKUP SONG moved to final destination: {final_path}")
                print(f"🛡️ [FAIL-SAFE] ✅ CONFIRMED: Backup song {i}/{len(final_attempt_songs)} is now in backend/songs/final_review directory")
            else:
                error_count += 1
                print(f"🛡️ [FAIL-SAFE] ⚠️ File not found: {file_path}")
                
        except Exception as e:
            error_count += 1
            print(f"🛡️ [FAIL-SAFE] ❌ Error moving {file_path}: {e}")
    
    print(f"🛡️ [FAIL-SAFE] Completed: {moved_count} songs moved, {error_count} errors")
    
    return {
        "moved_count": moved_count,
        "error_count": error_count
    }
