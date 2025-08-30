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

router = APIRouter(prefix="/song", tags=["song"])


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

    strTitle: str
    intIndex: int
    download_path: Optional[str] = "backend/songs/pending_review"


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
            f"[download_song_endpoint] Starting download for song: '{request.strTitle}' at index {request.intIndex}"
        )

        # Validate input parameters
        if not request.strTitle.strip():
            raise HTTPException(status_code=400, detail="Song title cannot be empty")

        if request.intIndex == 0:
            raise HTTPException(
                status_code=400,
                detail="Index cannot be 0. Use positive (1-based) or negative (-1 = last) indexing",
            )

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
    
    Expected format: {slug_title}_index_{intIndex}_{timestamp}.mp3
    Example: amazing-grace-verse-1-5_index_-1_20250830143022.mp3
    
    Args:
        filename: Song filename to parse
        
    Returns:
        Dict with parsed metadata or None if parsing fails
    """
    # Remove .mp3 extension if present
    if filename.endswith('.mp3'):
        filename = filename[:-4]
    
    # Match pattern: {title}_index_{index}_{timestamp}
    pattern = r'^(.+?)_index_([-]?\d+)_(\d{14})$'
    match = re.match(pattern, filename)
    
    if not match:
        return None
    
    title_slug, index_str, timestamp_str = match.groups()
    
    try:
        # Parse timestamp (YYYYMMDDHHMMSS)
        timestamp_dt = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
        created_date = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        created_date = timestamp_str
    
    return {
        'title_slug': title_slug,
        'index': int(index_str),
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
        review_dir = Path("backend/songs/final_review")
        
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
        
        # Sort files by index (negative indices first, then positive)
        matching_files.sort(key=lambda x: (x.parsed['index'] >= 0, abs(x.parsed['index'])))
        
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


