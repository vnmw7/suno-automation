import pythonbible as bible
from pythonbible import Book


class ChapterSplitError(Exception):
    """Custom exception for errors during chapter splitting."""

    pass


def split_chapter_into_sections(book_name, book_chapter_str: str) -> str:
    """
    Splits a given Bible chapter into sections based on its total number of verses,
    according to specified rules.

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
        str: A comma-separated string of verse ranges (e.g., "1-10,11-20").
             The output is numbers in one line, nothing extra.

    Raises:
        ChapterSplitError: If the chapter cannot be processed, input is invalid,
                           or Bible data cannot be fetched. This allows the caller
                           to handle errors appropriately, as the function itself
                           must only return the formatted numbers string on success.
    """

    print(f"Splitting chapter: {book_name} {book_chapter_str}")

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
        return f"1-{total_verses}"

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

    return ",".join(sections_output)

    test_chapters = {
        ("2 John", "1"): 13,  # < 15 verses -> 1 section
        ("Jude", "1"): 25,  # 15-29 verses -> 2 sections
        ("Obadiah", "1"): 21,  # 15-29 verses -> 2 sections
        ("Genesis", "1"): 31,  # 30-45 verses -> 3 sections
        ("Mark", "1"): 45,  # 30-45 verses -> 3 sections
        ("John", "1"): 51,  # 46-60 verses -> 4 sections
        ("Acts", "2"): 47,  # 46-60 verses -> 4 sections (Actual verses for Acts 2)
        (
            "Matthew",
            "5",
        ): 48,  # 46-60 verses -> 4 sections (Actual verses for Matthew 5)
        ("Luke", "1"): 80,  # > 60 verses  -> 5 sections
        ("Psalm", "119"): 176,  # > 60 verses  -> 5 sections
        ("Philemon", "1"): 25,  # Example for 2 sections
    }

    # Mock bible.get_number_of_verses for testing without network/full library setup
    # Store original if it exists, to restore later (though not critical for this script)
    original_get_number_of_verses = bible.get_number_of_verses

    def mock_get_number_of_verses(book, chapter):
        # print(f"Mocking call for {book} {chapter}")
        if (book, str(chapter)) in test_chapters:
            return test_chapters[(book, str(chapter))]
        # Simulate library errors for unknown chapters
        raise bible.InvalidChapterError(
            f"Mock: Chapter {chapter} not found for book {book}"
        )

    bible.get_number_of_verses = mock_get_number_of_verses

    print("Running test cases:")
    for (book, chapter_str), expected_verses in test_chapters.items():
        try:
            print(f"Input: {book} {chapter_str} (Expected verses: {expected_verses})")
            result = split_chapter_into_sections(book, chapter_str)
            print(f"Output: {result}")

            # Verification of the output (optional, but good for testing)
            parts = result.split(",")
            total_verses_from_output = 0
            last_end_verse = 0
            valid_ranges = True
            for i, part in enumerate(parts):
                start_s, end_s = part.split("-")
                start_v, end_v = int(start_s), int(end_s)
                if start_v != last_end_verse + 1 and i > 0:  # Check continuity
                    print(f"  ERROR: Discontinuity in ranges for {book} {chapter_str}")
                    valid_ranges = False
                    break
                if start_v > end_v:  # Check valid range
                    print(f"  ERROR: Invalid range {part} for {book} {chapter_str}")
                    valid_ranges = False
                    break
                total_verses_from_output += end_v - start_v + 1
                last_end_verse = end_v
            if valid_ranges and last_end_verse != expected_verses:
                print(
                    f"  ERROR: Last verse {last_end_verse} does not match expected {expected_verses} for {book} {chapter_str}"
                )
            # No direct check for section count here, but it's implicitly tested by ranges

        except ChapterSplitError as e:
            print(f"Error for {book} {chapter_str}: {e}")
        print("-" * 20)

    # Test invalid input
    print("Testing invalid inputs:")
    invalid_inputs = [
        ("Genesis", "abc"),
        ("Genesis", "0"),
        ("Genesis", "-1"),
        ("NonExistentBook", "1"),
        ("Jude", "2"),  # Jude has only 1 chapter
    ]
    for book, chapter_s in invalid_inputs:
        try:
            print(f"Input: {book} {chapter_s}")
            result = split_chapter_into_sections(book, chapter_s)
            print(f"Output: {result} (UNEXPECTED SUCCESS)")
        except ChapterSplitError as e:
            print(f"Caught expected error: {e}")
        print("-" * 20)

    # Restore original function if needed for other parts of a larger application
    bible.get_number_of_verses = original_get_number_of_verses
