import pythonbible as bible
from pythonbible import Book

try:
    # Test with enum
    verses = bible.get_number_of_verses(Book.GENESIS, 1)
    print(f"Number of verses in Genesis 1 (using enum): {verses}")

    # Test with int value
    verses = bible.get_number_of_verses(1, 1)
    print(f"Number of verses in Genesis 1 (using int): {verses}")

    # Test more books
    print(f"Number of verses in Exodus 1: {bible.get_number_of_verses(Book.EXODUS, 1)}")
    print(
        f"Number of verses in Matthew 5: {bible.get_number_of_verses(Book.MATTHEW, 5)}"
    )

except Exception as e:
    print(f"Error: {e}")
