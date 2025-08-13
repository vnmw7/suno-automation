# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-08-13

### Added
- Implemented a two-song review workflow in the frontend to download and review two songs sequentially.
- Added a backend endpoint (`/song/delete-files`) to delete song files from the server.
- Added functionality to delete songs from suno.com using browser automation when a "re-roll" verdict is given.
- Added `TODO` and `TOFIX` comments in the code to document suggestions for future improvements, including enhancing browser automation robustness, securing credentials, refactoring common code, and improving the song generation UX.

### Changed
- The song deletion logic is now more granular. It only deletes the specific songs that are marked for "re-roll" by the review process, both locally and from the suno.com website.
- The `handleGenerateSong` function in `ModalSongs.tsx` was completely restructured to support the new two-song review workflow.
- The backend deletion endpoint was updated to accept a list of specific songs to delete, including their indices on suno.com.

### Fixed
- Corrected an issue where only one of the two generated songs was being deleted from suno.com when a "re-roll" was requested. The system now correctly deletes both.

## [Unreleased] - 2024-12-19

### Fixed
- Corrected the frontend `generate_verse_range` function to use the correct `/ai-generation/verse-ranges` endpoint and send a JSON payload instead of query parameters.
- Reduced timeout for page load state during song creation to improve responsiveness

### Changed
- Refactored `ai_generation` routes to use the Gemini middleware directly (`middleware/gemini.py`) instead of the multi-tool agent (`multi_tool_agent/song_generation_agent.py`).
- Updated frontend `generateSongStructure` function to use new `/ai-generation/song-structure` endpoint instead of deprecated `/generate-song-structure`
- Added import for `ai_generation_router` in backend main.py
- Included `ai_generation_router` in the FastAPI app

### Added
- Added optional `structureId` field to frontend `SongStructureRequest` interface for song structure regeneration
- Added TODO comments throughout codebase for future improvements:
  - Missing frontend integration for new `/ai-generation/verse-ranges` endpoints
  - Missing `/download-song` endpoint implementation
  - Need for consistent error response structures across all endpoints
  - Type safety enhancement suggestions for shared types between frontend and backend
- Added TOFIX comments for:
  - Missing `/download-song` endpoint that frontend is calling

### Removed
- Removed deprecated `/generate-song-structure` endpoint from backend main.py.
- Removed deprecated `/generate-verse-ranges` and `/get-verse-ranges` endpoints from `main.py`.
- Removed unused `SongRequest` Pydantic model from `main.py`.
- Removed old `SongStructureRequest` class definition from main.py.

### Technical Debt
- Identified need to implement or fix `/download-song` endpoint referenced by frontend
- Identified opportunity for shared type definitions between TypeScript and Python
