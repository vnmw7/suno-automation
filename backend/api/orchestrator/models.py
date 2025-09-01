"""
System: backend
Module: api.orchestrator.models
Purpose: Pydantic models for orchestrator workflow requests and responses.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class OrchestratorRequest(BaseModel):
    """Request model for the complete song generation and review workflow."""

    strBookName: str
    intBookChapter: int
    strVerseRange: str
    strStyle: str
    strTitle: str
    song_structure_id: Optional[int] = None


class OrchestratorResponse(BaseModel):
    """Response model for the orchestrator workflow operations."""

    success: bool
    message: str
    total_attempts: int
    final_songs_count: int
    good_songs: Optional[int] = None
    re_rolled_songs: Optional[int] = None
    error: Optional[str] = None
    workflow_details: Optional[Dict[str, Any]] = None
