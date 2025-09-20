"""
System: Suno Automation
Module: Suno UI Selectors Configuration
Purpose: Centralized configuration for all Suno website UI selectors and element references
"""

class SunoSelectors:
    """
    Centralized configuration for all Suno UI selectors.
    Update these values when Suno changes their UI structure.
    """

    # Navigation URLs
    CREATE_URL = "https://suno.com/create"

    # Button Selectors
    CUSTOM_BUTTON = {
        "primary": 'button:has(span:has-text("Custom"))',
        "fallback": 'button:has-text("Custom")',
        "timeout": 10000
    }

    CREATE_BUTTON = {
        "primary": 'button[type="button"]:has-text("Create"):has(svg)',
        "fallback": 'button:has(span:has-text("Create"):has(svg))',
        "secondary_fallback": 'button[class*="rounded-full"]:has-text("Create")',
        "timeout": 5000
    }

    # Input Field Selectors
    LYRICS_INPUT = {
        # Updated selector for new textarea without data-testid
        "primary": 'textarea[placeholder="Write some lyrics"]',
        # Fallback to old selector in case it's still used somewhere
        "fallback": 'textarea[data-testid="lyrics-input-textarea"]',
        "timeout": 10000
    }

    STYLE_INPUT = {
        # Primary selector combining multiple stable attributes
        "primary": 'textarea[maxlength="200"][class*="resize-none"]',
        # Fallback to maxlength only
        "fallback": 'textarea[maxlength="200"]',
        # Additional fallback to old data-testid or class pattern
        "secondary_fallback": 'textarea[data-testid="tag-input-textarea"], textarea.resize-none[class*="outline-none"]',
        "timeout": 10000
    }

    TITLE_INPUT = {
        # Primary selector targeting the second input element (index 1)
        "primary": 'input[placeholder="Add a song title"]:nth-of-type(2)',
        # Fallback using nth-match for the second occurrence
        "fallback": 'input[placeholder="Add a song title"] >> nth=1',
        # Additional fallback using last-of-type or class combination
        "secondary_fallback": 'input[placeholder="Add a song title"]:last-of-type',
        "timeout": 10000
    }

    # Song List Selectors
    SONG_PLAY_BUTTON = '[aria-label="Play Song"]'

    SONG_ROW = '[data-testid="song-row"]'

    SONG_ID_ATTRIBUTES = {
        "primary": "data-clip-id",
        "fallback": "data-key"
    }

    SONG_ELEMENT_SELECTORS = [
        '[data-clip-id]',
        '[role="row"][data-key]'
    ]

    # Wait Times (in milliseconds)
    WAIT_TIMES = {
        "short": 1000,
        "medium": 2000,
        "long": 3000,
        "page_load": 5000
    }

    # Browser Configuration
    BROWSER_CONFIG = {
        "headless": False,
        "persistent_context": True,
        "user_data_dir": "backend/camoufox_session_data",
        "os": "windows",
        "humanize": True,
        "i_know_what_im_doing": True
    }

    @classmethod
    def get_selector(cls, element_name, selector_type="primary"):
        """
        Retrieve a selector for a given element.

        Args:
            element_name: Name of the UI element (e.g., "LYRICS_INPUT")
            selector_type: Type of selector to retrieve ("primary" or "fallback")

        Returns:
            str: The selector string or None if not found
        """
        element = getattr(cls, element_name, None)
        if element and isinstance(element, dict):
            return element.get(selector_type)
        return element

    @classmethod
    def get_timeout(cls, element_name):
        """
        Get the timeout value for a specific element.

        Args:
            element_name: Name of the UI element

        Returns:
            int: Timeout in milliseconds or default 10000
        """
        element = getattr(cls, element_name, None)
        if element and isinstance(element, dict):
            return element.get("timeout", 10000)
        return 10000