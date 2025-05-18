import pythonbible as bible
from pythonbible import Book


class ChapterSplitError(Exception):
    """Custom exception for errors during chapter splitting."""

    pass


def split_chapter_into_sections(book_name, book_chapter_str: str) -> int:
    """
    Calculates the number of sections a Bible chapter should be split into,
    based on its total number of verses.

    Rules for number of sections based on total verses:
    - Less than 15 verses: 1 section
    - 15 to 29 verses (inclusive): 2 sections
    - 30 to 45 verses (inclusive): 3 sections
    - 46 to 60 verses (inclusive): 4 sections (i.e. >45 and <=60)
    - Over 60 verses: 5 sections

    Args:
        book_name: The Bible book, can be a pythonbible.Book enum or a string name.
        book_chapter_str (str): The chapter number as a string (e.g., "1", "10").

    Returns:
        int: The number of sections the chapter should be split into.

    Raises:
        ChapterSplitError: If the chapter cannot be processed, input is invalid,
                           or Bible data cannot be fetched.
    """

    print(f"Calculating sections for chapter: {book_name} {book_chapter_str}")

    try:
        book_chapter = int(book_chapter_str)
        if book_chapter <= 0:
            raise ValueError("Chapter number must be positive.")
    except ValueError as e:
        raise ChapterSplitError(
            f"Invalid chapter number '{book_chapter_str}': {e}"
        ) from e

    book_to_use = book_name
    if isinstance(book_name, str) and not hasattr(book_name, "value"):
        try:
            for book in Book:
                if (
                    book.name.lower() == book_name.lower()
                    or str(book).lower().replace("book.", "").strip()
                    == book_name.lower()
                ):
                    book_to_use = book
                    break
        except Exception:
            pass

    try:
        total_verses = bible.get_number_of_verses(book_to_use, book_chapter)

        if total_verses is None or total_verses <= 0:
            raise bible.InvalidChapterError(
                f"No verses found or chapter is empty for {book_name} {book_chapter} (verse count: {total_verses})."
            )
    except (bible.InvalidBookError, bible.InvalidChapterError) as e:
        raise ChapterSplitError(
            f"Invalid book or chapter: {book_name} {book_chapter}. Source error: {str(e)}"
        ) from e
    except Exception as e:
        raise ChapterSplitError(
            f"Unexpected error fetching verse count for {book_name} {book_chapter}: {str(e)}"
        ) from e

    num_sections: int
    if total_verses < 15:
        num_sections = 1
    elif total_verses < 30:
        num_sections = 2
    elif total_verses <= 45:
        num_sections = 3
    elif total_verses <= 60:
        num_sections = 4
    else:
        num_sections = 5

    if num_sections == 1:
        return 1

    sections_output = []
    start_verse_for_current_section = 1

    base_length_per_section = total_verses // num_sections
    num_sections_with_extra_verse = total_verses % num_sections

    for i in range(num_sections):
        current_section_length = base_length_per_section
        if i < num_sections_with_extra_verse:
            current_section_length += 1

        if current_section_length == 0:
            continue

        end_verse_for_current_section = (
            start_verse_for_current_section + current_section_length - 1
        )

        if i == num_sections - 1:
            end_verse_for_current_section = total_verses

        sections_output.append(
            f"{start_verse_for_current_section}-{end_verse_for_current_section}"
        )
        start_verse_for_current_section = end_verse_for_current_section + 1

        if start_verse_for_current_section > total_verses and i < num_sections - 1:
            break

    return num_sections
