# Changelog

## [Unreleased] - 2025-08-18

### Fixed
- Fixed Pydantic validation error in `DownloadTestResponse` where the `error` field was receiving `None` instead of a string. Updated the field type to `Optional[str]` and modified the response building logic in `debug_download_both_songs` function to only include the `error` field when it actually has a value.
- Resolved "`& was unexpected at this time`" error in logging setup by changing the log file directory structure to place log files directly in the `backend\logs` directory without creating subdirectories.
- Updated AI review logging configuration to use a flat directory structure, eliminating the need for `ai-review` subfolder creation that was causing filesystem errors.

### Changed
- Refactored the song structure generation logic in the Song Management modal to ensure it fetches the most up-to-date structure information from the database before deciding to generate a new structure or regenerate an existing one. This prevents using stale data and ensures the correct action (generate vs. regenerate) is always taken.
- Fixed a bug in the song generation process where the script would time out waiting for song creation. The detection mechanism was updated to poll for new song elements on the page instead of relying on network state, making song creation detection more reliable.
- Improved error handling in orchestrator routes by properly handling optional fields in Pydantic models and ensuring consistent response structure across all endpoints.
