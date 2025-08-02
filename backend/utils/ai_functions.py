import sys
import os
import json
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.bible_utils import split_chapter_into_sections
from utils.assign_styles import get_style_by_chapter
from lib.supabase import supabase
from multi_tool_agent.song_generation_agent import root_agent

# Configure logging for AI generations
# TODO: Add log rotation to prevent files from growing too large
# TOFIX: Implement different log levels (DEBUG, INFO, WARNING, ERROR)
# TODO: Consider structured logging with JSON format for easier parsing
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
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


def generate_verse_ranges(book_name: str, book_chapter: int) -> list[str]:
    print(
        f"[generate_verse_ranges()] Generating verse ranges for {book_name} chapter {book_chapter}"
    )
    ai_logger.info(f"Generating verse ranges for {book_name} chapter {book_chapter}")
    
    split_chapter = split_chapter_into_sections(book_name, str(book_chapter))

    print(
        f"[generate_verse_ranges()] Splitting {book_name} {book_chapter} into sections: {split_chapter}"
    )
    
    # Use the agent to generate verse ranges
    try:
        # Log the request
        request_prompt = f"Split {book_name} chapter {book_chapter} into {split_chapter} verse ranges"
        ai_logger.info(f"Agent request: {request_prompt}")
        
        # TODO: Add validation that root_agent is properly initialized
        # TOFIX: Add timeout handling for long-running requests
        # TODO: Implement retry logic if the agent fails
        # TOFIX: Fix agent method call - 'LlmAgent' object has no attribute 'run'
        # Need to check google-adk documentation for correct method (possibly 'query' or 'invoke')
        # The agent will use the generate_verse_ranges tool
        verse_ranges_str = root_agent.run(request_prompt)
        
        # Log the response
        ai_logger.info(f"Agent response: {verse_ranges_str}")
        
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
        print(f"Error using agent for verse ranges: {e}")
        ai_logger.error(f"Error using agent for verse ranges: {e}")
        return []


def get_verse_ranges(book_name: str, book_chapter: int) -> list[str]:
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
        return generate_verse_ranges(book_name, book_chapter)


def generate_song_structure(
    strBookName: str, intBookChapter: int, strVerseRange: str
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
        request_prompt = f"Create a song structure for {strBookName} chapter {intBookChapter}, verses {strVerseRange}"
        ai_logger.info(f"Generating song structure for {strBookName} {intBookChapter}:{strVerseRange}")
        ai_logger.info(f"Agent request: {request_prompt}")
        
        # TOFIX: Update to use correct agent method instead of 'run'
        song_structure_response = root_agent.run(request_prompt)
        
        # Log the response
        ai_logger.info(f"Song structure response: {song_structure_response}")
        
        print(f"Song structure response: {song_structure_response}")

        # Parse the song structure
        if song_structure_response:
            # Try to parse as JSON directly first
            try:
                song_structure = json.loads(song_structure_response)
            except json.JSONDecodeError:
                # If direct parsing fails, extract JSON from the response
                # Simple extraction: find content between first { and last }
                # TODO: Improve JSON extraction to handle nested objects and edge cases
                # TOFIX: Add validation to ensure extracted JSON has required fields
                start_idx = song_structure_response.find('{')
                end_idx = song_structure_response.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    json_string = song_structure_response[start_idx:end_idx + 1]
                    song_structure = json.loads(json_string)
                    ai_logger.info(f"Extracted JSON: {json_string}")
                else:
                    print(f"Error: Could not extract JSON from response: {song_structure_response}")
                    ai_logger.error(f"Could not extract JSON from response: {song_structure_response}")
                    return {}
        else:
            print("Error: Failed to get song structure from agent")
            ai_logger.error("Failed to get song structure from agent")
            return {}
    except Exception as e:
        print(f"Error using agent for song structure: {e}")
        ai_logger.error(f"Error using agent for song structure: {e}")
        return {}

    print(f"Parsed song structure: {song_structure}")

    # TODO: Add validation function to ensure song structure meets requirements
    # Example: validate_song_structure(song_structure)
    # Should check for minimum sections (verse, chorus), proper format, etc.

    # Analyze passage tone using the agent
    try:
        # Log the request
        request_prompt = f"Analyze the tone of {strBookName} chapter {intBookChapter}, verses {strVerseRange}"
        ai_logger.info(f"Analyzing tone for {strBookName} {intBookChapter}:{strVerseRange}")
        ai_logger.info(f"Agent request: {request_prompt}")
        
        # TOFIX: Update to use correct agent method instead of 'run'
        passage_tone_response = root_agent.run(request_prompt)
        
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
