"""
System: backend
Module: api.ai_generation
Purpose: Defines the API routes for AI-powered generation operations, including verse ranges and song structures.
"""

import ast
import json
import logging
import os
import traceback
from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from lib.supabase import supabase
from middleware.gemini import model_flash
from pydantic import BaseModel
from utils.assign_styles import get_style_by_chapter
from utils.bible_utils import split_chapter_into_sections

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


# Configure logging for AI generations
# TODO: Add log rotation to prevent files from growing too large
# TOFIX: Implement different log levels (DEBUG, INFO, WARNING, ERROR)
# TODO: Consider structured logging with JSON format for easier parsing
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Create a logger for AI generations
ai_logger = logging.getLogger('ai_generations')
ai_logger.setLevel(logging.INFO)

# Create file handler with timestamp in filename
log_filename = os.path.join(log_dir, f'ai_generations_{datetime.now().strftime("%Y%m%d")}.log')
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
ai_logger.addHandler(file_handler)

# TODO: Future Improvements
# 1. Centralize AI Prompts - Create backend/constants/song_prompts.py to store all prompts
#    This will provide a single source of truth and avoid duplication with song_generation_agent.py
# 2. Add Caching for AI Responses - Implement caching mechanism for verse ranges and song structures
#    since Bible content doesn't change. This will reduce API calls and costs.
# 3. Validate Song Structure JSON - Add validation function to ensure AI-generated structures
#    meet minimum requirements (e.g., must have verse and chorus sections)
# 4. Logging Improvements - Replace print statements with structured logging using Python's
#    logging module for better debugging and monitoring in production
# 5. Consider upgrading from deepseek/deepseek-r1-0528:free to a more capable model
#    for better Bible verse analysis and structure generation



async def _run_gemini(prompt: str) -> str:
    """Helper function to run the Gemini model."""
    try:
        response = await model_flash.generate_content_async(prompt)
        return response.text
    except Exception as e:
        ai_logger.error(f"Error running Gemini model: {e}")
        raise


async def generate_verse_ranges_handler(book_name: str, book_chapter: int) -> list[str]:
    print(
        f"[generate_verse_ranges_handler()] Generating verse ranges for {book_name} chapter {book_chapter}"
    )
    ai_logger.info(f"Generating verse ranges for {book_name} chapter {book_chapter}")
    
    split_chapter = split_chapter_into_sections(book_name, str(book_chapter))

    print(
        f"[generate_verse_ranges_handler()] Splitting {book_name} {book_chapter} into sections: {split_chapter}"
    )
    
    # Use the agent to generate verse ranges
    try:
        # Log the request
        request_prompt = (
            "You are a helpful agent. Split the given Bible chapter into the requested number of sections. "
            "Return ONLY the verse ranges separated by commas (e.g., '1-11, 12-22'). "
            "No explanations or extra text.\n\n"
            f"Task: Split {book_name} chapter {book_chapter} into {split_chapter} verse ranges."
        )
        ai_logger.info(f"Gemini request: {request_prompt}")
        
        verse_ranges_str = await _run_gemini(request_prompt)
        
        # Log the response
        ai_logger.info(f"Gemini response: {verse_ranges_str}")
        
        if verse_ranges_str:
            verse_ranges = verse_ranges_str.split(",")
            print(f"Verse ranges: {verse_ranges} with type {type(verse_ranges)}")

            # Insert verse ranges into database
            for verse_range in verse_ranges:
                supabase.table("song_structure_tbl").insert(
                    {
                        "book_name": book_name,
                        "chapter": book_chapter,
                        "verse_range": verse_range.strip(),
                    }
                ).execute()

            return [v.strip() for v in verse_ranges]
        else:
            print(
                "Error: Failed to get verse ranges from agent. Skipping further processing."
            )
            ai_logger.error(f"Failed to get verse ranges for {book_name} {book_chapter}")
            return []
    except Exception as e:
        print(f"Error using Gemini for verse ranges: {e}")
        ai_logger.error(f"Error using Gemini for verse ranges: {e}")
        return []


async def get_verse_ranges(book_name: str, book_chapter: int) -> list[str]:
    """
    Get verse ranges for a book and chapter. If they don't exist, generate them.
    """
    response = (
        supabase.table("song_structure_tbl")
        .select("verse_range")
        .eq("book_name", book_name)
        .eq("chapter", book_chapter)
        .execute()
    )

    if response.data and len(response.data) > 0:
        return [item["verse_range"] for item in response.data]
    else:
        return await generate_verse_ranges_handler(book_name, book_chapter)


async def generate_song_structure_handler(
    strBookName: str, intBookChapter: int, strVerseRange: str, structureId: Optional[str] = None
) -> dict:
    # First check if song structure already exists
    existing_data = (
        supabase.table("song_structure_tbl")
        .select("song_structure, tone, styles")
        .eq("book_name", strBookName)
        .eq("chapter", intBookChapter)
        .eq("verse_range", strVerseRange)
        .execute()
    )

    # If song structure already exists and is not None, return it
    if existing_data.data and existing_data.data[0]["song_structure"]:
        song_structure_str = existing_data.data[0]["song_structure"]
        try:
            return (
                json.loads(song_structure_str)
                if isinstance(song_structure_str, str)
                else song_structure_str
            )
        except json.JSONDecodeError:
            print(
                f"Warning: Invalid JSON in existing song structure for {strBookName} {intBookChapter}:{strVerseRange}"
            )
            # Continue to regenerate the structure

    # Generate new song structure
    song_structure = {}
    passage_tone = 0
    styles = []

    # Generate song structure using the agent
    try:
        # Log the request
        request_prompt = (
            "You are a helpful agent. When asked to create a song structure:\n"
            "- Create a song structure using the given Bible verses\n"
            "- Use 4-6 sections (or more if needed) based on the verse content\n"
            "- Include sections like: Verse, Chorus, Bridge, Outro, Pre-Chorus, Post-Chorus, etc.\n"
            "- Return ONLY valid JSON format like: {'verse1': '1-5', 'chorus': '6-8', 'verse2': '9-12'}\n"
            "- Return ONLY a JSON object with no additional text or formatting\n"
            "- Do not include any explanations, markdown, or code blocks\n"
            "- Ensure the JSON uses double quotes for keys and values\n"
            "- Do not overlap or reuse verses between sections\n\n"
            f"Task: Create a song structure for {strBookName} chapter {intBookChapter}, verses {strVerseRange}"
        )
        ai_logger.info(f"Generating song structure for {strBookName} {intBookChapter}:{strVerseRange}")
        ai_logger.info(f"Gemini request: {request_prompt}")
        
        song_structure_response = await _run_gemini(request_prompt)
        
        # Log the response
        ai_logger.info(f"Song structure response: {song_structure_response}")
        
        print(f"Song structure response: {song_structure_response}")

        # Parse the song structure
        if not song_structure_response:
            print("Error: Failed to get song structure from agent")
            ai_logger.error("Failed to get song structure from agent")
            return {}

        try:
            # First, try to parse as standard JSON
            song_structure = json.loads(song_structure_response)
        except json.JSONDecodeError:
            try:
                # If that fails, try parsing as Python literal
                song_structure = ast.literal_eval(song_structure_response)
            except (SyntaxError, ValueError):
                # If both fail, try to extract a substring that might be JSON
                start_idx = song_structure_response.find('{')
                end_idx = song_structure_response.rfind('}')
                if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                    json_string = song_structure_response[start_idx:end_idx+1]
                    try:
                        # First try parsing extracted substring as JSON
                        song_structure = json.loads(json_string)
                    except json.JSONDecodeError:
                        try:
                            # Then try parsing as Python literal
                            song_structure = ast.literal_eval(json_string)
                        except (SyntaxError, ValueError):
                            print(f"Error: Could not parse response as JSON or Python literal: {json_string}")
                            ai_logger.error(f"Could not parse response as JSON or Python literal: {json_string}")
                            return {}
                else:
                    print(f"Error: Could not extract dictionary from response: {song_structure_response}")
                    ai_logger.error(f"Could not extract dictionary from response: {song_structure_response}")
                    return {}

        # Validate that we got a dictionary
        if not isinstance(song_structure, dict):
            print(f"Error: Parsed song structure is not a dictionary: {type(song_structure)}")
            ai_logger.error(f"Parsed song structure is not a dictionary: {type(song_structure)}")
            return {}
    except Exception as e:
        print(f"Error using Gemini for song structure: {e}")
        ai_logger.error(f"Error using Gemini for song structure: {e}")
        return {}

    print(f"Parsed song structure: {song_structure}")

    # TODO: Add validation function to ensure song structure meets requirements
    # Example: validate_song_structure(song_structure)
    # Should check for minimum sections (verse, chorus), proper format, etc.

    # Analyze passage tone using the agent
    try:
        # Log the request
        request_prompt = (
            "You are a helpful agent. When asked to analyze tone:\n"
            "- Analyze the emotional tone of the given Bible passage\n"
            "- Return ONLY '0' for negative tone or '1' for positive tone\n"
            "- No explanations\n\n"
            f"Task: Analyze the tone of {strBookName} chapter {intBookChapter}, verses {strVerseRange}"
        )
        ai_logger.info(f"Analyzing tone for {strBookName} {intBookChapter}:{strVerseRange}")
        ai_logger.info(f"Gemini request: {request_prompt}")
        
        passage_tone_response = await _run_gemini(request_prompt)
        
        # Log the response
        ai_logger.info(f"Tone response: {passage_tone_response}")
        
        print(f"Passage tone response: {passage_tone_response}")

        # Parse tone response
        passage_tone = (
            int(passage_tone_response.strip()) if passage_tone_response and passage_tone_response.strip().isdigit() else 1
        )
    except (ValueError, AttributeError, Exception) as e:
        print(
            f"Error parsing tone response: {e}, defaulting to positive (1)"
        )
        ai_logger.error(f"Error parsing tone response: {e}")
        passage_tone = 1

    # Get styles based on chapter and tone
    styles = get_style_by_chapter(strBookName, intBookChapter, passage_tone)
    print(f"Style for {strBookName} {intBookChapter}: {styles}")

    # Update the database with the generated structure
    try:
        supabase.table("song_structure_tbl").update(
            {
                "song_structure": json.dumps(song_structure),
                "tone": passage_tone,
                "styles": styles,
            }
        ).eq("book_name", strBookName).eq("chapter", intBookChapter).eq(
            "verse_range", strVerseRange
        ).execute()

        print(
            f"Successfully updated song structure for {strBookName} {intBookChapter}:{strVerseRange}"
        )
    except Exception as e:
        print(f"Error updating database: {e}")

    return song_structure


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
        verse_ranges = await get_verse_ranges(book_name, book_chapter)
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
