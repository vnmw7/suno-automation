"""
System: Suno Automation
Module: Orchestrator Utils
File URL: backend/api/orchestrator/utils.py
Purpose: Coordinate generation, download, review, and verdict handling including remote deletion.
"""

import os
import shutil
import asyncio
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

import aiohttp
from aiohttp import ClientError, ClientTimeout

from utils.delete_song import delete_song


# CDN-first download strategy attempts CDN once per song ID before falling back to browser automation.
# A 30-second timeout and timestamp-based collision handling protect existing pending_review assets.
CDN_BASE_URL = "https://cdn1.suno.ai"
CDN_TIMEOUT_SECONDS = 30
CDN_STREAM_CHUNK_SIZE = 64 * 1024

def _is_likely_mp3_header(header_bytes: bytes) -> bool:
    if not header_bytes or len(header_bytes) < 2:
        return False
    if header_bytes.startswith(b"ID3"):
        return True
    return header_bytes[0] == 0xFF and (header_bytes[1] & 0xE0) == 0xE0

def _resolve_collision_path(candidate_path: Path) -> Path:
    if not candidate_path.exists():
        return candidate_path
    timestamp_suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return candidate_path.with_name(f"{candidate_path.stem}_{timestamp_suffix}{candidate_path.suffix}")

def _remove_path_if_exists(target_path: Path) -> None:
    if target_path.exists():
        target_path.unlink()

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
    failsafe_dir = "backend/songs/fail_safe"

    # Ensure required directories exist
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(final_dir, exist_ok=True)
    os.makedirs(failsafe_dir, exist_ok=True)

    print(f"🎼 [WORKFLOW] ✅ VERIFIED: Final approved songs will be moved to: {final_dir}")
    print(f"🎼 [WORKFLOW] ✅ VERIFIED: Temporary downloads will be stored in: {temp_dir}")
    print(f"🎼 [WORKFLOW] ✅ VERIFIED: Fail-safe songs will be moved to: {failsafe_dir}")
    
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
            print("🎼 [WORKFLOW] Step 1: Generating songs...")
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
                print("🎼 [WORKFLOW] This is EXPECTED if Suno didn't redirect to song page")
                print("🎼 [WORKFLOW] Songs were generated but database tracking may be incomplete.")
                print("🎼 [WORKFLOW] Proceeding with download and review using fallback methods...")
                print("🎼 [WORKFLOW] Manual review will be recommended for these songs")

            # Log successful generation details and extract song_ids
            song_id = None
            song_ids = []  # Array to hold ALL song IDs from generation
            if "result" in generation_result:
                result = generation_result["result"]
                song_id = result.get("song_id")  # Keep for backward compatibility
                song_ids = result.get("song_ids", [])  # Get ALL song IDs (Suno creates 2)

                # Fallback: if no song_ids array but have single song_id
                if not song_ids and song_id:
                    song_ids = [song_id]

                print("🎼 [WORKFLOW] ✅ Generation successful!")
                print(f"🎼 [WORKFLOW] First Song ID: {song_id}")
                print(f"🎼 [WORKFLOW] All Song IDs: {song_ids}")
                print(f"🎼 [WORKFLOW] pg1_id: {pg1_id}")

            # STEP 2: Wait for Suno processing
            wait_time_seconds = 60
            print(f"🎼 [WORKFLOW] Step 2: Waiting for Suno processing ({wait_time_seconds} seconds)...")
            print(f"🎼 [WORKFLOW] ⏳ Starting wait at: {asyncio.get_event_loop().time()}")
            await asyncio.sleep(wait_time_seconds)
            print(f"🎼 [WORKFLOW] ⏰ Wait completed at: {asyncio.get_event_loop().time()}")

            # STEP 3: Download both songs
            print("🎼 [WORKFLOW] Step 3: Downloading both generated songs...")
            print(f"🎼 [WORKFLOW] Download parameters: title='{title}', temp_dir='{temp_dir}'")
            print(f"🎼 [WORKFLOW] Song IDs for downloads: {song_ids if song_ids else 'None available'}")

            download_results = await download_both_songs(title, temp_dir, song_ids)
            
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
            print("🎼 [WORKFLOW] Step 5: Processing review verdicts...")
            
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

    # FAIL-SAFE: Only activate if absolutely NO songs remain (all were deleted)
    # This is a true emergency fail-safe, not a quality bypass
    failsafe_songs_moved = 0

    # Check if any songs were preserved (not deleted) in the final attempt
    final_preserved = 0
    if workflow_details["attempts"] and len(workflow_details["attempts"]) >= max_attempts:
        final_attempt_data = workflow_details["attempts"][-1]
        if "reviews" in final_attempt_data:
            for review in final_attempt_data["reviews"]:
                if review.get("verdict") == "error" or (review.get("verdict") == "re-roll" and os.path.exists(review.get("file_path", ""))):
                    final_preserved += 1

    # Only activate fail-safe if we have some songs AND no songs made it through
    if final_attempt_songs and workflow_details["songs_kept"] == 0 and final_preserved > 0:
        print(f"🎼 [WORKFLOW] 🛡️ EMERGENCY FAIL-SAFE: Found {final_preserved} preserved songs from errors")
        print("🎼 [WORKFLOW] 🛡️ Note: All re-roll songs were deleted as they had critical failures")

        # Only move preserved songs (those with errors, not re-rolls that were deleted)
        preserved_songs = []
        for song in final_attempt_songs:
            if os.path.exists(song["file_path"]):
                preserved_songs.append(song)

        if preserved_songs:
            print(f"🎼 [WORKFLOW] 🛡️ Moving {len(preserved_songs)} error/preserved songs to fail_safe directory")
            failsafe_result = await handle_failsafe_songs(preserved_songs)  # No need to pass final_dir
            failsafe_songs_moved = failsafe_result["moved_count"]
            workflow_details["songs_kept"] += failsafe_songs_moved

            if failsafe_songs_moved > 0:
                return {
                    "success": True,
                    "message": f"🎼 Max attempts ({max_attempts}) reached. All songs with critical failures were deleted. Emergency fail-safe activated for {failsafe_songs_moved} song(s) with review errors.",
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
        print('🎼 [GENERATE] Preparing to close any blocking modal before lyric entry')
        result = await generate_song_handler(
            strBookName=book_name,
            intBookChapter=chapter, 
            strVerseRange=verse_range,
            strStyle=style,
            strTitle=title,
            blnCloseModal=True
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


async def downloadSongsFromCdn(
    song_id: str,
    download_dir: str,
    *,
    session: Optional[aiohttp.ClientSession] = None,
    base_url: Optional[str] = None,
    timeout_seconds: int = CDN_TIMEOUT_SECONDS,
    chunk_size: int = CDN_STREAM_CHUNK_SIZE
) -> Dict[str, Any]:
    """Fetch an MP3 from the CDN, validating headers and preserving Result-pattern semantics."""
    if not song_id:
        return {
            "success": False,
            "song_id": song_id,
            "error": "Missing song_id value"
        }

    download_directory = Path(download_dir)
    download_directory.mkdir(parents=True, exist_ok=True)

    resolved_base_url = (base_url or CDN_BASE_URL).rstrip("/")
    cdn_url = f"{resolved_base_url}/{song_id}.mp3"

    candidate_path = download_directory / f"{song_id}.mp3"
    final_path = _resolve_collision_path(candidate_path)
    temp_path = final_path.with_suffix(f"{final_path.suffix}.part")

    session_timeout = ClientTimeout(total=timeout_seconds)
    uses_ephemeral_session = False
    active_session = session
    if active_session is None:
        active_session = aiohttp.ClientSession(timeout=session_timeout)
        uses_ephemeral_session = True

    first_chunk: bytes = b""
    try:
        print(f"📥 [CDN] Fetching {song_id} from {cdn_url}")
        async with active_session.get(cdn_url, timeout=session_timeout) as response:
            if response.status != 200:
                error_message = f"HTTP {response.status}: {response.reason or 'Unknown response'}"
                print(f"📥 [CDN] ❌ {error_message}")
                return {
                    "success": False,
                    "song_id": song_id,
                    "error": error_message
                }

            with temp_path.open("wb") as destination:
                async for chunk in response.content.iter_chunked(chunk_size):
                    if not chunk:
                        continue
                    if not first_chunk:
                        first_chunk = chunk
                    destination.write(chunk)

            if not first_chunk:
                _remove_path_if_exists(temp_path)
                empty_message = "Empty response body from CDN"
                return {
                    "success": False,
                    "song_id": song_id,
                    "error": empty_message
                }

            if not _is_likely_mp3_header(first_chunk):
                _remove_path_if_exists(temp_path)
                return {
                    "success": False,
                    "song_id": song_id,
                    "error": "Invalid MP3 header returned by CDN"
                }

            if temp_path.stat().st_size == 0:
                _remove_path_if_exists(temp_path)
                return {
                    "success": False,
                    "song_id": song_id,
                    "error": "Downloaded file is empty"
                }

            os.replace(temp_path, final_path)
            file_size = final_path.stat().st_size
            print(f"📥 [CDN] ✅ Downloaded {song_id} ({file_size:,} bytes) -> {final_path}")
            return {
                "success": True,
                "song_id": song_id,
                "file_path": str(final_path),
                "message": "Downloaded from CDN"
            }

    except asyncio.TimeoutError:
        _remove_path_if_exists(temp_path)
        timeout_message = f"CDN request timed out after {timeout_seconds} seconds"
        print(f"📥 [CDN] ❌ {timeout_message}")
        return {
            "success": False,
            "song_id": song_id,
            "error": timeout_message
        }
    except ClientError as exc:
        _remove_path_if_exists(temp_path)
        error_message = f"CDN request failed: {str(exc)}"
        print(f"📥 [CDN] ❌ {error_message}")
        return {
            "success": False,
            "song_id": song_id,
            "error": error_message
        }
    except Exception as exc:
        _remove_path_if_exists(temp_path)
        error_message = f"Unexpected CDN error: {str(exc)}"
        print(f"📥 [CDN] ❌ {error_message}")
        return {
            "success": False,
            "song_id": song_id,
            "error": error_message
        }
    finally:
        if uses_ephemeral_session and active_session is not None:
            await active_session.close()


async def download_both_songs(title: str, temp_dir: str, song_ids: list = None) -> Dict[str, Any]:
    """Download both songs via CDN-first strategy with Playwright fallback for resilience.

    Args:
        title: Song title to search for
        temp_dir: Directory to save downloads
        song_ids: Optional list of song IDs for direct navigation to song pages
    """
    try:
        from utils.download_song_v2 import download_song_v2

        downloaded_songs: List[Dict[str, Any]] = []
        existing_file_paths: Set[str] = set()
        cdn_failures: List[Dict[str, Any]] = []
        index_configs = [
            {"index": -1, "label": "[DOWNLOAD-1]", "song_id": song_ids[0] if song_ids and len(song_ids) > 0 else None},
            {"index": -2, "label": "[DOWNLOAD-2]", "song_id": song_ids[1] if song_ids and len(song_ids) > 1 else None},
        ]
        successful_cdn_indices: Set[int] = set()

        if song_ids:
            print("\n📥 [CDN] Starting CDN-first download attempts...")
            for config in index_configs:
                current_song_id = config["song_id"]
                label = config["label"]
                index_value = config["index"]
                if not current_song_id:
                    continue

                cdn_result = await downloadSongsFromCdn(
                    song_id=current_song_id,
                    download_dir=temp_dir
                )

                if cdn_result.get("success"):
                    file_path = cdn_result.get("file_path")
                    print(f"📥 {label} CDN success: {file_path}")
                    if file_path and file_path not in existing_file_paths:
                        downloaded_songs.append({
                            "file_path": file_path,
                            "title": title,
                            "song_id": current_song_id
                        })
                        existing_file_paths.add(file_path)
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            print(f"📥 {label} File size: {file_size:,} bytes")
                    successful_cdn_indices.add(index_value)
                else:
                    error_detail = cdn_result.get("error", "Unknown CDN error")
                    print(f"📥 {label} CDN failed: {error_detail}")
                    cdn_failures.append({
                        "song_id": current_song_id,
                        "error": error_detail
                    })

        if cdn_failures:
            failure_summaries = ', '.join(f"{failure['song_id']}: {failure['error']}" for failure in cdn_failures)
            print(f"📥 [CDN] Triggering Playwright fallback for CDN issues -> {failure_summaries}")

        async def _download_with_playwright(config: Dict[str, Any]) -> None:
            index_value = config["index"]
            label = config["label"]
            direct_song_id = config["song_id"]

            print(f"\n📥 {label} ===========")
            print(f"📥 {label} Starting download for song at index {index_value}")
            print(f"📥 {label} Title: '{title}'")
            print(f"📥 {label} Temp directory: '{temp_dir}'")
            if direct_song_id:
                print(f"📥 {label} Using song_id for direct navigation: {direct_song_id}")
            else:
                print(f"📥 {label} No song_id available, will navigate to /me page")
            print(f"📥 {label} Calling download_song_v2...")

            download_result = await download_song_v2(
                strTitle=title,
                intIndex=index_value,
                download_path=temp_dir,
                song_id=direct_song_id
            )

            print(f"📥 {label} Download completed")
            print(f"📥 {label} Success: {download_result.get('success')}")

            if download_result.get("success"):
                fallback_song_id = download_result.get("song_id") or direct_song_id
                file_path = download_result.get("file_path")
                if file_path and file_path not in existing_file_paths:
                    downloaded_songs.append({
                        "file_path": file_path,
                        "title": title,
                        "song_id": fallback_song_id
                    })
                    existing_file_paths.add(file_path)
                    print(f"📥 {label} ✅ Successfully downloaded")
                    print(f"📥 {label} File path: {file_path}")
                    if fallback_song_id:
                        print(f"📥 {label} Song ID: {fallback_song_id}")
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        print(f"📥 {label} File size: {file_size:,} bytes")
                else:
                    print(f"📥 {label} ⚠️ Duplicate file path detected, skipping append")
            else:
                print(f"📥 {label} ❌ Failed to download")
                print(f"📥 {label} Error: {download_result.get('error')}")

        for config in index_configs:
            if config["index"] in successful_cdn_indices:
                print(f"📥 {config['label']} Skipping Playwright fallback; CDN download succeeded.")
                continue
            await _download_with_playwright(config)

        if len(downloaded_songs) == 0:
            return {
                "success": False,
                "error": "Failed to download any songs",
                "downloads": []
            }
        if len(downloaded_songs) == 1:
            print("🎼 [DOWNLOAD] Warning: Only downloaded 1 of 2 songs")

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
        print(f"🎼 [REVIEW] Song title: {song.get('title', 'N/A')}")
        print(f"🎼 [REVIEW] Song ID: {song.get('song_id', 'N/A')}")

        # Verify the file exists before attempting review
        if not os.path.exists(file_path):
            print(f"🎼 [REVIEW] ❌ File not found for review: {file_path}")
            return {
                "file_path": file_path,
                "title": song["title"],
                "song_id": song.get("song_id"),
                "verdict": "error",
                "review_details": {"error": f"Audio file not found: {file_path}"}
            }

        # Check pg1_id and decide review strategy
        # pg1_id is required to fetch the original lyrics from database for comparison
        if not pg1_id or pg1_id == 0:
            print(f"🎼 [REVIEW] ⚠️ pg1_id is missing ({pg1_id}) for review: {file_path}")
            print("🎼 [REVIEW] REASON: Suno.com doesn't redirect to song page after creation")
            print("🎼 [REVIEW] IMPACT: Cannot fetch original lyrics for AI comparison")
            print("🎼 [REVIEW] FALLBACK: Using simplified review without lyrics comparison...")
            print("🎼 [REVIEW] RECOMMENDATION: Manual review required for quality assurance")
            
            # Simplified review when database lookup isn't possible
            # In production, this could trigger a basic audio quality check
            # or queue the song for manual review
            return {
                "file_path": file_path,
                "title": song["title"],
                "song_id": song.get("song_id"),
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
            print("\n📝 [AI-RESPONSE-1] First AI Response (Transcription):")
            print(f"{'─'*40}")
            print(review_result['first_response'][:500] + '...' if len(review_result.get('first_response', '')) > 500 else review_result.get('first_response', ''))
            print(f"{'─'*40}")
        
        if review_result.get('second_response'):
            print("\n📝 [AI-RESPONSE-2] Second AI Response (Comparison):")
            print(f"{'─'*40}")
            print(review_result['second_response'][:500] + '...' if len(review_result.get('second_response', '')) > 500 else review_result.get('second_response', ''))
            print(f"{'─'*40}")
        
        print(f"🎼 [REVIEW-DEBUG] Full result keys: {list(review_result.keys()) if isinstance(review_result, dict) else 'Not a dict'}")

        # Structure the final result for this song
        return {
            "file_path": file_path,
            "title": song["title"],
            "song_id": song.get("song_id"),
            "verdict": review_result.get("verdict", "error"),
            "review_details": review_result
        }

    if not downloaded_songs:
        return []

    # Process reviews sequentially to respect API rate limits
    print("\n🎼 [REVIEW-QUEUE] Starting sequential processing...")
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
                    wait_time = 10  # Fallback: Wait 10 seconds between songs (Gemini Flash)
                print(f"\n⏳ [RATE-LIMIT] Waiting {wait_time} seconds before next review...")
                print("⏳ [RATE-LIMIT] Reason: Respecting API rate limits (Free tier: 15 RPM for Gemini Flash)")
                for remaining in range(wait_time, 0, -10):
                    print(f"⏳ [RATE-LIMIT] Time remaining: {remaining} seconds...")
                    await asyncio.sleep(min(10, remaining))
                
        except Exception as e:
            error_msg = f"Exception during review for {song['file_path']}: {e}"
            print("\n❌ [REVIEW-ERROR] Critical error occurred!")
            print(f"❌ [REVIEW-ERROR] Song: {os.path.basename(song['file_path'])}")
            print(f"❌ [REVIEW-ERROR] Error type: {type(e).__name__}")
            print(f"❌ [REVIEW-ERROR] Error message: {str(e)}")
            print("❌ [REVIEW-ERROR] Full traceback:")
            print(traceback.format_exc())
            final_results.append({
                "file_path": song["file_path"],
                "title": song["title"],
                "song_id": song.get("song_id"),
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
        from middleware.gemini import model_flash
        
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

        response = await model_flash.generate_content_async(
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
        
        # Add delay after upload to respect API rate limits
        try:
            from backend.config.ai_review_config import DELAY_BETWEEN_API_CALLS
            wait_time = DELAY_BETWEEN_API_CALLS
        except ImportError:
            wait_time = 5  # Fallback: 5 seconds for Gemini Flash free tier
        
        print(f"⏳ [RATE-LIMIT] Waiting {wait_time} seconds after file upload...")
        print("⏳ [RATE-LIMIT] Reason: Respecting API rate limits between upload and first prompt")
        for remaining in range(wait_time, 0, -10):
            print(f"⏳ [RATE-LIMIT] Time remaining: {remaining} seconds...")
            await asyncio.sleep(min(10, remaining))
        
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
        
        # Add delay between first and second prompt to respect API rate limits
        try:
            from backend.config.ai_review_config import DELAY_BETWEEN_API_CALLS
            wait_time = DELAY_BETWEEN_API_CALLS
        except ImportError:
            wait_time = 5  # Fallback: 5 seconds for Gemini Flash free tier
        
        print(f"⏳ [RATE-LIMIT] Waiting {wait_time} seconds before second prompt...")
        print("⏳ [RATE-LIMIT] Reason: Respecting API rate limits between first and second prompt")
        for remaining in range(wait_time, 0, -10):
            print(f"⏳ [RATE-LIMIT] Time remaining: {remaining} seconds...")
            await asyncio.sleep(min(10, remaining))
        
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
        print("🎼 [REVIEW_API-DEBUG] Will attempt to fetch from tblprogress_v1 with this ID")

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
    """Process review verdicts: move good songs to final_review, delete bad ones using centralized deletion."""
    kept_count = 0
    deleted_count = 0

    for result in review_results:
        file_path = result["file_path"]
        verdict = result["verdict"]
        song_id = result.get("song_id")  # Get song_id for potential remote deletion

        try:
            if verdict == "continue":
                # Move to final_review directory - THIS IS THE VERIFIED FINAL DESTINATION
                filename = os.path.basename(file_path)
                final_path = os.path.join(final_dir, filename)

                if os.path.exists(file_path):
                    shutil.move(file_path, final_path)
                    kept_count += 1
                    print(f"🎼 [VERDICT] ✅ APPROVED SONG moved to final destination: {final_path}")
                    print("🎼 [VERDICT] ✅ CONFIRMED: Song is now in backend/songs/final_review directory")
                else:
                    print(f"🎼 [VERDICT] ⚠️ File not found for moving: {file_path}")

            elif verdict == "re-roll":
                print("\n🗑️ [DELETE-FLOW] ===========")
                print("🗑️ [DELETE-FLOW] Starting deletion process for RE-ROLL verdict")
                print(f"🗑️ [DELETE-FLOW] File: {file_path}")
                print(f"🗑️ [DELETE-FLOW] Song ID: {song_id if song_id else 'MISSING'}")
                print(f"🗑️ [DELETE-FLOW] File exists: {os.path.exists(file_path)}")

                # Use centralized deletion utility with mandatory remote deletion
                if not song_id:
                    # Per the migration plan, song_id is REQUIRED for re-roll deletions
                    error_msg = f"Missing song_id for re-roll deletion of {file_path}"
                    print(f"🗑️ [DELETE-FLOW] ❌ {error_msg}")
                    print("🗑️ [DELETE-FLOW] Attempting fallback: local deletion only")
                    # Fallback: delete locally and continue processing other songs
                    try:
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            print(f"🗑️ [DELETE-FLOW] File size before deletion: {file_size:,} bytes")
                            os.remove(file_path)
                            deleted_count += 1
                            print("🗑️ [DELETE-FLOW] ✅ Successfully deleted local file (no song_id available)")
                            print(f"🗑️ [DELETE-FLOW] Deleted file was: {file_path}")
                        else:
                            print(f"🗑️ [DELETE-FLOW] ⚠️ File already doesn't exist: {file_path}")
                    except Exception as e:
                        print(f"🗑️ [DELETE-FLOW] ❌ Failed local delete without song_id: {e}")
                        print(f"🗑️ [DELETE-FLOW] Error type: {type(e).__name__}")
                    print("🗑️ [DELETE-FLOW] ===========")
                    continue

                # Perform mandatory remote+local deletion when song_id exists
                print("🗑️ [DELETE-FLOW] Starting centralized deletion (local + remote)")
                print("🗑️ [DELETE-FLOW] Calling delete_song with:")
                print(f"🗑️ [DELETE-FLOW]   - song_id: {song_id}")
                print(f"🗑️ [DELETE-FLOW]   - file_path: {file_path}")
                print("🗑️ [DELETE-FLOW]   - delete_from_suno: True")

                delete_result = await delete_song(song_id=song_id, file_path=file_path, delete_from_suno=True)

                print("🗑️ [DELETE-FLOW] Delete result received:")
                print(f"🗑️ [DELETE-FLOW]   - Success: {delete_result.get('success')}")
                print(f"🗑️ [DELETE-FLOW]   - Local deleted: {delete_result.get('local_deleted')}")
                print(f"🗑️ [DELETE-FLOW]   - Suno deleted: {delete_result.get('suno_deleted')}")
                print(f"🗑️ [DELETE-FLOW]   - Errors: {delete_result.get('errors', delete_result.get('error', 'None'))}")

                # Consider deletion successful if either local or remote deletion succeeded
                if delete_result.get("local_deleted") or delete_result.get("suno_deleted") or delete_result.get("success"):
                    deleted_count += 1
                    print("🗑️ [DELETE-FLOW] ✅ Deletion SUCCESSFUL")
                    print(f"🗑️ [DELETE-FLOW] Deleted poor quality song - Local: {delete_result.get('local_deleted')}, Remote: {delete_result.get('suno_deleted')}")
                else:
                    print("🗑️ [DELETE-FLOW] ❌ Deletion FAILED")
                    print(f"🗑️ [DELETE-FLOW] Error details: {delete_result.get('errors', delete_result.get('error', 'unknown error'))} for {file_path}")

                print("🗑️ [DELETE-FLOW] ===========\n")

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
    Process verdicts for the final attempt with intelligent deletion and fail-safe.

    On the final attempt, we delete songs with critical errors (re-roll verdict) but
    track what was deleted. The fail-safe only activates if NO songs remain.

    Args:
        review_results (List[Dict]): Review results from AI
        final_dir (str): Final review directory path

    Returns:
        Dict[str, int]: Processing results
    """
    kept_count = 0
    deleted_count = 0
    preserved_count = 0
    critical_failures = 0

    print("🎼 [VERDICT-FINAL] Processing final attempt verdicts with intelligent deletion")

    for result in review_results:
        file_path = result["file_path"]
        verdict = result["verdict"]
        song_id = result.get("song_id")

        try:
            if verdict == "continue":
                # Move good songs to final_review as usual - VERIFIED FINAL DESTINATION
                filename = os.path.basename(file_path)
                final_path = os.path.join(final_dir, filename)

                if os.path.exists(file_path):
                    shutil.move(file_path, final_path)
                    kept_count += 1
                    print(f"🎼 [VERDICT-FINAL] ✅ APPROVED SONG moved to final destination: {final_path}")
                    print("🎼 [VERDICT-FINAL] ✅ CONFIRMED: Song is now in backend/songs/final_review directory")
                else:
                    print(f"🎼 [VERDICT-FINAL] ⚠️ File not found for moving: {file_path}")

            elif verdict == "re-roll":
                # STRATEGY 1: Delete re-roll songs even on final attempt
                # Check severity of the issue from review details
                review_details = result.get("review_details", {})
                second_response = review_details.get("second_response", "").lower()

                # Detect critical failures that should always be deleted
                is_critical = any([
                    "cut off" in second_response or "cuts off" in second_response,
                    "abrupt" in second_response,
                    "no audio" in second_response,
                    "unintelligible" in second_response,
                    "completely wrong" in second_response,
                    "harsh digital noise" in second_response
                ])

                if is_critical:
                    # Delete critical failures even on final attempt
                    print("\n🗑️ [DELETE-CRITICAL] ===========")
                    print("🗑️ [DELETE-CRITICAL] ❌ CRITICAL FAILURE detected")
                    print(f"🗑️ [DELETE-CRITICAL] File: {file_path}")
                    print(f"🗑️ [DELETE-CRITICAL] Song ID: {song_id if song_id else 'MISSING'}")
                    print("🗑️ [DELETE-CRITICAL] Failure keywords found in review")

                    if song_id:
                        # Use centralized deletion with mandatory remote deletion
                        print("🗑️ [DELETE-CRITICAL] Starting centralized deletion")
                        delete_result = await delete_song(song_id=song_id, file_path=file_path, delete_from_suno=True)

                        print("🗑️ [DELETE-CRITICAL] Delete result:")
                        print(f"🗑️ [DELETE-CRITICAL]   - Local: {delete_result.get('local_deleted')}")
                        print(f"🗑️ [DELETE-CRITICAL]   - Remote: {delete_result.get('suno_deleted')}")
                        print(f"🗑️ [DELETE-CRITICAL]   - Success: {delete_result.get('success')}")

                        if delete_result.get("local_deleted") or delete_result.get("suno_deleted") or delete_result.get("success"):
                            deleted_count += 1
                            critical_failures += 1
                            print("🗑️ [DELETE-CRITICAL] ✅ Successfully deleted critical failure")
                        else:
                            print(f"🗑️ [DELETE-CRITICAL] ❌ Delete failed: {delete_result.get('errors', delete_result.get('error', 'unknown error'))}")
                            preserved_count += 1  # Count as preserved if deletion failed
                        print("🗑️ [DELETE-CRITICAL] ===========\n")
                    else:
                        # No song_id, try local deletion only
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                deleted_count += 1
                                critical_failures += 1
                                print(f"🎼 [VERDICT-FINAL] Deleted critical failure locally: {file_path}")
                            except Exception as e:
                                print(f"🎼 [VERDICT-FINAL] Failed to delete locally: {e}")
                                preserved_count += 1
                        else:
                            print(f"🎼 [VERDICT-FINAL] File already gone: {file_path}")
                else:
                    # Non-critical re-roll on final attempt - still delete but note it
                    print(f"🎼 [VERDICT-FINAL] ⚠️ Non-critical re-roll: deleting {file_path}")

                    if song_id:
                        delete_result = await delete_song(song_id=song_id, file_path=file_path, delete_from_suno=True)
                        if delete_result.get("success"):
                            deleted_count += 1
                            print("🎼 [VERDICT-FINAL] Deleted non-critical re-roll song")
                        else:
                            preserved_count += 1
                            print(f"🎼 [VERDICT-FINAL] Failed to delete, preserving: {file_path}")
                    else:
                        # Try local deletion
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                deleted_count += 1
                                print("🎼 [VERDICT-FINAL] Deleted non-critical re-roll locally")
                            except Exception:
                                preserved_count += 1

            else:  # verdict == "error" or unknown
                # Keep file in temp directory for potential recovery
                preserved_count += 1
                print(f"🎼 [VERDICT-FINAL] ⚠️ Review error, preserving for potential recovery: {file_path}")

        except Exception as e:
            print(f"🎼 [VERDICT-FINAL] Error processing {file_path}: {e}")
            preserved_count += 1

    print(f"🎼 [VERDICT-FINAL] Final attempt results: {kept_count} kept, {deleted_count} deleted ({critical_failures} critical), {preserved_count} preserved")

    return {
        "kept_count": kept_count,
        "deleted_count": deleted_count,
        "preserved_count": preserved_count,
        "critical_failures": critical_failures
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
    print("🔍 [VERIFY] This is where AI-approved songs (verdict: 'continue') will be moved")
    print("🔍 [VERIFY] Note: Fail-safe songs go to backend/songs/fail_safe directory")

    return final_destination


async def handle_failsafe_songs(final_attempt_songs: List[Dict], final_dir: str = None) -> Dict[str, int]:
    """
    🛡️ FAIL-SAFE MECHANISM: Move final attempt songs to fail_safe directory.

    This function is called when all 3 attempts fail to produce AI-approved songs.
    It ensures that the work from the final attempt isn't lost by moving downloaded
    songs to a separate fail_safe directory for later review.

    Args:
        final_attempt_songs (List[Dict]): Songs downloaded in the final attempt
        final_dir (str, optional): Ignored, uses fail_safe directory instead

    Returns:
        Dict[str, int]: Results with moved_count and error_count
    """
    moved_count = 0
    error_count = 0

    # Use dedicated fail_safe directory instead of final_review
    failsafe_dir = "backend/songs/fail_safe"
    os.makedirs(failsafe_dir, exist_ok=True)

    print(f"🛡️ [FAIL-SAFE] Processing {len(final_attempt_songs)} songs from final attempt")
    print(f"🛡️ [FAIL-SAFE] Moving to dedicated fail-safe directory: {failsafe_dir}")

    for i, song in enumerate(final_attempt_songs, 1):
        file_path = song["file_path"]

        try:
            if os.path.exists(file_path):
                # Create fail-safe filename with clear labeling
                original_filename = os.path.basename(file_path)
                name_part, ext = os.path.splitext(original_filename)
                failsafe_filename = f"{name_part}_FAILSAFE{ext}"
                final_path = os.path.join(failsafe_dir, failsafe_filename)

                # Move the file to fail_safe directory
                shutil.move(file_path, final_path)
                moved_count += 1
                print(f"🛡️ [FAIL-SAFE] ✅ BACKUP SONG moved to fail-safe directory: {final_path}")
                print(f"🛡️ [FAIL-SAFE] ✅ CONFIRMED: Backup song {i}/{len(final_attempt_songs)} is now in {failsafe_dir}")
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

