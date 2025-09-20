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