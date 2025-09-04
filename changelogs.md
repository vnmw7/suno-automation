# Changelog

## [Unreleased] - 2025-09-04

### Fixed
- **Music Player Playback Speed**: Fixed issue where 2x and 3x playback speed controls were not working
  - Added `useEffect` hook to properly update audio element's `playbackRate` property when speed changes
  - Now correctly syncs React state with actual HTML5 audio playback rate

### Added
- **Granular Playback Speed Options**: Enhanced music player with more precise speed control
  - Added 12 speed options with 0.25x increments: 0.25x, 0.5x, 0.75x, 1x, 1.25x, 1.5x, 1.75x, 2x, 2.25x, 2.5x, 2.75x, 3x
  - Converted speed controls from buttons to dropdown selects for better UI space efficiency
  - Supports both global and per-song speed settings

### Changed
- **UI Improvements**: Updated speed control interface from button groups to dropdown selects
  - Global speed control now uses a select dropdown
  - Individual song speed controls now use select dropdowns
  - Maintains disabled state for individual controls when global speed is enabled