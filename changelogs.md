# Changelog

## [Unreleased] - 2025-08-18

### Fixed
- Fixed a bug in `get_song_with_lyrics` where it was incorrectly called with a `pg1_id` instead of a `structure_id`. The function now correctly accepts a `pg1_id` and fetches the associated song and lyric data more efficiently.
- Fixed Pydantic validation error in `DownloadTestResponse` where the `error` field was receiving `None` instead of a string. Updated the field type to `Optional[str]` and modified the response building logic in `debug_download_both_songs` function to only include the `error` field when it actually has a value.
- Resolved "`& was unexpected at this time`" error in logging setup by changing the log file directory structure to place log files directly in the `backend\logs` directory without creating subdirectories.
- Updated AI review logging configuration to use a flat directory structure, eliminating the need for `ai-review` subfolder creation that was causing filesystem errors.

### Added
- Created reusable AI review utilities module at `backend\utils\ai_review.py` by extracting the `review_song_with_ai` function from `backend\api\ai_review\utils.py`. This module includes all necessary helper functions (`upload_file_to_google_ai`, `send_prompt_to_google_ai`) and can now be imported from anywhere in the project for song quality assessment.

### Changed
- Refactored the song structure generation logic in the Song Management modal to ensure it fetches the most up-to-date structure information from the database before deciding to generate a new structure or regenerate an existing one. This prevents using stale data and ensures the correct action (generate vs. regenerate) is always taken.
- Fixed a bug in the song generation process where the script would time out waiting for song creation. The detection mechanism was updated to poll for new song elements on the page instead of relying on network state, making song creation detection more reliable.
- Improved error handling in orchestrator routes by properly handling optional fields in Pydantic models and ensuring consistent response structure across all endpoints.
- Updated `review_song_with_ai` function parameter from `song_structure_id` to `pg1_id` to better reflect that it references the database ID from tblprogress table rather than song_structure_tbl.
- Refactored AI review route endpoint (`backend\api\ai_review\routes.py`) to use the centralized AI review utilities from `backend\utils\ai_review.py` instead of local utils. This eliminates code duplication and ensures consistency across the application.
- Updated `SongReviewRequest` model to use `pg1_id` parameter instead of `song_structure_id` to match the database schema in `tblprogress_v1` table, improving data consistency and reducing confusion about which table ID is being referenced.
- Updated orchestrator workflow (`backend\api\orchestrator\utils.py`) to use the centralized AI review utilities from `backend\utils\ai_review.py` in the `review_all_songs` function, ensuring consistent AI review behavior across all parts of the application.
- Synchronized AI review logic across all modules by ensuring both `backend\api\ai_review\utils.py` and `backend\utils\ai_review.py` contain identical implementations of the review functionality, maintaining code consistency while preserving module independence.
