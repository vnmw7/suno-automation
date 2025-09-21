"""
System: backend
Module: api.ai_review
Purpose: Defines API routes for AI song review operations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import traceback
import os
from utils.ai_review import review_song_with_ai

router = APIRouter(prefix="/api/v1/ai_review", tags=["ai_review"])

class SongReviewRequest(BaseModel):
    """Request model for reviewing a song."""
    audio_file_path: str
    pg1_id: int

class SongReviewResponse(BaseModel):
    """Response model for song review operations."""
    success: bool
    verdict: str  # "continue", "re-roll", or "error"
    first_response: Optional[str] = None
    second_response: Optional[str] = None
    error: Optional[str] = None
    audio_file: Optional[str] = None
    deletion_message: Optional[str] = None
    move_message: Optional[str] = None

@router.post("/review/", response_model=SongReviewResponse)
async def review_song_endpoint(request: SongReviewRequest):
    """
    Review a song using AI to check for quality issues and lyric accuracy

    Args:
        request: SongReviewRequest containing audio file path and pg1_id

    Returns:
        SongReviewResponse with review results and verdict
    """
    try:
        print(f"[AI Review] Starting review for: {request.audio_file_path}")

        # Validate input parameters
        if not request.audio_file_path:
            raise HTTPException(status_code=400, detail="Audio file path is required")
        if not request.pg1_id:
            raise HTTPException(status_code=400, detail="pg1_id is required")
        if not os.path.exists(request.audio_file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found: {request.audio_file_path}"
            )

        print("[AI Review] Parameters validated, starting review process...")
        
        # Perform AI review using centralized utils module from backend.utils.ai_review
        review_result = await review_song_with_ai(
            audio_file_path=request.audio_file_path,
            pg1_id=request.pg1_id
        )

        if not review_result["success"]:
            print(f"[AI Review] Review failed: {review_result.get('error', 'Unknown error')}")
            return SongReviewResponse(
                success=False,
                verdict="error",
                error=review_result.get("error"),
                audio_file=request.audio_file_path
            )

        print(f"[AI Review] Review completed. Verdict: {review_result['verdict']}")
        return SongReviewResponse(
            success=True,
            verdict=review_result["verdict"],
            first_response=review_result.get("first_response"),
            second_response=review_result.get("second_response"),
            audio_file=review_result.get("audio_file"),
            deletion_message=review_result.get("deletion_message"),
            move_message=review_result.get("move_message")
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[AI Review] Critical error: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for AI review service"""
    return {
        "status": "healthy",
        "service": "ai_review",
        "message": "AI review service is operational"
    }
