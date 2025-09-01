"""
Test script for the manual review endpoint.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

# Import the functions directly for testing
import sys
sys.path.append('.')
from api.song.routes import slugify_text, parse_song_filename

def test_slugify():
    """Test the slugify_text function."""
    test_cases = [
        ("Ruth 1:1-11", "ruth-1-1-11"),
        ("Amazing Grace", "amazing-grace"),
        ("John 3:16", "john-3-16"),
        ("1 Kings 2:3-5", "1-kings-2-3-5"),
        ("Test   Multiple  Spaces", "test-multiple-spaces"),
        ("Special!@#$%Characters", "specialcharacters"),
    ]
    
    print("Testing slugify_text function:")
    for input_text, expected in test_cases:
        result = slugify_text(input_text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_text}' -> '{result}' (expected: '{expected}')")
    print()

def test_parse_filename():
    """Test the parse_song_filename function."""
    test_cases = [
        "ruth-1-1-11_index_-1_20250830143022.mp3",
        "ruth-1-1-11_index_-2_20250830115445.mp3",
        "ruth-1-1-11_index_0_20250830120030.mp3",
        "amazing-grace-verse-1-5_index_1_20250830083015.mp3",
        "invalid_filename.mp3",
    ]
    
    print("Testing parse_song_filename function:")
    for filename in test_cases:
        result = parse_song_filename(filename)
        if result:
            print(f"  ✓ {filename}")
            print(f"    - Title slug: {result['title_slug']}")
            print(f"    - Index: {result['index']}")
            print(f"    - Created: {result['created_date']}")
        else:
            print(f"  ✗ {filename} - Failed to parse")
    print()

def create_test_files():
    """Create test song files in the final_review directory."""
    review_dir = Path("backend/songs/final_review")
    review_dir.mkdir(parents=True, exist_ok=True)
    
    # Test files to create
    test_files = [
        "ruth-1-1-11_index_-2_20250830115445.mp3",
        "ruth-1-1-11_index_-1_20250830143022.mp3",
        "ruth-1-1-11_index_0_20250830120030.mp3",
        "ruth-2-1-5_index_-1_20250830130000.mp3",
        "john-3-16_index_0_20250830140000.mp3",
    ]
    
    print("Creating test files:")
    for filename in test_files:
        file_path = review_dir / filename
        # Create empty MP3 file for testing
        file_path.write_bytes(b'')
        print(f"  Created: {filename}")
    print()

async def test_endpoint():
    """Test the manual review endpoint with HTTP requests."""
    print("Testing manual review endpoint:")
    print("Note: This requires the FastAPI server to be running.")
    print("Start the backend server and then make a request to:")
    print("  POST http://localhost:8000/api/song/manual-review")
    print("  Body: {")
    print('    "bookName": "Ruth",')
    print('    "chapter": 1,')
    print('    "verseRange": "1-11"')
    print("  }")
    print()
    print("Expected response: 3 matching files for Ruth 1:1-11")
    print()

def main():
    """Run all tests."""
    print("=" * 60)
    print("Manual Review Endpoint Test Suite")
    print("=" * 60)
    print()
    
    # Run tests
    test_slugify()
    test_parse_filename()
    create_test_files()
    asyncio.run(test_endpoint())
    
    print("=" * 60)
    print("Tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()