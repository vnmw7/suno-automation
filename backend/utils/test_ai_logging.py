import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_functions import generate_verse_ranges, generate_song_structure

def test_logging():
    """Test the AI logging functionality"""
    print("Testing AI logging...")
    
    # Test 1: Generate verse ranges
    print("\n1. Testing verse range generation:")
    verse_ranges = generate_verse_ranges("Genesis", 1)
    print(f"Generated verse ranges: {verse_ranges}")
    
    # Test 2: Generate song structure (if verse ranges were generated)
    if verse_ranges and len(verse_ranges) > 0:
        print("\n2. Testing song structure generation:")
        song_structure = generate_song_structure("Genesis", 1, verse_ranges[0])
        print(f"Generated song structure: {song_structure}")
    
    print("\nTest complete! Check the logs with: python backend\\utils\\log_viewer.py")

if __name__ == "__main__":
    test_logging()
