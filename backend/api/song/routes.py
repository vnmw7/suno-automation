from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import traceback
import os
from .utils import review_song_with_ai, generate_song_handler

router = APIRouter(prefix="/song", tags=["song"])


class SongReviewRequest(BaseModel):
    audio_file_path: str
    song_structure: Dict[str, Any]
    title: Optional[str] = None


class SongRequest(BaseModel):
    strBookName: str
    intBookChapter: int
    strVerseRange: str
    strStyle: str
    strTitle: str


class SongReviewResponse(BaseModel):
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


@router.post("/review/", response_model=SongReviewResponse)
async def review_song_endpoint(request: SongReviewRequest):
    """
    Review a song using AI to check for quality issues and lyric accuracy.

    Args:
        request: SongReviewRequest containing audio file path and song structure

    Returns:
        SongReviewResponse with review results and verdict
    """
    try:
        print(
            f"[review_song_endpoint] Starting review for audio file: {request.audio_file_path}"
        )

        # Validate audio file path
        if not request.audio_file_path:
            raise HTTPException(status_code=400, detail="Audio file path is required")

        # Validate song structure
        if not request.song_structure:
            raise HTTPException(status_code=400, detail="Song structure is required")

        # Check if audio file exists
        if not os.path.exists(request.audio_file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found at path: {request.audio_file_path}",
            )

        print(
            "[review_song_endpoint] Audio file validated, starting AI review process..."
        )

        # Perform the AI review
        review_result = await review_song_with_ai(
            audio_file_path=request.audio_file_path,
            song_structure=request.song_structure,
        )

        if not review_result["success"]:
            print(
                f"[review_song_endpoint] Review failed: {review_result.get('error', 'Unknown error')}"
            )
            return SongReviewResponse(
                success=False,
                verdict="error",
                error=review_result.get("error", "Review process failed"),
                audio_file=request.audio_file_path,
            )

        print(
            f"[review_song_endpoint] Review completed successfully with verdict: {review_result['verdict']}"
        )

        return SongReviewResponse(
            success=True,
            verdict=review_result["verdict"],
            first_response=review_result.get("first_response"),
            second_response=review_result.get("second_response"),
            audio_file=review_result.get("audio_file"),
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[review_song_endpoint] Critical error occurred: {e}")
        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during song review: {str(e)}",
        )


@router.get("/review/health")
async def review_health_check():
    """
    Health check endpoint for the song review service.
    """
    return {
        "status": "healthy",
        "service": "song_review",
        "message": "Song review service is operational",
    }
