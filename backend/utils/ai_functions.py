import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.bible_utils import split_chapter_into_sections
from utils.llm_chat_utils import llm_general_query, extract_json_from_markdown
from utils.llm_chat_backup import (
    aimlapi_general_query,
    extract_json_from_markdown as extract_json_from_markdown_backup,
)
from utils.assign_styles import get_style_by_chapter
from lib.supabase import supabase


def generate_verse_ranges(book_name: str, book_chapter: int) -> list[str]:
    print(f"[generate_verse_ranges()] Generating verse ranges for {book_name} chapter {book_chapter}")
    split_chapter = split_chapter_into_sections(book_name, str(book_chapter))

    print(f"[generate_verse_ranges()] Splitting {book_name} {book_chapter} into sections: {split_chapter}")
    prompt = f"Split {book_name} {book_chapter} in Christian NIV Bible into {split_chapter} sections of similar size which stand alone. Give the range of verses separated by commas. Provide the output as numbers in oneline, nothing extra like explanations. Do not iclude the thinking and thought process to save output tokens."
    verse_ranges_str = llm_general_query(prompt)

    if not verse_ranges_str:
        print("Primary LLM failed, trying backup LLM...")
        verse_ranges_str = aimlapi_general_query(prompt)

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
            "Error: Failed to get verse ranges from LLM. Skipping further processing."
        )
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

    # Generate song structure using LLM
    prompt = f"Make a song structure using the Book of {strBookName} chapter {intBookChapter}, strictly from verses {strVerseRange} in the Bible only. The song will have 4-6 naturally segmented either verses, choruses or bridges. Strictly do not overlap nor reuse the verses in each segment. Strictly the output should be in json format: {{'stanza label': 'bible verse range number only', 'stanza label': 'bible verse range number only'}}. Do not provide any explanation only the json output."

    song_structure_response = llm_general_query(prompt)
    primary_llm_failed = not song_structure_response

    if primary_llm_failed:
        print("Primary LLM failed, trying backup LLM...")
        song_structure_response = aimlapi_general_query(prompt)

    print(f"Song structure response: {song_structure_response}")

    # Parse the song structure
    try:
        if song_structure_response:
            # Extract JSON from markdown
            if primary_llm_failed:
                json_string = extract_json_from_markdown_backup(
                    song_structure_response
                )
            else:
                json_string = extract_json_from_markdown(song_structure_response)
            song_structure = (
                json.loads(json_string)
                if isinstance(json_string, str)
                else json_string
            )
        else:
            print("Error: Failed to get song structure from LLM")
            return {}
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON response from LLM: {song_structure_response}")
        return {}

    print(f"Parsed song structure: {song_structure}")

    # Analyze passage tone
    tone_prompt = f"Analyze the overall Bible passage tone for {strBookName} {intBookChapter}:{strVerseRange}. Strictly the output should be 0 or 1 only. 0 for negative and 1 for positive. Do not provide any explanation only the number."

    passage_tone_response = llm_general_query(tone_prompt)
    if not passage_tone_response:
        print("Primary LLM failed for tone analysis, trying backup LLM...")
        passage_tone_response = aimlapi_general_query(tone_prompt)

    print(f"Passage tone response: {passage_tone_response}")

    try:
        passage_tone = (
            int(passage_tone_response.strip()) if passage_tone_response else 1
        )
    except (ValueError, AttributeError):
        print(
            f"Error parsing tone response: {passage_tone_response}, defaulting to positive (1)"
        )
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
