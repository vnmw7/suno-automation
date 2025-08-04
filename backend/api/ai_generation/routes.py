"""
System: backend
Module: api.ai_generation
Purpose: Defines the API routes for AI-powered generation operations, including verse ranges and song structures.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import traceback
from .utils import generate_verse_ranges_handler, generate_song_structure_handler

router = APIRouter(prefix="/ai-generation", tags=["ai-generation"])


class VerseRangeRequest(BaseModel):
    """Request model for generating verse ranges."""
    book_name: str
    book_chapter: int


class SongStructureRequest(BaseModel):
    """Request model for generating a song structure."""
    strBookName: str
    intBookChapter: int
    strVerseRange: str
    structureId: Optional[str] = None  # For regeneration


class VerseRangeResponse(BaseModel):
    """Response model for verse range generation."""
    success: bool
    message: str
    verse_ranges: Optional[list[str]] = None
    error: Optional[str] = None


class SongStructureResponse(BaseModel):
    """Response model for song structure generation."""
    success: bool
    message: str
    result: Optional[dict] = None
    error: Optional[str] = None


# TODO: Ensure all endpoints return consistent error structures
# All endpoints should follow the pattern: success: bool, message: str, error?: str
# This helps frontend handle errors consistently
@router.post("/verse-ranges", response_model=VerseRangeResponse)
async def generate_verse_ranges_endpoint(request: VerseRangeRequest):
    """
    Generate verse ranges for a given book and chapter.

    Args:
        request: VerseRangeRequest containing book name and chapter number

    Returns:
        VerseRangeResponse with generated verse ranges or error details
    """
    try:
        print(
            f"[generate_verse_ranges_endpoint] Generating verse ranges for {request.book_name} chapter {request.book_chapter}"
        )

        verse_ranges = await generate_verse_ranges_handler(
            book_name=request.book_name,
            book_chapter=request.book_chapter
        )

        return VerseRangeResponse(
            success=True,
            message="Verse ranges generated successfully.",
            verse_ranges=verse_ranges
        )
    except Exception as e:
        print(f"[generate_verse_ranges_endpoint] Critical error occurred: {e}")
        print(traceback.format_exc())
        return VerseRangeResponse(
            success=False,
            message="A critical error occurred during the verse ranges generation.",
            error=str(e)
        )


@router.get("/verse-ranges", response_model=VerseRangeResponse)
async def get_verse_ranges_endpoint(book_name: str, book_chapter: int):
    """
    Retrieve existing verse ranges for a given book and chapter.

    Args:
        book_name: The name of the book
        book_chapter: The chapter number

    Returns:
        VerseRangeResponse with retrieved verse ranges or error details
    """
    try:
        from utils.ai_functions import get_verse_ranges
        
        verse_ranges = get_verse_ranges(book_name, book_chapter)
        return VerseRangeResponse(
            success=True,
            message="Verse ranges retrieved successfully.",
            verse_ranges=verse_ranges
        )
    except Exception as e:
        print(f"[get_verse_ranges_endpoint] Error occurred: {e}")
        return VerseRangeResponse(
            success=False,
            message="Failed to retrieve verse ranges.",
            error=str(e)
        )


@router.post("/song-structure", response_model=SongStructureResponse)
async def generate_song_structure_endpoint(request: SongStructureRequest):
    """
    Generate a song structure based on book, chapter, and verse range.

    Args:
        request: SongStructureRequest containing book details and optional structure ID for regeneration

    Returns:
        SongStructureResponse with generated structure or error details
    """
    try:
        print(
            f"[generate_song_structure_endpoint] Generating song structure for {request.strBookName} "
            f"chapter {request.intBookChapter}, verses {request.strVerseRange}"
        )

        result = await generate_song_structure_handler(
            strBookName=request.strBookName,
            intBookChapter=request.intBookChapter,
            strVerseRange=request.strVerseRange,
            structureId=request.structureId
        )

        return SongStructureResponse(
            success=True,
            message="Song structure generated successfully.",
            result=result
        )
    except Exception as e:
        print(f"[generate_song_structure_endpoint] Critical error occurred: {e}")
        print(traceback.format_exc())
        return SongStructureResponse(
            success=False,
            message="A critical error occurred during the song structure generation.",
            error=str(e)
        )

# TODO: Consider creating a shared types file or code generation tool
# to ensure type consistency between frontend TypeScript interfaces
# and backend Pydantic models
