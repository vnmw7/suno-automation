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

    print(f"[split_chapter_into_sections()] Calculating sections for chapter: {book_name} {book_chapter_str}")

    try:
        book_chapter = int(book_chapter_str)
        if book_chapter <= 0:
            raise ValueError("Chapter number must be positive.")
    except ValueError as e:
        raise ChapterSplitError(
            f"Invalid chapter number '{book_chapter_str}': {e}"
        ) from e

    if isinstance(book_name, str):
        try:
            print(f"Normalizing book name: {book_name}")
            normalized_book_name = book_name.strip().replace(" ", "_").upper()
            print(f"Normalized book name: {normalized_book_name}")

            if normalized_book_name.startswith("1_"):
                normalized_book_name = normalized_book_name[2:] + "_1"
            elif normalized_book_name.startswith("2_"):
                normalized_book_name = normalized_book_name[2:] + "_2"
            elif normalized_book_name.startswith("3_"):
                normalized_book_name = normalized_book_name[2:] + "_3"

            print(f"Normalized book name: {normalized_book_name}")
            
            book_to_use = Book[normalized_book_name]
            print(f"Using book enum: {book_to_use}")
        except KeyError:
            # If direct match fails, try a more general normalization
            try:
                cleaned_book_name = book_name.lower().replace(" ", "")
                for book in Book:
                    if book.name.lower().replace("_", "") == cleaned_book_name:
                        book_to_use = book
                        break
                else:
                    # If no match is found after iterating, we keep the original string
                    # and let the bible library handle it, logging the failure.
                    print(f"Could not find a matching book enum for '{book_name}'. Passing as is.")
                    book_to_use = book_name
            except Exception as e:
                print(f"An unexpected error occurred during book normalization for '{book_name}': {e}")
                book_to_use = book_name
    else:
        book_to_use = book_name

    try:
        total_verses = bible.get_number_of_verses(book_to_use, book_chapter)
        print(f"[split_chapter_into_sections({book_name}, {book_chapter_str})] Total verses in {book_name} {book_chapter}: {total_verses}")

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

    print(
        f"Chapter {book_name} {book_chapter} split into {num_sections} sections: {sections_output}"
    )
    return num_sections
