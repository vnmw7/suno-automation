import importlib
import importlib.util
import os

from pythonbible import Book

utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils"))
bible_utils_path = os.path.join(utils_path, "bible_utils.py")

spec = importlib.util.spec_from_file_location("bible_utils", bible_utils_path)
bible_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bible_utils)

split_chapter_into_sections = bible_utils.split_chapter_into_sections

# Test with Book enum
book = Book.GENESIS
book_chapter = 1

try:
    # Get the display name
    book_display_name = str(book).replace("Book.", "")

    # Test with Book enum
    verse_ranges_enum = split_chapter_into_sections(book, str(book_chapter))
    print(
        f"Verse ranges for {book_display_name} {book_chapter} (using enum): {verse_ranges_enum}"
    )

    # Test with string name
    verse_ranges_string = split_chapter_into_sections("Genesis", str(book_chapter))
    print(
        f"Verse ranges for Genesis {book_chapter} (using string): {verse_ranges_string}"
    )

    # Test another book with enum
    book2 = Book.JOHN
    book_chapter2 = 3
    verse_ranges_john = split_chapter_into_sections(book2, str(book_chapter2))
    print(f"Verse ranges for JOHN {book_chapter2}: {verse_ranges_john}")

except bible_utils.ChapterSplitError as e:
    print(f"Error: {e}")
