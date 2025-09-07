# Changelog

## [Unreleased] - 2025-09-06

### Changed
- **AI Review Model Switch**: Migrated from Gemini 2.5 Pro to Gemini 2.5 Flash for song reviews
  - 7.5x faster processing: 15 RPM vs 2 RPM (Pro model)
  - Reduced API call delays from 31s to 5s between requests
  - Reduced song-to-song delays from 31s to 10s
  - Total review time per song reduced from ~93s to ~15s (6x faster)
  - Trade-off: Slightly less accuracy for significantly improved speed

### Fixed
- **Unicode Encoding Issues**: Fixed corrupted special characters in delete_song.py module
  - Replaced malformed Unicode characters in print statements with readable text prefixes
  - Fixed module import errors caused by UTF-8 decoding issues

- **Music Player Playback Speed**: Fixed issue where 2x and 3x playback speed controls were not working
  - Added `useEffect` hook to properly update audio element's `playbackRate` property when speed changes
  - Now correctly syncs React state with actual HTML5 audio playback rate

- **AI Review Rate Limiting**: Resolved Google Gemini API rate limit errors (429 quota exceeded)
  - Changed from parallel to sequential song review processing to respect API limits
  - Added configurable delays between API calls (31s for Gemini Pro free tier)
  - Implemented wait times between song reviews (31s to account for multiple API calls per song)
  - Created configuration system for easy switching between Gemini Pro and Flash models
  - **Added delays within single song review to prevent quota errors**:
    - 31-second delay after file upload before first prompt
    - 31-second delay between first and second prompts
    - Countdown display showing remaining wait time

### Added
- **Song Deletion API Endpoints**: Complete song management with deletion capabilities
  - `POST /song/delete` - Delete single song locally and/or from Suno.com
  - `POST /song/delete/batch` - Batch delete multiple songs with detailed results
  - `DELETE /song/delete/{song_id}` - RESTful deletion by Suno ID
  - `GET /song/find-songs` - Find songs in directories for deletion management
  - Created `backend/utils/delete_song.py` utility module with SongDeleter class
  - Supports both local file deletion and remote Suno.com deletion via browser automation
  - Includes automatic empty directory cleanup after file deletion
  - Comprehensive error handling and batch operation support

- **Granular Playback Speed Options**: Enhanced music player with more precise speed control
  - Added 12 speed options with 0.25x increments: 0.25x, 0.5x, 0.75x, 1x, 1.25x, 1.5x, 1.75x, 2x, 2.25x, 2.5x, 2.75x, 3x
  - Converted speed controls from buttons to dropdown selects for better UI space efficiency
  - Supports both global and per-song speed settings

- **Comprehensive AI Review Logging**: Enhanced debugging capabilities for song review process
  - Added detailed session-level logging with timestamps and progress tracking
  - Implemented full AI response logging (transcriptions and comparisons)
  - Added visual indicators for different log types (uploads, API calls, responses, errors)
  - Included rate limit countdown displays during wait periods
  - Added error classification with specific guidance for common issues

- **AI Review Configuration**: New configuration system for API rate management
  - Created `config/ai_review_config.py` for centralized settings
  - Support for switching between Gemini Pro (2 RPM) and Flash (15 RPM) models
  - Configurable rate limits for free and paid tiers
  - Adjustable delays between API calls and song reviews

### Changed
- **UI Improvements**: Updated speed control interface from button groups to dropdown selects
  - Global speed control now uses a select dropdown
  - Individual song speed controls now use select dropdowns
  - Maintains disabled state for individual controls when global speed is enabled

- **Review Processing Model**: Shifted from concurrent to sequential processing
  - Songs now reviewed one at a time to prevent rate limit violations
  - Added intelligent waiting between reviews based on API tier
  - Improved error handling with specific rate limit detection

### Added
- **Camoufox Actions Module**: New reusable browser automation utility class
  - Created `backend/utils/camoufox_actions.py` with CamoufoxActions class
  - Provides teleport_click and teleport_hover methods that bypass humanization
  - Uses direct JavaScript execution for instantaneous interactions
  - Supports left/right click options and configurable delays

### Fixed
- **Song Deletion Options Button**: Updated selector to target correct HTML element
  - Fixed `_find_options_button` method in delete_song.py to find div elements with "More Options" aria-label
  - Added specific selector for the three-dots menu icon structure
  - Fixed bare except statements to comply with Ruff linting rules (E722)
  
- **Song Deletion Delete Button**: Corrected selector for trash/delete menu item
  - Updated `_find_delete_button` method to find "Move to Trash" text in div[role="menuitem"] elements
  - Prioritized correct selector matching Suno's actual HTML structure
  
- **Song Deletion Confirmation**: Removed unnecessary confirmation dialog handling
  - Removed `_find_confirm_button` method as Suno doesn't show confirmation dialogs
  - Simplified deletion flow by removing confirmation step
  - Changed page load wait from "networkidle" to "domcontentloaded" for faster execution