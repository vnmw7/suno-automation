"""
System: backend
Module: api.song
Purpose: Defines the API routes for song-related operations, including generation, download, and review.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import traceback
import os
import re
from datetime import datetime
from pathlib import Path
from .utils import generate_song_handler, download_song_handler
from utils.delete_song import SongDeleter

router = APIRouter(prefix="/api/v1/song", tags=["song"])


class SongReviewRequest(BaseModel):
    """Request model for reviewing a song."""

    audio_file_path: str
    song_structure_id: int


class SongRequest(BaseModel):
    """Request model for generating a song."""

    strBookName: str
    intBookChapter: int
    strVerseRange: str
    strStyle: str
    strTitle: str


class SongDownloadRequest(BaseModel):
    """Request model for downloading a song."""

    strTitle: Optional[str] = None
    intIndex: Optional[int] = None
    download_path: Optional[str] = "backend/songs/pending_review"
    song_id: Optional[str] = None


class SongDownloadResponse(BaseModel):
    """Response model for song download operations."""

    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None
    song_title: str
    song_index: int



class SongReviewResponse(BaseModel):
    """Response model for song review operations."""

    success: bool
    verdict: str  # "continue", "re-roll", or "error"
    first_response: Optional[str] = None
    second_response: Optional[str] = None
    error: Optional[str] = None
    audio_file: Optional[str] = None


class ManualReviewRequest(BaseModel):
    """Request model for manual song review."""
    
    bookName: str
    chapter: int
    verseRange: str


class SongFileInfo(BaseModel):
    """Information about a parsed song file."""
    
    filename: str
    parsed: Dict[str, Any]
    path: str


class ManualReviewResponse(BaseModel):
    """Response model for manual song review."""
    
    files: List[SongFileInfo]
    total_songs: int
    verse_reference: str


class DeleteSongRequest(BaseModel):
    """Request model for deleting a single song."""
    
    song_id: Optional[str] = None
    file_path: Optional[str] = None
    delete_from_suno: bool = False


class DeleteSongResponse(BaseModel):
    """Response model for single song deletion."""
    
    success: bool
    local_deleted: bool = False
    suno_deleted: bool = False
    errors: List[str] = []
    message: str


class BatchDeleteRequest(BaseModel):
    """Request model for deleting multiple songs."""
    
    song_ids: Optional[List[str]] = None
    file_paths: Optional[List[str]] = None
    delete_from_suno: bool = False


class BatchDeleteResponse(BaseModel):
    """Response model for batch song deletion."""
    
    success: bool
    total_processed: int
    deleted_count: int
    failed_count: int
    results: List[Dict[str, Any]]
    errors: List[str] = []


@router.post("/generate")
async def generate_song_endpoint(request: SongRequest):
    """
    Generate a song using Suno API.

    Args:
        request: SongRequest containing book name, chapter, verse range, style, and title

    Returns:
        JSON response with success status and result or error details
    """
    try:
        print(
            f"[generate_song_endpoint] Generating song for {request.strBookName} {request.intBookChapter}:{request.strVerseRange}"
        )

        result = await generate_song_handler(
            strBookName=request.strBookName,
            intBookChapter=request.intBookChapter,
            strVerseRange=request.strVerseRange,
            strStyle=request.strStyle,
            strTitle=request.strTitle,
        )

        return {
            "success": True,
            "message": "Song generated successfully.",
            "result": result,
        }
    except ValueError as ve:
        print(f"[generate_song_endpoint] ValueError: {ve}")
        return {
            "error": str(ve),
            "message": "Missing or invalid song structure data.",
            "success": False,
        }
    except Exception as e:
        print(f"[generate_song_endpoint] Critical error occurred: {e}")
        print(traceback.format_exc())
        return {
            "error": str(e),
            "message": "A critical error occurred during the song generation.",
            "success": False,
        }


@router.post("/download/", response_model=SongDownloadResponse)
async def download_song_endpoint(request: SongDownloadRequest):
    """
    Download a song from Suno by automating browser interactions.

    Args:
        request: SongDownloadRequest containing song title, index, and optional download path

    Returns:
        SongDownloadResponse with download results and file path or error details
    """
    try:
        print(
            f"[download_song_endpoint] Starting download for song: '{request.strTitle}' at index {request.intIndex}, song_id: {request.song_id}"
        )

        # Validate input parameters
        # If song_id is provided, title and index are optional
        if not request.song_id:
            # If no song_id, then title is required
            if not request.strTitle or not request.strTitle.strip():
                raise HTTPException(status_code=400, detail="Either song_id or strTitle must be provided")
            
            # If title is provided without song_id, index is required and cannot be 0
            if request.intIndex is None:
                raise HTTPException(status_code=400, detail="intIndex is required when downloading by title")
            
            if request.intIndex == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Index cannot be 0. Use positive (1-based) or negative (-1 = last) indexing",
                )
        else:
            # When song_id is provided, set default values if not provided
            if request.strTitle is None:
                request.strTitle = "Downloaded Song"  # Default title
            if request.intIndex is None:
                request.intIndex = 1  # Default to first song

        # Validate download path if provided
        if request.download_path:
            try:
                # Ensure the directory can be created/accessed
                os.makedirs(request.download_path, exist_ok=True)
            except Exception as path_error:
                raise HTTPException(
                    status_code=400, detail=f"Invalid download path: {str(path_error)}"
                )

        print(
            "[download_song_endpoint] Parameters validated, initiating download process..."
        )

        # Perform the download
        download_result = await download_song_handler(
            strTitle=request.strTitle,
            intIndex=request.intIndex,
            download_path=request.download_path,
            song_id=request.song_id,
        )

        if not download_result["success"]:
            print(
                f"[download_song_endpoint] Download failed: {download_result.get('error', 'Unknown error')}"
            )
            return SongDownloadResponse(
                success=False,
                error=download_result.get("error", "Download process failed"),
                song_title=request.strTitle,
                song_index=request.intIndex,
            )

        print(
            f"[download_song_endpoint] Download completed successfully: {download_result['file_path']}"
        )

        return SongDownloadResponse(
            success=True,
            file_path=download_result["file_path"],
            song_title=download_result["song_title"],
            song_index=download_result["song_index"],
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[download_song_endpoint] Critical error occurred: {e}")
        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during song download: {str(e)}",
        )


def slugify_text(text: str) -> str:
    """
    Convert text to slug format for filename matching.
    
    Args:
        text: Text to slugify
        
    Returns:
        Slugified text (lowercase, spaces to hyphens, special chars removed)
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces with hyphens
    text = text.replace(" ", "-")
    # Remove special characters (keep only alphanumeric and hyphens)
    text = re.sub(r'[^a-z0-9\-]', '', text)
    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)
    # Strip leading/trailing hyphens
    text = text.strip('-')
    return text


def parse_song_filename(filename: str) -> Optional[Dict]:
    """
    Parse a song filename to extract metadata.

    Expected format (per CLAUDE.md):
    - {slug_title}_{song_id}_{timestamp}.mp3 (UUID format)

    Example:
    - isaiah-1-1-10_0536dd17-8cfd-4bca-9fd7-831621daac10_20250913152839.mp3

    Args:
        filename: Song filename to parse

    Returns:
        Dict with parsed metadata or None if parsing fails
    """
    # Remove .mp3 extension if present
    if filename.endswith('.mp3'):
        filename = filename[:-4]

    # Pattern: {title}_{uuid}_{timestamp}
    # UUID pattern: 8-4-4-4-12 hexadecimal characters
    pattern = r'^(.+?)_([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})_(\d{14})$'
    match = re.match(pattern, filename)

    if not match:
        return None

    title_slug, song_id, timestamp_str = match.groups()

    try:
        # Parse timestamp (YYYYMMDDHHMMSS)
        timestamp_dt = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
        created_date = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        created_date = timestamp_str

    return {
        'title_slug': title_slug,
        'song_id': song_id,
        'timestamp': timestamp_str,
        'created_date': created_date
    }


@router.post("/manual-review", response_model=ManualReviewResponse)
async def manual_review_endpoint(request: ManualReviewRequest):
    """
    Fetch songs from the final_review directory for manual review.
    
    Args:
        request: ManualReviewRequest containing bookName, chapter, and verseRange
        
    Returns:
        ManualReviewResponse with list of matching songs
    """
    try:
        # Create the search slug from request parameters
        search_slug = slugify_text(f"{request.bookName}-{request.chapter}-{request.verseRange}")
        print(f"[manual_review_endpoint] Searching for songs with slug: {search_slug}")
        
        # Define the review directory path
        review_dir = Path("songs/final_review")
        
        # Ensure directory exists
        if not review_dir.exists():
            print(f"[manual_review_endpoint] Creating directory: {review_dir}")
            review_dir.mkdir(parents=True, exist_ok=True)
            return ManualReviewResponse(
                files=[],
                total_songs=0,
                verse_reference=f"{request.bookName} {request.chapter}:{request.verseRange}"
            )
        
        # Find all matching files
        matching_files = []
        
        # List all .mp3 files in the directory
        for file_path in review_dir.glob("*.mp3"):
            filename = file_path.name
            
            # Parse the filename
            parsed = parse_song_filename(filename)
            
            if parsed and parsed['title_slug'] == search_slug:
                # Create the accessible path for frontend - include subdirectory
                relative_path = f"final_review/{filename}"
                
                matching_files.append(SongFileInfo(
                    filename=filename,
                    parsed=parsed,
                    path=relative_path
                ))
                
                print(f"[manual_review_endpoint] Found matching file: {filename}")
        
        # Sort files by timestamp (most recent first)
        matching_files.sort(key=lambda x: x.parsed['timestamp'], reverse=True)
        
        print(f"[manual_review_endpoint] Found {len(matching_files)} matching songs")
        
        return ManualReviewResponse(
            files=matching_files,
            total_songs=len(matching_files),
            verse_reference=f"{request.bookName} {request.chapter}:{request.verseRange}"
        )
        
    except Exception as e:
        print(f"[manual_review_endpoint] Error occurred: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching songs for manual review: {str(e)}"
        )


@router.post("/delete", response_model=DeleteSongResponse)
async def delete_song_endpoint(request: DeleteSongRequest):
    """
    Delete a song locally and/or from Suno.com.
    
    Args:
        request: DeleteSongRequest containing optional song_id, file_path, and delete_from_suno flag
        
    Returns:
        DeleteSongResponse with deletion status and details
    """
    try:
        # Validate that at least one identifier is provided
        if not request.song_id and not request.file_path:
            raise HTTPException(
                status_code=400,
                detail="Either song_id or file_path must be provided"
            )
        
        print(f"[delete_song_endpoint] Starting deletion - Song ID: {request.song_id}, File: {request.file_path}, From Suno: {request.delete_from_suno}")
        
        # Initialize the SongDeleter
        deleter = SongDeleter()
        
        # Perform deletion
        result = await deleter.delete_song(
            song_id=request.song_id,
            file_path=request.file_path,
            delete_from_suno=request.delete_from_suno
        )
        
        # Prepare response message
        messages = []
        if result["local_deleted"]:
            messages.append("Local file deleted successfully")
        if result["suno_deleted"]:
            messages.append("Song deleted from Suno.com successfully")
        if not result["success"]:
            messages.append("Deletion failed")
        
        return DeleteSongResponse(
            success=result["success"],
            local_deleted=result["local_deleted"],
            suno_deleted=result["suno_deleted"],
            errors=result.get("errors", []),
            message=". ".join(messages) if messages else "No operations performed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[delete_song_endpoint] Error occurred: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during song deletion: {str(e)}"
        )


@router.post("/delete/batch", response_model=BatchDeleteResponse)
async def batch_delete_endpoint(request: BatchDeleteRequest):
    """
    Delete multiple songs in batch locally and/or from Suno.com.
    
    Args:
        request: BatchDeleteRequest containing optional song_ids, file_paths, and delete_from_suno flag
        
    Returns:
        BatchDeleteResponse with batch deletion results
    """
    try:
        # Validate that at least one list is provided
        if not request.song_ids and not request.file_paths:
            raise HTTPException(
                status_code=400,
                detail="Either song_ids or file_paths must be provided"
            )
        
        print(f"[batch_delete_endpoint] Starting batch deletion - Songs: {len(request.song_ids or [])}, Files: {len(request.file_paths or [])}")
        
        # Initialize the SongDeleter
        deleter = SongDeleter()
        
        results = []
        deleted_count = 0
        failed_count = 0
        all_errors = []
        
        # Process file deletions
        if request.file_paths:
            for file_path in request.file_paths:
                try:
                    result = await deleter.delete_song(
                        file_path=file_path,
                        delete_from_suno=False  # Only delete locally for batch file operations
                    )
                    
                    if result["success"]:
                        deleted_count += 1
                    else:
                        failed_count += 1
                        all_errors.extend(result.get("errors", []))
                    
                    results.append({
                        "file_path": file_path,
                        "success": result["success"],
                        "errors": result.get("errors", [])
                    })
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Failed to delete {file_path}: {str(e)}"
                    all_errors.append(error_msg)
                    results.append({
                        "file_path": file_path,
                        "success": False,
                        "errors": [error_msg]
                    })
        
        # Process Suno deletions
        if request.song_ids and request.delete_from_suno:
            for song_id in request.song_ids:
                try:
                    result = await deleter.delete_song(
                        song_id=song_id,
                        delete_from_suno=True
                    )
                    
                    if result["success"]:
                        deleted_count += 1
                    else:
                        failed_count += 1
                        all_errors.extend(result.get("errors", []))
                    
                    results.append({
                        "song_id": song_id,
                        "success": result["success"],
                        "errors": result.get("errors", [])
                    })
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Failed to delete song {song_id}: {str(e)}"
                    all_errors.append(error_msg)
                    results.append({
                        "song_id": song_id,
                        "success": False,
                        "errors": [error_msg]
                    })
        
        total_processed = deleted_count + failed_count
        
        return BatchDeleteResponse(
            success=failed_count == 0,
            total_processed=total_processed,
            deleted_count=deleted_count,
            failed_count=failed_count,
            results=results,
            errors=all_errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[batch_delete_endpoint] Error occurred: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during batch deletion: {str(e)}"
        )


@router.delete("/delete/{song_id}")
async def delete_song_by_id(song_id: str, delete_from_suno: bool = False):
    """
    Delete a song by its Suno ID using REST conventions.
    
    Args:
        song_id: The Suno song ID
        delete_from_suno: Query parameter to also delete from Suno.com
        
    Returns:
        DeleteSongResponse with deletion status
    """
    try:
        print(f"[delete_song_by_id] Deleting song {song_id}, from Suno: {delete_from_suno}")
        
        # Initialize the SongDeleter
        deleter = SongDeleter()
        
        # Perform deletion
        result = await deleter.delete_song(
            song_id=song_id,
            delete_from_suno=delete_from_suno
        )
        
        # Prepare response message
        messages = []
        if result["suno_deleted"]:
            messages.append(f"Song {song_id} deleted from Suno.com successfully")
        if not result["success"]:
            messages.append(f"Failed to delete song {song_id}")
        
        return DeleteSongResponse(
            success=result["success"],
            local_deleted=result["local_deleted"],
            suno_deleted=result["suno_deleted"],
            errors=result.get("errors", []),
            message=". ".join(messages) if messages else "Operation completed"
        )
        
    except Exception as e:
        print(f"[delete_song_by_id] Error occurred: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during song deletion: {str(e)}"
        )


@router.get("/find-songs")
async def find_songs_endpoint(directory: str = "backend/songs", pattern: str = "*.mp3"):
    """
    Find all song files in a directory matching a pattern.
    
    Args:
        directory: Directory to search (default: backend/songs)
        pattern: File pattern to match (default: *.mp3)
        
    Returns:
        List of file paths found
    """
    try:
        print(f"[find_songs_endpoint] Searching for {pattern} in {directory}")
        
        # Initialize the SongDeleter to use its find method
        deleter = SongDeleter()
        
        # Find songs
        songs = deleter.find_songs_in_directory(directory, pattern)
        
        return {
            "success": True,
            "directory": directory,
            "pattern": pattern,
            "count": len(songs),
            "files": songs
        }
        
    except Exception as e:
        print(f"[find_songs_endpoint] Error occurred: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error finding songs: {str(e)}"
        )
