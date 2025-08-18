# Changelog

## [Unreleased] - 2025-08-18

### Changed
- Refactored the song structure generation logic in the Song Management modal to ensure it fetches the most up-to-date structure information from the database before deciding to generate a new structure or regenerate an existing one. This prevents using stale data and ensures the correct action (generate vs. regenerate) is always taken.
