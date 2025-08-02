from google.adk.agents import Agent
from .config import AI_MODEL

# TODO: Future Improvements
# 1. Integrate with centralized prompt constants once created
# 2. Add support for different Bible versions (NIV, KJV, ESV, etc.)
# 3. Consider adding context about the book/chapter to improve AI understanding
# 4. Implement prompt versioning for A/B testing different approaches
# 5. Add support for custom song structure templates

def generate_verse_ranges(book_name: str, book_chapter: int, num_sections: int) -> str:
    """Generate verse ranges for a Bible chapter using AI."""
    prompt = f"Split {book_name} {book_chapter} in Christian NIV Bible into {num_sections} sections of similar size which stand alone. Give the range of verses separated by commas. Provide the output as numbers in oneline, nothing extra like explanations. Do not include the thinking and thought process to save output tokens."
    
    # Return the prompt for the agent to process
    return prompt


def generate_song_structure(book_name: str, book_chapter: int, verse_range: str) -> str:
    """Generate song structure for Bible verses using AI."""
    prompt = f"""
    Make a song structure using the Book of {book_name} chapter {book_chapter}, strictly from verses {verse_range} in the Bible only. The song will have 4-6 (or more if applicable) naturally segmented based on the Bible verse contents. Strictly do not overlap nor reuse the verses in each segment. Strictly the output should be in json format: {{'stanza label': 'bible verse range number only', 'stanza label': 'bible verse range number only'}}. Do not provide any explanation only the json output.

    Here are the core building blocks. 
    1. Verse - To tell the story, set the scene, and provide details
    2. Chorus - To state the main idea or theme of the song
    3. Bridge - To provide a contrast and a break from repetition
    4. Intro - To set the mood, key, and tempo
    5. Outro - To bring the song to a conclusion
    6. Pre-Chorus - A short section that builds anticipation before the chorus
    7. Post-Chorus - A section that comes immediately after a chorus
    8. Hook - The single most catchy, memorable part
    9. Refrain - A line or phrase that repeats
    10. Solo/Instrumental Break - Showcases a particular instrument
    11. Middle 8 - Another name for a Bridge
    12. Breakdown - Stripped back arrangement section
    """
    
    return prompt


def analyze_passage_tone(book_name: str, book_chapter: int, verse_range: str) -> str:
    """Analyze the emotional tone of a Bible passage."""
    prompt = f"Analyze the overall Bible passage tone for {book_name} {book_chapter}:{verse_range}. Strictly the output should be 0 or 1 only. 0 for negative and 1 for positive. Do not provide any explanation only the number."
    
    return prompt


root_agent = Agent(
    name="song_generation_agent",
    model=AI_MODEL,
    description=(
        "Agent to generate verse range from a Bible chapter, analyze tone, and create song structure."
    ),
    instruction=(
        "You are a helpful agent who can:\n"
        "1. Split Bible chapters into verse ranges\n"
        "2. Create song structures mapping sections to verse ranges\n"
        "3. Analyze the emotional tone of Bible passages\n"
        "Always return JSON format for song structures."
    ),
    tools=[generate_verse_ranges, generate_song_structure, analyze_passage_tone],
)
