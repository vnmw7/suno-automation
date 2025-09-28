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

    # Context Menu Selectors
    OPTIONS_BUTTON = {
        "selectors": [
            # New selector based on provided element structure
            'button.context-menu-button:has(svg path[d*="M6 14q-.824"])',
            'button[class*="context-menu-button"]:has(svg)',
            # Original selectors
            'button[aria-label="More Options"]',
            'button[aria-label*="More Options"]',
            'button:has(svg path[d*="M10 6q0-.824.588-1.412"])',
            'button[aria-label*="options"]',
            'button[aria-label*="menu"]',
            'button[aria-label*="More"]',
            'button[data-state="open"]',
            'button[data-testid*="options"]',
            'button[data-testid*="menu"]',
            'button:has(svg[viewBox="0 0 24 24"])',
            'button:has(svg[data-testid*="dots"])',
            'button:has(svg[class*="dots"])',
            '[role="button"]:has(svg)'
        ],
        "timeout": 5000
    }

    CONTEXT_MENU = {
        "selectors": [
            # New selectors based on provided HTML structure
            "div[data-context-menu='true']",
            "div.css-hiwxta.eu96siw0[data-context-menu='true']",
            "div[data-mouseover-id][data-context-menu='true']",
            # Fallback to class-based selectors
            "div.css-hiwxta",
            "div.eu96siw0",
            # Original selectors kept as fallback
            "div[data-radix-menu-content]",
            "div[role='menu']",
            "[data-radix-popper-content-wrapper]",
            "div.radix-menu-content",
            "[role='menu'][data-state='open']",
            "div[data-radix-menu-content][data-state='open']",
            "[role='menu'][data-state='open']",
            ".context-menu[data-state='open']"
        ],
        "timeout": 10000
    }

    DOWNLOAD_TRIGGER = {
        "selectors": [
            # Primary selector for Download button with arrow icon
            'button.context-menu-button:has(span:has-text("Download")):has(svg)',
            'button.context-menu-button:has(svg path[d*="M12 15.575"]):has(span:has-text("Download"))',
            # More specific selector matching the exact structure
            'button[type="button"]:has(svg path[d*="M12 15.575q-.2 0-.375"]):has(span.css-s40uml:has-text("Download"))',
            # Selector with download icon path
            'button:has(svg path[d*="M6 20q-.824 0-1.412"]):has-text("Download")',
            # Fallback selectors
            'button:has-text("Download"):has(svg)',
            '*:has-text("Download"):has(svg[viewBox="0 0 24 24"])',
            '[role="menuitem"]:has-text("Download")'
        ],
        "timeout": 8000
    }

    DOWNLOAD_SUBMENU = {
        "selectors": [
            # Primary selector for download submenu container
            "div.css-1l1uabm.eu96siw2",
            # Container with MP3 Audio button
            "div.eu96siw2:has(button:has-text('MP3 Audio'))",
            # Context menu items container
            "div:has(> div.context-menu-item button:has-text('MP3 Audio'))",
            # Alternative selectors
            "div[data-context-menu='true'].css-hiwxta.eu96siw0",
            "div[data-mouseover-id][data-context-menu='true']",
            # Original selectors as fallback
            "div[data-radix-menu-content][data-state='open'][role='menu']",
            "*[role='menu'][data-state='open']"
        ],
        "timeout": 8000
    }

    MP3_OPTION = {
        "selectors": [
            # Most specific - using aria-label attribute (based on user's HTML sample)
            'button[aria-label="MP3 Audio"]',
            'button[type="button"][aria-label="MP3 Audio"]',

            # Text-based selectors with button element constraint
            "button.context-menu-button:has(span:has-text('MP3 Audio'))",
            "button.context-menu-button:has(svg):has-text('MP3 Audio')",
            "div.context-menu-item button:has-text('MP3 Audio')",

            # SVG path-based selector (specific to MP3 icon)
            "button[type='button']:has(svg path[d*='M9 20a1']):has-text('MP3 Audio')",

            # Less specific fallbacks - but still constrained to button elements
            "div[role='menuitem'] button:has-text('MP3 Audio')",
            "button:has-text('MP3 Audio')",
            "[data-testid*='mp3']"
            # REMOVED: "*:has-text('MP3 Audio')" - too generic, matches parent containers
        ],
        "timeout": 8000
    }

    DELETE_BUTTON = {
        "selectors": [
            # Primary selector combining aria-label and context-menu-button class for uniqueness
            'button[aria-label="Move to Trash"].context-menu-button',
            # Selector with trash icon SVG path and text
            'button.context-menu-button:has(svg path[d*="M7.308 20.5a1.74"]):has-text("Move to Trash")',
            # Type and aria-label combination
            'button[type="button"][aria-label="Move to Trash"]',
            # Context menu button with Move to Trash text
            'button.context-menu-button:has(span:has-text("Move to Trash"))',
            # Original selectors as fallback
            'div[role="menuitem"]:has-text("Move to Trash")',
            'div[role="menuitem"]:has-text("Trash")',
            '[role="menuitem"]:has-text("Move to Trash")',
            '[role="menuitem"]:has-text("Trash")',
            '[role="menuitem"]:has-text("Delete")',
            'div[role="menuitem"] span:has-text("Move to Trash")',
            'button:has-text("Delete")',
            'button:has-text("Trash")',
            'button:has-text("Remove")',
            'div[role="option"]:has-text("Delete")',
            'li:has-text("Delete")'
        ],
        "timeout": 5000
    }

    DOWNLOAD_ANYWAY_BUTTON = {
        "selectors": [
            # New selectors based on provided HTML structure
            'button[type="button"].rounded-full:has-text("Download Anyway")',
            'button.min-w-[200px]:has-text("Download Anyway")',
            'button.bg-background-tertiary:has-text("Download Anyway")',
            # Original selectors kept for compatibility
            'button:has(span:has-text("Download Anyway"))',
            'button:has-text("Download Anyway")',
            '*:has-text("Download Anyway")'
        ],
        "timeout": 10000
    }

    # Input Field Selectors
    LYRICS_INPUT = {
        # Primary: The most robust selector. It finds the "Lyrics" label,
        # then selects the adjacent container's textarea that also has the unique placeholder.
        # This is extremely unlikely to fail.
        "primary": 'div:has(> div div:text-is("Lyrics")) + div textarea[placeholder="Write some lyrics (leave empty for instrumental)"]',

        # Fallback: Per your request, this relies *only* on the structure.
        # It finds the "Lyrics" label and gets the textarea in the next container,
        # ignoring the placeholder text completely.
        "fallback": 'div:has(> div div:text-is("Lyrics")) + div textarea',

        # Secondary Fallback: A simple but effective selector that relies only on the unique placeholder,
        # in case the structure around the label changes.
        "secondary_fallback": 'textarea[placeholder="Write some lyrics (leave empty for instrumental)"]',
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
    # Song cards containing the actual song data (these are the song containers, not play buttons)
    SONG_CARD = 'div[data-testid="clip-row"].clip-row'

    # Legacy name kept for backward compatibility (will be deprecated)
    SONG_PLAY_BUTTON = 'div[data-testid="clip-row"].clip-row'

    SONG_ROW = '[data-testid="song-row"]'

    SONG_ID_ATTRIBUTES = {
        "primary": "data-clip-id",
        "fallback": "data-key"
    }

    SONG_ELEMENT_SELECTORS = [
        # Primary: Most specific selector combining multiple attributes for uniqueness
        'div.clip-row[data-testid="clip-row"].css-6rcthi.e1qa35zq0',
        # Secondary: Using data-testid which is most reliable
        'div[data-testid="clip-row"]',
        # Tertiary: Class-based fallback with partial class match
        'div.clip-row.e1qa35zq0',
        # Alternative: Using just the stable class name
        'div.clip-row',
        # Legacy: Old selectors for backward compatibility
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
        "headless": True,
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