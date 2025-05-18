import json

from lib.supabase import supabase
from utils.assign_styles import get_style_by_chapter
from utils.bible_utils import split_chapter_into_sections
from utils.converter import bookname_to_abrv
from utils.llm_chat_backup import aimlapi_general_query
from utils.llm_chat_utils import llm_general_query

book_name = "Genesis"
book_chapter = 1

split_chapter = split_chapter_into_sections(book_name, str(book_chapter))

prompt = f"Split {book_name} {book_chapter} in Christian NIV Bible into {split_chapter} sections of similar size which stand alone. Give the range of verses separated by commas. Provide the output as numbers in oneline, nothing extra like explanations. Do not iclude the thinking and thought process to save output tokens."

verse_ranges_str = llm_general_query(prompt)

if not verse_ranges_str:
    print("Primary LLM failed, trying backup LLM...")
    verse_ranges_str = aimlapi_general_query(prompt)

if verse_ranges_str:
    verse_ranges = verse_ranges_str.split(",")
    print(type(verse_ranges))
    print(f"Verse ranges: {verse_ranges}")

    if verse_ranges:  # Check if verse_ranges is not empty after split
        print(f"First verse range: {verse_ranges[0]}")
    else:
        print("Error: verse_ranges is empty after splitting.")
else:
    print("Error: Failed to get verse ranges from LLM. Skipping further processing.")
    verse_ranges = (
        []
    )  # Initialize as empty list to prevent further errors if other code expects it

prompt = f"Outline the Book of '{book_name}' Chapter '{book_chapter}' Verses '{verse_ranges[0]}' in the bible as a song structure of 4-6 naturally segmented verses, choruses or bridges. Don't write out the text. Never split one verse across stanzas. Never reuse verses. Give no introduction, conclusion or explanation, simply give scripture ranges separated by commas. For each, Label your stanzas inside brackets[] followed by a colon : and followed by only verse range like 5-14, each separated by comma in a single line. give nothing else. example: [Chorus]:18-28,[Bridge]:29-35"

prompt = "Make a song structure using the Book of Genesis chapter 1, strictly from verses 1-5 in the Bible only. The song will have 4-6 naturally segmented either verses, choruses or bridges. Strictly do not overlap nor reuse the verses in each segment. Strictly the output should be in json format: {'stanza label': 'bible verse range number only', 'stanza label': 'bible verse range number only'}. Do not provide any explanation only the json output."

song_structure = llm_general_query(prompt)
if not song_structure:
    print("Primary LLM failed, trying backup LLM...")
    song_structure = aimlapi_general_query(prompt)
print(f"Song structure: {song_structure}")

song_structure_dict = {}
try:
    if isinstance(song_structure, str):
        if song_structure.startswith("```") and song_structure.endswith("```"):
            song_structure_cleaned = song_structure[3:-3].strip()
            if song_structure_cleaned.startswith("json"):
                song_structure_cleaned = song_structure_cleaned[4:].strip()
        else:
            song_structure_cleaned = song_structure

        song_structure_json_string = song_structure_cleaned.replace("'", '"')
    else:
        song_structure_json_string = json.dumps(song_structure)

    parsed_song_structure = json.loads(song_structure_json_string)

    if not isinstance(parsed_song_structure, dict):
        print(
            f"Warning: Parsed song structure is not a dictionary. Received: {type(parsed_song_structure)}"
        )
    else:
        book_abrv = bookname_to_abrv(book_name)
        for label, verse_range_str in parsed_song_structure.items():
            verse_range_str = verse_range_str.strip()
            verses_in_label = {}

            start_verse_num_str, end_verse_num_str = "", ""
            if "-" in verse_range_str:
                start_verse_num_str, end_verse_num_str = verse_range_str.split("-")
            else:
                start_verse_num_str = end_verse_num_str = verse_range_str

            try:
                start_verse = int(start_verse_num_str)
                end_verse = int(end_verse_num_str)

                for verse_num in range(start_verse, end_verse + 1):
                    response = (
                        supabase.table("bible_verses_tbl")
                        .select("verse_text")
                        .eq("book", book_abrv)
                        .eq("chapter", book_chapter)
                        .eq("start_verse", verse_num)
                        .limit(1)
                        .execute()
                    )
                    verse_text = (
                        response.data[0]["verse_text"]
                        if response.data and len(response.data) > 0
                        else f"Verse {verse_num} not found"
                    )
                    verses_in_label[str(verse_num)] = verse_text
                song_structure_dict[label] = verses_in_label
            except ValueError:
                print(
                    f"Warning: Could not parse verse range '{verse_range_str}' for label '{label}'"
                )
                song_structure_dict[label] = {
                    "error": f"Invalid verse range: {verse_range_str}"
                }
except json.JSONDecodeError:
    print(f"Error: Could not decode song_structure JSON. Content: '{song_structure}'")
    song_structure_dict = {"error": "Failed to decode JSON song structure"}
except Exception as e:
    print(f"An unexpected error occurred while processing song structure: {e}")
    song_structure_dict = {"error": f"Unexpected error: {e}"}

print(f"Song structure dict: {song_structure_dict}")

prompt = f"Analyze the overall Bible passage is positive or negative: {song_structure_dict}. Strictly the output should be 0 or 1 only. 0 for negative and 1 for positive. Do not provide any explanation only the number."

passage_tone = llm_general_query(prompt)
if not passage_tone:
    print("Primary LLM failed, trying backup LLM...")
    passage_tone = aimlapi_general_query(prompt)
print(f"Passage tone: {passage_tone}")

style = get_style_by_chapter(book_name, book_chapter, int(passage_tone))
print(f"Style for {book_name} {book_chapter}: {style}")
