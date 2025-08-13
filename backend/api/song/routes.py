"""
System: backend
Module: api.song
Purpose: Defines the API routes for song-related operations, including generation, download, and review.
"""

from fastapi import APIRouter, HTTPException, Body, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Union
import traceback
import os
from .utils import generate_song_handler, download_song_handler, delete_song_from_suno_handler

router = APIRouter(prefix="/song", tags=["song"])


class SongToDelete(BaseModel):
    file_path: str
    suno_index: int

class SongDeleteRequest(BaseModel):
    """Request model for deleting song files."""
    song_title: str
    songs: List[SongToDelete]


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


@router.post("/delete-files")
async def delete_song_files_endpoint(request: SongDeleteRequest):
    """
    Delete one or more song files from the server and from suno.com.

    Args:
        request: SongDeleteRequest containing a list of songs to delete.

    Returns:
        JSON response with success status and details of deleted/not found files.
    """
    deleted_files = []
    not_found_files = []
    errors = []

    allowed_directory = os.path.abspath("backend/songs/pending_review")

    for song in request.songs:
        # --- Delete local file ---
        try:
            absolute_file_path = os.path.abspath(song.file_path)
            if not absolute_file_path.startswith(allowed_directory):
                not_found_files.append(song.file_path)
                continue
            if os.path.exists(absolute_file_path):
                os.remove(absolute_file_path)
                deleted_files.append(song.file_path)
            else:
                not_found_files.append(song.file_path)
        except Exception as e:
            errors.append({"file_path": song.file_path, "error": str(e)})

        # --- Delete from Suno.com ---
        try:
            # Note: The suno_index from the frontend (e.g., 1, 2) is converted to a
            # negative index (-1, -2) to reliably delete the most recent songs from Suno,
            # which are located at the end of the list retrieved by the automation.
            suno_deletion_result = await delete_song_from_suno_handler(request.song_title, intIndex=-song.suno_index)
            if not suno_deletion_result["success"]:
                errors.append({"song_title": request.song_title, "suno_index": song.suno_index, "error": suno_deletion_result.get("error", "Unknown error deleting from Suno")})
        except Exception as e:
            errors.append({"song_title": request.song_title, "suno_index": song.suno_index, "error": str(e)})


    if errors:
        raise HTTPException(status_code=500, detail={"message": "Errors occurred during file deletion.", "errors": errors})

    return {
        "success": True,
        "message": "File deletion process completed.",
        "deleted_files": deleted_files,
        "not_found_files": not_found_files,
    }


@router.get("/list")
async def list_songs_endpoint(request: Request):
    """
    List song files from the server that have passed AI review and are ready for the frontend.
    """
    # Songs in this directory have been reviewed by the AI and are awaiting final manual review on the frontend.
    songs_dir = "backend/songs/reviewed"
    try:
        if not os.path.isdir(songs_dir):
            # It's possible the directory doesn't exist yet if no songs have been reviewed.
            # Return an empty list instead of an error.
            return {"success": True, "files": []}

        dirents = os.listdir(songs_dir)
        mp3_files = [f for f in dirents if f.endswith(".mp3")]

        book_name = request.query_params.get("bookName")
        chapter_param = request.query_params.get("chapter")
        range_param = request.query_params.get("range")

        if book_name and chapter_param and range_param:
            normalized_book_name = book_name.replace(" ", "_")
            expected_file_prefix = f"{normalized_book_name}_{chapter_param}-{range_param}".lower()
            mp3_files = [f for f in mp3_files if f.lower().startswith(expected_file_prefix)]

        return {"success": True, "files": mp3_files}
    except Exception as e:
        print(f"[list_songs_endpoint] Critical error occurred: {e}")
        print(traceback.format_exc())
        return {"success": False, "error": "Failed to list song files from server."}
