# TODO: Verify google-adk is properly installed with: pip install google-adk
# TOFIX: If google-adk import fails, consider using google.generativeai directly
# TOFIX: Add proper error handling for missing API keys (GOOGLE_API_KEY or GEMINI_API_KEY)
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from ._config import AI_MODEL_LITE

# TODO: Future Improvements
# 1. Integrate with centralized prompt constants once created
# 2. Consider adding context about the book/chapter to improve AI understanding
# 3. Implement prompt versioning for A/B testing different approaches
# 4. Add support for custom song structure templates

def generate_verse_ranges(book_name: str, book_chapter: int, num_sections: int) -> str:
    """Generate verse ranges for a Bible chapter using AI."""
    # Tool function for the agent to understand its capability
    # The actual generation will be handled by the agent based on its instruction
    return f"Splitting {book_name} chapter {book_chapter} into {num_sections} sections"


def generate_song_structure(book_name: str, book_chapter: int, verse_range: str) -> str:
    """Generate song structure for Bible verses using AI."""
    # Tool function for the agent to understand its capability
    return f"Creating song structure for {book_name} chapter {book_chapter}, verses {verse_range}"


def analyze_passage_tone(book_name: str, book_chapter: int, verse_range: str) -> str:
    """Analyze the emotional tone of a Bible passage."""
    # Tool function for the agent to understand its capability
    return f"Analyzing tone for {book_name} chapter {book_chapter}, verses {verse_range}"


# TODO: Add proper exception handling for Agent initialization
# TOFIX: Consider implementing a fallback mechanism if Agent creation fails
# TODO: Add retry logic with exponential backoff for API calls
# TOFIX: Implement request/response validation to ensure proper JSON format
# TODO: Add performance logging, specifically tracking token usage for thinking_budget
# TODO: Implement graceful fallback for ThinkingConfig initialization errors

root_agent = Agent(
    name="song_generation_agent",
    model=AI_MODEL_LITE,
    # planner=BuiltInPlanner(thinking_budget=THINKING_BUDGET_LITE),  # Fixed: Use planner instead of generate_content_config
    description=(
        "Agent to generate verse range from a Bible chapter, analyze tone, and create song structure."
    ),
    instruction=(
        "You are a helpful agent who can:\n"
        "1. Split Bible chapters into verse ranges\n"
        "2. Create song structures mapping sections to verse ranges\n"
        "3. Analyze the emotional tone of Bible passages\n\n"
        "When asked to split a chapter:\n"
        "- Split the given Bible chapter into the requested number of sections\n"
        "- Return ONLY the verse ranges separated by commas (e.g., '1-11, 12-22')\n"
        "- No explanations or extra text\n\n"
        "When asked to create a song structure:\n"
        "- Create a song structure using the given Bible verses\n"
        "- Use 4-6 sections (or more if needed) based on the verse content\n"
        "- Include sections like: Verse, Chorus, Bridge, Outro, Pre-Chorus, Post-Chorus, etc.\n"
        # TOFIX: Update instruction to explicitly request pure JSON output
        # TODO: Add example of expected JSON format to reduce parsing errors
        "- Return ONLY valid JSON format like: {'verse1': '1-5', 'chorus': '6-8', 'verse2': '9-12'}\n"
        "- Return ONLY a JSON object with no additional text or formatting\n"
        "- Do not include any explanations, markdown, or code blocks\n"
        "- Ensure the JSON uses double quotes for keys and values\n"
        "- Do not overlap or reuse verses between sections\n\n"
        "When asked to analyze tone:\n"
        "- Analyze the emotional tone of the given Bible passage\n"
        # TODO: Consider expanding tone scale from binary (0/1) to 1-5 range for more nuance
        # TOFIX: Add validation that returned value is within expected range
        "- Return ONLY '0' for negative tone or '1' for positive tone\n"
        "- No explanations"
    ),
    tools=[generate_verse_ranges, generate_song_structure, analyze_passage_tone],
)

# Create a runner for the agent
# Define an app name for the runner
APP_NAME = "song-generation-service"

# Create an instance of the session service for managing conversation history
# TODO: Consider implementing persistent session storage instead of InMemorySessionService
# TOFIX: Add session cleanup mechanism to prevent memory leaks in long-running processes
session_service = InMemorySessionService()

# Create the runner with all required arguments
# TODO: Add error handling for runner initialization failures
# TOFIX: Implement health check mechanism to verify runner is operational
agent_runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)
