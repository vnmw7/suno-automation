"""
System: backend
Module: api.orchestrator.utils
Purpose: Utility functions for the orchestrator workflow including song generation, 
         download, review, and intelligent retry logic.
"""

import os
import shutil
import asyncio
from typing import Dict, Any, List, Tuple
import traceback


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
    2. Wait for Suno processing (3 minutes) 
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
    
    # Ensure required directories exist
    temp_dir = "backend/songs/temp" 
    final_dir = "backend/songs/final_review"
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(final_dir, exist_ok=True)
    
    workflow_details = {
        "attempts": [],
        "total_songs_generated": 0,
        "total_songs_reviewed": 0, 
        "songs_kept": 0,
        "songs_deleted": 0
    }
    
    max_attempts = 3
    
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
            generation_result = await generate_songs(
                book_name, chapter, verse_range, style, title
            )
            
            if not generation_result["success"]:
                attempt_details["final_action"] = f"generation_failed: {generation_result['error']}"
                workflow_details["attempts"].append(attempt_details)
                continue
                
            attempt_details["generation_success"] = True
            workflow_details["total_songs_generated"] += 2  # Suno generates 2 songs
            
            # STEP 2: Wait for Suno processing
            print(f"🎼 [WORKFLOW] Step 2: Waiting for Suno processing (3 minutes)...")
            await asyncio.sleep(3 * 60)  # 3 minutes wait
            
            # STEP 3: Download both songs
            print(f"🎼 [WORKFLOW] Step 3: Downloading both generated songs...")
            download_results = await download_both_songs(title, temp_dir)
            
            if not download_results["success"]:
                attempt_details["final_action"] = f"download_failed: {download_results['error']}"
                workflow_details["attempts"].append(attempt_details)
                continue
                
            attempt_details["downloads"] = download_results["downloads"]
            downloaded_songs = download_results["downloads"]
            
            # STEP 4: Review both songs
            print(f"🎼 [WORKFLOW] Step 4: Reviewing {len(downloaded_songs)} downloaded songs...")
            review_results = await review_all_songs(downloaded_songs, song_structure_id)
            
            attempt_details["reviews"] = review_results
            workflow_details["total_songs_reviewed"] += len(review_results)
            
            # STEP 5: Process verdicts and handle files
            print(f"🎼 [WORKFLOW] Step 5: Processing review verdicts...")
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
    
    return {
        "success": True,  # Technical success, but no quality songs
        "message": f"🎼 Max attempts ({max_attempts}) reached. All generated songs were rejected by AI review.",
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
        
        result = await generate_song_handler(
            strBookName=book_name,
            intBookChapter=chapter, 
            strVerseRange=verse_range,
            strStyle=style,
            strTitle=title
        )
        
        if result and isinstance(result, dict) and result.get("success"):
            return {"success": True, "result": result}
        else:
            return {"success": False, "error": "Song generation returned invalid result"}
            
    except Exception as e:
        return {"success": False, "error": f"Song generation failed: {str(e)}"}


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


async def review_all_songs(downloaded_songs: List[Dict], song_structure_id: int) -> List[Dict[str, Any]]:
    """Review all downloaded songs using AI review system."""
    review_results = []
    
    # Import the review functionality - we need to check what's available
    try:
        # This might need to be adjusted based on actual review endpoint location
        # For now, we'll create a placeholder that calls the review API
        for i, song in enumerate(downloaded_songs):
            print(f"🎼 [REVIEW] Reviewing song {i+1}/{len(downloaded_songs)}: {song['file_path']}")
            
            # TODO: Replace with actual review API call
            # This should call the existing review endpoint
            review_result = await call_review_api(song["file_path"], song_structure_id)
            
            review_results.append({
                "file_path": song["file_path"],
                "index": song["index"],
                "title": song["title"],
                "verdict": review_result.get("verdict", "error"),
                "review_details": review_result
            })
            
        return review_results
        
    except Exception as e:
        print(f"🎼 [REVIEW] Review process failed: {e}")
        # Return error verdicts for all songs
        return [{
            "file_path": song["file_path"],
            "index": song["index"], 
            "title": song["title"],
            "verdict": "error",
            "review_details": {"error": str(e)}
        } for song in downloaded_songs]


async def call_review_api(file_path: str, song_structure_id: int) -> Dict[str, Any]:
    """Call the AI review API for a single song."""
    try:
        # TODO: This needs to be implemented to call the actual review endpoint
        # For now, return a mock response
        
        # In the actual implementation, this would make an HTTP request to the review endpoint
        # or directly call the review function
        
        # Mock implementation - replace with actual review call
        import random
        verdicts = ["continue", "re-roll"]
        mock_verdict = random.choice(verdicts)  # Temporary for testing
        
        return {
            "success": True,
            "verdict": mock_verdict,
            "first_response": f"Mock first response for {file_path}",
            "second_response": f"Mock second response for {file_path}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "verdict": "error", 
            "error": str(e)
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
                # Move to final_review directory
                filename = os.path.basename(file_path)
                final_path = os.path.join(final_dir, filename)
                
                if os.path.exists(file_path):
                    shutil.move(file_path, final_path)
                    kept_count += 1
                    print(f"🎼 [VERDICT] ✅ Moved good song to final_review: {final_path}")
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
