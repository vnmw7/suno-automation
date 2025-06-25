import importlib
import importlib.util
import os

lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lib"))
supabase_utils_path = os.path.join(lib_path, "supabase.py")

spec = importlib.util.spec_from_file_location("supabase_utils", supabase_utils_path)
supabase_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supabase_utils)

supabase = supabase_utils.supabase


def bookname_to_abrv(bookname: str) -> str:
    """
    Convert book name to a more readable format.
    """

    mapping = {
        "1 Chronicles": "1CH",
        "1 Corinthians": "1CO",
        "1 Esdras": "1ES",
        "1 John": "1JN",
        "1 Kings": "1KI",
        "1 Maccabees": "1MA",
        "1 Peter": "1PE",
        "1 Samuel": "1SA",
        "1 Thessalonians": "1TH",
        "1 Timothy": "1TI",
        "2 Chronicles": "2CH",
        "2 Corinthians": "2CO",
        "2 Esdras": "2ES",
        "2 John": "2JN",
        "2 Kings": "2KI",
        "2 Maccabees": "2MA",
        "2 Peter": "2PE",
        "2 Samuel": "2SA",
        "2 Thessalonians": "2TH",
        "2 Timothy": "2TI",
        "3 John": "3JN",
        "3 Maccabees": "3MA",
        "4 Maccabees": "4MA",
        "Acts": "ACT",
        "Amos": "AMO",
        "Baruch": "BAR",
        "Colossians": "COL",
        "Daniel (Greek)": "DAG",
        "Daniel": "DAN",
        "Deuteronomy": "DEU",
        "Ecclesiastes": "ECC",
        "Ephesians": "EPH",
        "Esther (Greek)": "ESG",
        "Esther": "EST",
        "Exodus": "EXO",
        "Ezekiel": "EZK",
        "Ezra": "EZR",
        "Galatians": "GAL",
        "Genesis": "GEN",
        "Habakkuk": "HAB",
        "Haggai": "HAG",
        "Hebrews": "HEB",
        "Hosea": "HOS",
        "Isaiah": "ISA",
        "James": "JAS",
        "Judges": "JDG",
        "Judith": "JDT",
        "Jeremiah": "JER",
        "John": "JHN",
        "Job": "JOB",
        "Joel": "JOL",
        "Jonah": "JON",
        "Joshua": "JOS",
        "Jude": "JUD",
        "Lamentations": "LAM",
        "Leviticus": "LEV",
        "Luke": "LUK",
        "Malachi": "MAL",
        "Prayer of Manasseh": "MAN",
        "Matthew": "MAT",
        "Micah": "MIC",
        "Mark": "MRK",
        "Nahum": "NAM",
        "Nehemiah": "NEH",
        "Numbers": "NUM",
        "Obadiah": "OBA",
        "Philemon": "PHM",
        "Philippians": "PHP",
        "Proverbs": "PRO",
        "Psalm 151": "PS2",
        "Psalms": "PSA",
        "Revelation": "REV",
        "Romans": "ROM",
        "Ruth": "RUT",
        "Sirach": "SIR",
        "Song of Solomon": "SNG",
        "Titus": "TIT",
        "Tobit": "TOB",
        "Wisdom": "WIS",
        "Zechariah": "ZEC",
        "Zephaniah": "ZEP",
    }
    return mapping.get(bookname, bookname)


def song_strcture_to_lyrics(input_dict, book_name: str, book_chapter: int) -> dict:
    output_dict = {}
    current_book_abrv = bookname_to_abrv(book_name)

    for section_key, verse_range_str in input_dict.items():
        section_verses_data = {}
        verse_numbers_to_fetch = []

        cleaned_verse_range_str = verse_range_str.strip()

        # Extract verse range by removing book name and chapter
        if cleaned_verse_range_str.startswith(f"{book_name} {book_chapter}:"):
            cleaned_verse_range_str = cleaned_verse_range_str[len(f"{book_name} {book_chapter}:") :]

        if "-" in cleaned_verse_range_str:
            parts = cleaned_verse_range_str.split("-")
            if len(parts) == 2:
                start_v_str, end_v_str = parts
                try:
                    start_v = int(start_v_str.strip())
                    end_v = int(end_v_str.strip())
                    if start_v <= end_v:
                        verse_numbers_to_fetch = range(start_v, end_v + 1)
                    else:
                        print(
                            f"Warning: Invalid range '{cleaned_verse_range_str}' for section '{section_key}'. Start verse > end verse."
                        )
                except ValueError:
                    print(
                        f"Error: Malformed range '{cleaned_verse_range_str}' for section '{section_key}'. Could not convert parts to int."
                    )
            else:
                print(
                    f"Error: Malformed range string '{cleaned_verse_range_str}' for section '{section_key}'. Expected format 'start-end'."
                )
        else:
            try:
                verse_numbers_to_fetch = [int(cleaned_verse_range_str)]
            except ValueError:
                print(
                    f"Error: Malformed verse number '{cleaned_verse_range_str}' for section '{section_key}'. Could not convert to int."
                )

        for verse_num in verse_numbers_to_fetch:
            try:
                verse_text_response = (
                    supabase.table("bible_verses_tbl")
                    .select("verse_text")
                    .eq("book", current_book_abrv)
                    .eq("chapter", book_chapter)
                    .eq("start_verse", verse_num)
                    .single()
                    .execute()
                )
                actual_verse_text = ""
                if (
                    verse_text_response.data
                    and "verse_text" in verse_text_response.data
                ):
                    actual_verse_text = verse_text_response.data["verse_text"]
                else:
                    print(
                        f"Warning: No verse text found for {current_book_abrv} {book_chapter}:{verse_num} in section '{section_key}'"
                    )

                section_verses_data[str(verse_num)] = actual_verse_text
            except Exception as e:
                print(
                    f"Exception fetching/processing verse {current_book_abrv} {book_chapter}:{verse_num} for section '{section_key}': {e}"
                )
                section_verses_data[str(verse_num)] = ""

        output_dict[section_key] = section_verses_data

    return output_dict
