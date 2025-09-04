# Changelog

## [Unreleased] - 2025-09-04

### Fixed
- **Music Player Playback Speed**: Fixed issue where 2x and 3x playback speed controls were not working
  - Added `useEffect` hook to properly update audio element's `playbackRate` property when speed changes
  - Now correctly syncs React state with actual HTML5 audio playback rate

- **AI Review Rate Limiting**: Resolved Google Gemini API rate limit errors (429 quota exceeded)
  - Changed from parallel to sequential song review processing to respect API limits
  - Added configurable delays between API calls (30s for Gemini Pro free tier)
  - Implemented wait times between song reviews (65s to account for 2 API calls per song)
  - Created configuration system for easy switching between Gemini Pro and Flash models

### Added
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