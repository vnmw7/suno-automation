# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-08-15

### Added
- **Orchestrator Module**: Complete automated song workflow system with dedicated API module (`backend/api/orchestrator/`)
  - Created `routes.py` with `/orchestrator/workflow` main endpoint and `/orchestrator/status` health check
  - Created `models.py` with comprehensive request/response models for workflow operations
  - Created `utils.py` with core workflow logic, retry mechanisms, and file management utilities
- **Automated Song Generation Workflow**: End-to-end automation handling generation, download, review, and file management
  - Generates 2 songs per request on Suno.com automatically
  - Downloads both songs using negative indexing (-1, -2) for reliable song retrieval
  - AI quality review integration with automatic verdict processing
  - 3-attempt intelligent retry logic with exponential backoff
- **Fail-Safe Mechanism**: Backup system to preserve work when AI consistently rejects songs
  - Preserves final attempt songs instead of deleting them
  - Moves backup songs to `backend/songs/final_review` with "_FAILSAFE" suffix
  - Ensures no work is lost even after complete workflow failure
- **Enhanced File Management**: Automated organization of generated songs
  - Approved songs (`verdict: "continue"`) → `backend/songs/final_review`
  - Rejected songs (`verdict: "re-roll"`) → deleted (except final attempt)
  - Temporary downloads → `backend/songs/temp`
  - Fail-safe backups → `backend/songs/final_review` with clear labeling
- **Comprehensive Workflow Tracking**: Detailed progress reporting and statistics
  - Attempt-by-attempt tracking with success/failure reasons
  - Song generation, download, and review statistics
  - Comprehensive error handling and logging with emoji-prefixed messages
  - User-friendly progress reporting with detailed workflow results

### Changed
- **Frontend Simplification**: Completely refactored `ModalSongs.tsx` song generation process
  - **BREAKING CHANGE**: Replaced complex multi-step manual process with single orchestrator API call
  - Removed individual calls to generate, download, and review endpoints
  - Single button click now handles entire workflow automatically
  - Enhanced user experience with real-time workflow progress updates
  - Updated button text and descriptions to reflect automated nature
- **API Architecture**: Improved separation of concerns with dedicated orchestrator service
  - Song operations (`/song/`) focus on individual tasks
  - Orchestrator operations (`/orchestrator/`) handle complex workflows
  - Better error handling and response consistency across endpoints
- **Import Cleanup**: Removed unused imports from simplified frontend components
  - Cleaned up `generateSong`, `downloadSongAPI`, and `reviewSongAPI` imports
  - Removed unused type definitions (`SongDownloadRequest`, `SongReviewRequest`)
  - Streamlined component dependencies and reduced bundle size

### Fixed
- **Song Download System**: Enhanced reliability with negative indexing support
  - Fixed duplicate song element handling in Suno.com interface
  - Improved browser automation with "teleport" click techniques for speed and reliability
  - Better error handling for premium content warnings and download failures
- **AI Review Integration**: Seamless integration between orchestrator and review system
  - Fixed review API call integration within orchestrator workflow
  - Proper error handling for review failures with fallback mechanisms
  - Enhanced logging for review process debugging and monitoring

### Technical Improvements
- **Robust Browser Automation**: Enhanced download reliability with multiple fallback strategies
  - Teleport click/hover techniques for bypassing bot detection
  - Multiple selector patterns for element location resilience
  - Enhanced scrolling and visibility verification
- **Error Handling**: Comprehensive exception handling throughout workflow
  - Graceful degradation when individual steps fail
  - Detailed error reporting with actionable information
  - Automatic recovery mechanisms for transient failures
- **Code Organization**: Professional modular architecture for maintainability
  - Single responsibility principle with dedicated utility functions
  - Clear separation between orchestrator logic and individual operations
  - Comprehensive documentation and inline comments

### Developer Experience
- **Enhanced Logging**: Emoji-prefixed log messages for easy filtering and monitoring
  - 🎼 for orchestrator operations
  - 🛡️ for fail-safe mechanisms  
  - ✅ for success confirmations
  - ⚠️ for warnings and non-critical issues
- **Comprehensive Documentation**: Detailed docstrings and code comments
  - Clear explanation of workflow steps and decision points
  - Usage examples and parameter documentation
  - Troubleshooting guides embedded in code comments

## [1.0.0] - 2024-12-19

### Fixed
- Corrected the frontend `generate_verse_range` function to use the correct `/ai-generation/verse-ranges` endpoint and send a JSON payload instead of query parameters
- Reduced timeout for page load state during song creation to improve responsiveness

### Changed
- Refactored `ai_generation` routes to use the Gemini middleware directly (`middleware/gemini.py`) instead of the multi-tool agent (`multi_tool_agent/song_generation_agent.py`)
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
- Removed deprecated `/generate-song-structure` endpoint from backend main.py
- Removed deprecated `/generate-verse-ranges` and `/get-verse-ranges` endpoints from `main.py`
- Removed unused `SongRequest` Pydantic model from `main.py`
- Removed old `SongStructureRequest` class definition from main.py

### Technical Debt
- Identified need to implement or fix `/download-song` endpoint referenced by frontend
- Identified opportunity for shared type definitions between TypeScript and Python
