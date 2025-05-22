from browserforge.fingerprints import Screen
from camoufox.sync_api import Camoufox
import json
import re

from lib.supabase import supabase
from utils.assign_styles import get_style_by_chapter
from utils.bible_utils import split_chapter_into_sections
from utils.llm_chat_backup import aimlapi_general_query
from utils.llm_chat_utils import llm_general_query
from utils.converter import bookname_to_abrv, song_structure_to_lyrics_structure

book_name = "Genesis"
book_chapter = 1

response = (
    supabase.table("song_structure_tbl")
    .select("verse_range")
    .eq("book_name", book_name)
    .eq("chapter", book_chapter)
    .execute()
)

verse_ranges = []

if response.data is not None and len(response.data) == 0:
    print("No data found in Supabase, proceeding to split chapter.")
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

        if verse_ranges:
            print(f"First verse range: {verse_ranges[0]}")
        else:
            print("Error: verse_ranges is empty after splitting.")
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
else:
    print("Data found in Supabase, no need to split chapter.")
    for item in response.data:
        verse_ranges.append(item["verse_range"])

print(f"Verse ranges from Supabase: {verse_ranges}")

response = (
    supabase.table("song_structure_tbl")
    .select("verse_range")
    .eq("book_name", book_name)
    .eq("chapter", book_chapter)
    .is_("song_structure", None)
    .execute()
)

print(f"Response from Supabase: {response}")

if response.data is not None and len(response.data) > 0:
    for verse_range in verse_ranges:
        song_structure = {}
        passage_tone = 0
        styles = []

        prompt = f"Outline the Book of '{book_name}' Chapter '{book_chapter}' Verses '{verse_range}' in the bible as a song structure of 4-6 naturally segmented verses, choruses or bridges. Don't write out the text. Never split one verse across stanzas. Never reuse verses. Give no introduction, conclusion or explanation, simply give scripture ranges separated by commas. For each, Label your stanzas inside brackets[] followed by a colon : and followed by only verse range like 5-14, each separated by comma in a single line. give nothing else. example: [Chorus]:18-28,[Bridge]:29-35"

        prompt = "Make a song structure using the Book of Genesis chapter 1, strictly from verses 1-5 in the Bible only. The song will have 4-6 naturally segmented either verses, choruses or bridges. Strictly do not overlap nor reuse the verses in each segment. Strictly the output should be in json format: {'stanza label': 'bible verse range number only', 'stanza label': 'bible verse range number only'}. Do not provide any explanation only the json output."

        song_structure = llm_general_query(prompt)
        if not song_structure:
            print("Primary LLM failed, trying backup LLM...")
            song_structure = aimlapi_general_query(prompt)
        print(f"Song structure: {song_structure}")

        song_structure_dict = song_structure

        print(f"Song structure dict: {song_structure_dict}")

        prompt = f"Analyze the overall Bible passage is positive or negative: {song_structure_dict}. Strictly the output should be 0 or 1 only. 0 for negative and 1 for positive. Do not provide any explanation only the number."

        passage_tone = llm_general_query(prompt)
        if not passage_tone:
            print("Primary LLM failed, trying backup LLM...")
            passage_tone = aimlapi_general_query(prompt)
        print(f"Passage tone: {passage_tone}")

        styles = get_style_by_chapter(book_name, book_chapter, int(passage_tone))
        print(f"Style for {book_name} {book_chapter}: {styles}")

        supabase.table("song_structure_tbl").update(
            {
                "song_structure": str(song_structure_dict),
                "tone": int(passage_tone),
                "styles": styles,
            }
        ).eq("book_name", book_name).eq("chapter", book_chapter).eq(
            "verse_range", verse_range
        ).execute()

song_structure_dict = (
    supabase.table("song_structure_tbl")
    .select("song_structure")
    .eq("book_name", book_name)
    .eq("chapter", book_chapter)
    .execute()
)

song_structure_json_string = song_structure_dict.data[0]["song_structure"]
parsed_song_structure = json.loads(song_structure_json_string)

song_structure_verses = song_structure_to_lyrics_structure(
    parsed_song_structure, book_name, book_chapter
)
print(f"Converted song structure verses: {song_structure_verses}")

lyrics_parts = []
for section_title, verses_dict in song_structure_verses.items():
    lyrics_parts.append(f"[{section_title}]:")
    for verse_num, verse_text in verses_dict.items():
        processed_text = verse_text.strip()
        processed_text = re.sub(r"\s*([.;])\s*", r"\1\n\n", processed_text)
        processed_text = re.sub(r"^\s+(?=\S)", "", processed_text, flags=re.MULTILINE)
        lyrics_parts.append(processed_text)

intermediate_lyrics = "\n".join(lyrics_parts)
lyrics = re.sub(r"\n{3,}", "\n", intermediate_lyrics)
lyrics = re.sub(r"\n", "\n\n", lyrics)
# Remove the new line after ":" in section titles
lyrics = re.sub(r"(\[.*?\]:)\n+", r"\1\n", lyrics)

print(lyrics)


os_list = ["windows", "macos", "linux"]
font_list = ["Arial", "Helvetica", "Times New Roman"]
constrains = Screen(max_width=1920, max_height=1080)


with Camoufox(
    os=os_list,
    fonts=font_list,
    screen=constrains,
    humanize=True,
    main_world_eval=True,
    geoip=True,
) as browser:
    page = browser.new_page(locale="en-US")
    page.goto("https://suno.com")
    page.wait_for_timeout(2000)
    page.wait_for_load_state("load")
    page.click('button:has(span:has-text("Sign in"))')
    page.wait_for_timeout(2000)
    page.click('button:has(img[alt="Sign in with Google"])')
    page.wait_for_timeout(2000)
    page.type('input[type="email"]', "pbNJ1sznC2Gr@gmail.com")
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)
    page.wait_for_load_state("load")
    page.wait_for_timeout(2000)
    page.type('input[type="password"]', "&!8G26tlbsgO")
    page.keyboard.press("Enter")
    page.wait_for_load_state("load")
    page.click('button:has(span:has-text("Custom"))')
    page.wait_for_timeout(2000)
    page.type('textarea[data-testid="lyrics-input-textarea"]', "pbNJ1sznC2Gr@gmail.com")
    page.wait_for_timeout(2000)
