import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.bible_utils import split_chapter_into_sections
from utils.llm_chat_utils import llm_general_query
from utils.llm_chat_backup import aimlapi_general_query
from lib.supabase import supabase


def generate_verse_ranges(book_name: str, book_chapter: int) -> list[str]:
    split_chapter = split_chapter_into_sections(book_name, str(book_chapter))
    prompt = f"Split {book_name} {book_chapter} in Christian NIV Bible into {split_chapter} sections of similar size which stand alone. Give the range of verses separated by commas. Provide the output as numbers in oneline, nothing extra like explanations. Do not iclude the thinking and thought process to save output tokens."
    verse_ranges_str = llm_general_query(prompt)

    if not verse_ranges_str:
        print("Primary LLM failed, trying backup LLM...")
        verse_ranges_str = aimlapi_general_query(prompt)

    if verse_ranges_str:
        verse_ranges = verse_ranges_str.split(",")
        print(f"Verse ranges: {verse_ranges} with type {type(verse_ranges)}")

    else:
        print(
            "Error: Failed to get verse ranges from LLM. Skipping further processing."
        )
        verse_ranges = []

    for verse_range in verse_ranges:
        supabase.table("song_structure_tbl").insert(
            {
                "book_name": book_name,
                "chapter": book_chapter,
                "verse_range": verse_range,
            }
        ).execute()
