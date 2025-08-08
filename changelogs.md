# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2024-12-19

### Fixed
- Corrected the frontend `generate_verse_range` function to use the correct `/ai-generation/verse-ranges` endpoint and send a JSON payload instead of query parameters.

### Changed
- Updated frontend `generateSongStructure` function to use new `/ai-generation/song-structure` endpoint instead of deprecated `/generate-song-structure`
- Added import for `ai_generation_router` in backend main.py
- Included `ai_generation_router` in the FastAPI app

### Added
- Added optional `structureId` field to frontend `SongStructureRequest` interface for song structure regeneration
- Added TODO comments throughout codebase for future improvements:
  - Duplicate verse range endpoints in main.py that need consolidation
  - Missing frontend integration for new `/ai-generation/verse-ranges` endpoints
  - Missing `/download-song` endpoint implementation
  - Need for consistent error response structures across all endpoints
  - Type safety enhancement suggestions for shared types between frontend and backend
- Added TOFIX comments for:
  - Duplicate verse range endpoints in main.py
  - Missing `/download-song` endpoint that frontend is calling

### Removed
- Removed deprecated `/generate-song-structure` endpoint from backend main.py
- Removed old `SongStructureRequest` class definition from main.py

### Technical Debt
- Identified need to consolidate verse range endpoints (currently duplicated in main.py and ai_generation routes)
- Identified need to implement or fix `/download-song` endpoint referenced by frontend
- Identified opportunity for shared type definitions between TypeScript and Python
