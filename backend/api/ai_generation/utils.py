"""
System: backend
Module: api.ai_generation.utils
Purpose: Utility functions for AI-powered generation operations.
"""

import asyncio
from typing import Optional, Dict, List
from utils.ai_functions import generate_verse_ranges, generate_song_structure


async def generate_verse_ranges_handler(
    book_name: str,
    book_chapter: int
) -> List[str]:
    """
    Handle verse range generation for a given book and chapter.
    
    Args:
        book_name: The name of the book
        book_chapter: The chapter number
        
    Returns:
        List of verse ranges
    """
    try:
        # Run the synchronous function in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        verse_ranges = await loop.run_in_executor(
            None, 
            generate_verse_ranges, 
            book_name, 
            book_chapter
        )
        
        return verse_ranges
    except Exception as e:
        print(f"[generate_verse_ranges_handler] Error: {e}")
        raise


async def generate_song_structure_handler(
    strBookName: str,
    intBookChapter: int,
    strVerseRange: str,
    structureId: Optional[str] = None
) -> Dict:
    """
    Handle song structure generation for given book, chapter, and verse range.
    
    Args:
        strBookName: The name of the book
        intBookChapter: The chapter number
        strVerseRange: The verse range
        structureId: Optional structure ID for regeneration
        
    Returns:
        Dictionary containing the generated song structure
    """
    try:
        # Run the synchronous function in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            generate_song_structure,
            strBookName,
            intBookChapter,
            strVerseRange
        )
        
        # If structureId is provided, this is a regeneration
        if structureId:
            print(f"[generate_song_structure_handler] Regenerated structure for ID: {structureId}")
        
        return result
    except Exception as e:
        print(f"[generate_song_structure_handler] Error: {e}")
        raise
