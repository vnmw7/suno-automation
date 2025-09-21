fix: Update song ID extraction to use href attribute from song links

- Fixed song ID extraction failing due to incorrect selector (was looking for non-existent [data-testid="song-row"])
- Updated wait selector to use SONG_CARD (div[data-testid="clip-row"].clip-row) instead of SONG_ROW
- Implemented new extraction method to get song IDs from anchor tag href attributes (format: /song/{song_id})
- Added robust fallback to legacy attribute-based extraction (data-clip-id, data-key) if href method fails
- Improved debugging output to clearly identify extraction method used (href vs attribute)
- Ensures proper song tracking in database with correct Suno song IDs

feat: Update Suno UI selectors to use combined attributes for better stability

- Updated STYLE_INPUT selector to use stable attributes instead of dynamic placeholder text
  - Primary: textarea[maxlength="200"][class*="resize-none"]
  - Fallback: textarea[maxlength="200"]
  - Secondary: Multiple fallback options including old data-testid
- Updated TITLE_INPUT selector to target the second input element (index 1)
  - Primary: input[placeholder="Add a song title"]:nth-of-type(2)
  - Fallback: input[placeholder="Add a song title"] >> nth=1 (Playwright nth selector)
  - Secondary: input[placeholder="Add a song title"]:last-of-type
- Updated CREATE_BUTTON selector with combined attributes for accuracy
  - Primary: button[type="button"]:has-text("Create"):has(svg)
  - Fallback: button:has(span:has-text("Create"):has(svg))
  - Secondary: button[class*="rounded-full"]:has-text("Create")
- Fixed generate_song function in utils.py to use new selector format (primary/fallback/secondary_fallback)
  instead of old "selectors" array format


feat: Refactor and update Suno UI selectors for improved accuracy

- Renamed "tags" input to "style" input to accurately reflect its purpose (musical style, not tags)
- Updated style textarea selector to match new Suno UI: textarea[placeholder="Hip-hop, R&B, upbeat"]
- Updated title input selector to match new Suno UI: input[placeholder="Add a song title"]
- Added secondary fallback selectors for both style and title inputs
- Improved logging messages to correctly identify "style of music" instead of "tags"
- Enhanced fallback strategy with three levels of selectors for style and title inputs

feat: Centralize and optimize Suno UI selector management

- Created backend/configs/suno_selectors.py as a centralized configuration for all UI selectors
- Updated lyrics textarea selector to match new Suno UI: textarea[placeholder="Write some lyrics"]
- Implemented fallback selector strategy for all UI elements to improve resilience
- Made all selectors, timeouts, and browser configurations easily configurable in one place
- Added primary and fallback selectors for buttons, inputs, and song elements
- Improved error handling with detailed logging for selector failures
- Future UI changes now require updates only in suno_selectors.py

feat: Enhance SunoDownloader with improved error handling and download retries

- Updated download_song_v2.py to include a retry mechanism for downloads, allowing up to 3 attempts on failure.
- Improved logging for download processes, including detailed messages for each step and error encountered.
- Enhanced song ID extraction logic to ensure accurate identification from song elements.
- Updated filename generation to include song ID and timestamp for better tracking.
- Adjusted navigation messages for clarity during the download process.