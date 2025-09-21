"""
System: backend
Module: api.orchestrator.routes  
Purpose: API routes for orchestrator workflow operations - the "mission control"
         for complex song generation, download, and review workflows.
"""

from fastapi import APIRouter
import os
import traceback
from pydantic import BaseModel
from typing import Optional
from .models import OrchestratorRequest, OrchestratorResponse
from .utils import execute_song_workflow, download_both_songs

router = APIRouter(prefix="/api/v1/orchestrator", tags=["orchestrator"])


class DownloadTestRequest(BaseModel):
    title: str
    temp_dir: str = "backend/songs/pending_review"


class DownloadTestResponse(BaseModel):
    success: bool
    message: str
    downloads: list = []
    error: Optional[str] = None


class ReviewTestRequest(BaseModel):
    audio_file_path: str
    pg1_id: int = 0


class ReviewTestResponse(BaseModel):
    success: bool
    message: str
    verdict: Optional[str] = None
    review_details: dict = {}
    error: Optional[str] = None


@router.post("/workflow", response_model=OrchestratorResponse)
async def song_workflow_orchestrator(request: OrchestratorRequest):
    """
    🎼 SONG WORKFLOW ORCHESTRATOR
    
    The "Mission Control" endpoint for complete song creation workflows.
    
    This orchestrates the entire song creation process:
    1. Generate 2 songs on Suno.com (single generation creates 2 variants)
    2. Wait for Suno processing (3 minutes)
    3. Download both songs using negative indexing (-1, -2) 
    4. AI review each song for quality
    5. Handle verdicts:
       - "continue": Move to backend/songs/final_review
       - "re-roll": Delete and retry generation
    6. Auto-retry up to 3 times if needed
    7. Fallback: Move final attempt songs to final_review regardless
    
    BENEFITS:
    - Single API call handles entire complex workflow
    - Intelligent retry logic for quality assurance
    - Automatic file management (move good, delete bad)
    - Comprehensive workflow tracking and statistics
    - Robust error handling at each step
    
    Args:
        request: OrchestratorRequest with book, chapter, verse range, style, and title
    
    Returns:
        OrchestratorResponse: Complete workflow results, statistics, and file locations
    """
    print(f"🎼 [ORCHESTRATOR] === WORKFLOW STARTED ===")
    print(f"🎼 [ORCHESTRATOR] Request: {request.strBookName} {request.intBookChapter}:{request.strVerseRange}")
    print(f"🎼 [ORCHESTRATOR] Style: {request.strStyle}")
    print(f"🎼 [ORCHESTRATOR] Title: {request.strTitle}")
    
    try:
        # Execute the core workflow
        workflow_result = await execute_song_workflow(
            book_name=request.strBookName,
            chapter=request.intBookChapter,
            verse_range=request.strVerseRange,
            style=request.strStyle,
            title=request.strTitle,
            song_structure_id=request.song_structure_id
        )
        
        print(f"🎼 [ORCHESTRATOR] === WORKFLOW COMPLETED ===")
        print(f"🎼 [ORCHESTRATOR] Success: {workflow_result['success']}")
        print(f"🎼 [ORCHESTRATOR] Final songs: {workflow_result.get('final_songs_count', 0)}")
        
        # Convert workflow result to API response
        return OrchestratorResponse(
            success=workflow_result["success"],
            message=workflow_result["message"],
            total_attempts=workflow_result["total_attempts"],
            final_songs_count=workflow_result["final_songs_count"],
            good_songs=workflow_result.get("good_songs"),
            re_rolled_songs=workflow_result.get("re_rolled_songs"), 
            error=workflow_result.get("error"),
            workflow_details=workflow_result.get("workflow_details")
        )
        
    except Exception as e:
        error_msg = f"🎼 Orchestrator failed with exception: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        
        return OrchestratorResponse(
            success=False,
            message="Orchestrator workflow failed due to unexpected error",
            total_attempts=0,
            final_songs_count=0,
            error=error_msg
        )


@router.get("/status")
async def orchestrator_status():
    """
    Get current orchestrator service status and statistics.
    
    Returns basic health check and service information.
    """
    return {
        "status": "operational",
        "service": "Song Workflow Orchestrator",
        "version": "1.0.0",
        "endpoints": [
            "/orchestrator/workflow - Main workflow execution",
            "/orchestrator/status - Service health check",
            "/orchestrator/debug/download - Test song download functionality",
            "/orchestrator/debug/review - Test song review functionality"
        ],
        "workflow_features": [
            "Automated song generation (2 songs per request)",
            "Intelligent download with negative indexing",
            "AI-powered quality review",
            "3-attempt retry logic with fallback",
            "Automatic file management and organization"
        ]
    }


@router.post("/debug/download", response_model=DownloadTestResponse)
async def debug_download_both_songs(request: DownloadTestRequest):
    """
    🔧 DEBUG ENDPOINT: Test download_both_songs function
    
    This endpoint allows direct testing of the download functionality without
    running the full orchestrator workflow.
    
    Args:
        request: DownloadTestRequest with song title and temp directory
    
    Returns:
        DownloadTestResponse: Download results and debug information
    """
    print(f"🔧 [DEBUG-DOWNLOAD] Starting download test for title: '{request.title}'")
    print(f"🔧 [DEBUG-DOWNLOAD] Using temp directory: {request.temp_dir}")
    
    try:
        # Call the download function directly
        result = await download_both_songs(request.title, request.temp_dir)
        
        print(f"🔧 [DEBUG-DOWNLOAD] Download result: {result}")
        
        # Build response, only including error if it exists
        response_data = {
            "success": result["success"],
            "message": result.get("message", "Download test completed"),
            "downloads": result.get("downloads", [])
        }
        
        # Only add error field if it exists and is not None
        if "error" in result and result["error"] is not None:
            response_data["error"] = result["error"]
        
        return DownloadTestResponse(**response_data)
        
    except Exception as e:
        error_msg = f"Debug download test failed: {str(e)}"
        print(f"🔧 [DEBUG-DOWNLOAD] {error_msg}")
        print(traceback.format_exc())
        
        return DownloadTestResponse(
            success=False,
            message="Download test failed with exception",
            downloads=[],
            error=error_msg
        )


@router.post("/debug/review", response_model=ReviewTestResponse)
async def debug_review_song(request: ReviewTestRequest):
    """
    🔧 DEBUG ENDPOINT: Test song review functionality
    
    This endpoint allows direct testing of the AI song review process without
    running the full orchestrator workflow. Useful for testing review logic,
    checking AI response parsing, and debugging review verdicts.
    
    Args:
        request: ReviewTestRequest with audio file path and song structure ID
    
    Returns:
        ReviewTestResponse: Review results and debug information
    """
    print(f"🔧 [DEBUG-REVIEW] Starting review test for file: '{request.audio_file_path}'")
    print(f"🔧 [DEBUG-REVIEW] Using pg1_id: {request.pg1_id}")

    try:
        # Import the review function from utils
        from .utils import call_review_api
        
        # Verify the file exists
        if not os.path.exists(request.audio_file_path):
            return ReviewTestResponse(
                success=False,
                message="Review test failed - file not found",
                error=f"Audio file not found: {request.audio_file_path}"
            )
        
        # Call the review API function directly
        review_result = await call_review_api(
            file_path=request.audio_file_path,
            pg1_id=request.pg1_id
        )
        
        print(f"🔧 [DEBUG-REVIEW] Review result: {review_result}")
        
        # Build response
        response_data = {
            "success": review_result.get("success", False),
            "message": "Review test completed",
            "verdict": review_result.get("verdict"),
            "review_details": {
                "first_response": review_result.get("first_response"),
                "second_response": review_result.get("second_response"),
                "audio_file": review_result.get("audio_file"),
                "raw_result": review_result
            }
        }
        
        # Only add error field if it exists and is not None
        if "error" in review_result and review_result["error"] is not None:
            response_data["error"] = review_result["error"]
        
        return ReviewTestResponse(**response_data)
        
    except Exception as e:
        error_msg = f"Debug review test failed: {str(e)}"
        print(f"🔧 [DEBUG-REVIEW] {error_msg}")
        print(traceback.format_exc())
        
        return ReviewTestResponse(
            success=False,
            message="Review test failed with exception",
            error=error_msg
        )
