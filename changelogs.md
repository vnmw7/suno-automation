# Changelog

## [2025-08-31] - Critical MP3 Playback Bug Fix and Security Hardening

### Fixed
- **NameError in song streaming endpoint**: Fixed undefined `safe_filename` variable causing 500 Internal Server Error when streaming MP3 files
- **Audio playback failure**: Resolved "Audio format not supported" error that was actually caused by server returning error JSON instead of audio data
- **CORS security vulnerability**: Replaced wildcard CORS origins with specific allowed origins list

### Security Improvements
- **Directory traversal protection**: Implemented robust path validation using Python's `pathlib` to prevent unauthorized file access
- **Path resolution security**: All file paths are now resolved to absolute paths and verified to be within the songs directory sandbox
- **CORS hardening**: Restricted CORS to specific origins and methods instead of allowing all origins

### Technical Root Cause Analysis
- **Primary issue**: FastAPI endpoint at `/api/songs/{file_path:path}` was crashing due to `NameError: name 'safe_filename' is not defined`
- **Browser behavior**: The browser's Opaque Response Blocking (ORB) security feature blocked the error response, causing `NS_BINDING_ABORTED` 
- **Misleading symptom**: The "Audio format not supported" error was a red herring - the actual issue was the server returning JSON error instead of audio

### Implementation Details
- **Backend (`backend/routes/songs.py`)**:
  - Complete rewrite of `stream_song()` endpoint with secure path handling
  - Replaced inadequate `'..' in filename` check with proper `pathlib` resolution
  - Fixed the undefined variable by using `full_path.name` for the filename
  - Added comprehensive error handling and logging
  
- **Backend (`backend/main.py`)**:
  - Updated CORS middleware to use explicit allowed origins list
  - Restricted allowed methods to GET, POST, OPTIONS only

### Files Modified
- `backend/routes/songs.py`: Complete security rewrite of song streaming endpoint
- `backend/main.py`: Hardened CORS configuration

---

## [2025-08-30] - UI/UX Enhancements for Manual Review Interface

### Added
- **Review Interface Header**: Changed from "Your Generated Songs" to "Songs for Manual Review" for clarity
- **Batch Selection Operations**: 
  - Select All checkbox for bulk song selection
  - Bulk review status application (Pending, In Review, Approved, Rejected)
  - Visual selection indicator with blue highlight for selected songs
  - Selected count display showing number of songs selected
  
- **Enhanced Review Actions**:
  - Individual approve/reject/mark for review buttons on each song card
  - Quick action buttons with visual feedback (color changes on status)
  - Review notes textarea for optional reviewer comments per song
  - Persistent storage of review notes in localStorage
  
- **Improved Song Card Design**:
  - Selection checkbox integrated into song header
  - Review actions section separated with border
  - Status-based styling (selected songs have blue background)
  - Cleaner layout with better visual hierarchy

### Changed
- **Song State Management**: Extended to include `reviewNotes` and `isSelected` properties
- **localStorage Format**: Updated to store both review status and notes in structured format
- **Visual Feedback**: Added transition effects for smoother interactions

### Technical Implementation
- **Frontend (`frontend/app/components/DisplayGeneratedSongs.tsx`)**:
  - Added `toggleSongSelection()`, `toggleSelectAll()`, `applyBulkReviewStatus()` functions
  - Added `changeReviewNotes()` function for handling review comments
  - Extended `SongState` interface with new properties
  - Backward compatible localStorage handling for existing review data

### Files Modified
- `frontend/app/components/DisplayGeneratedSongs.tsx`: Complete UI/UX overhaul for manual review workflow

---

## [2025-08-30] - Frontend Data Flow Updates for Manual Review

### Changed
- **ModalSongs Component Data Flow**: Updated to use manual review API instead of public file fetching
  - Replaced `fetchSongFilesFromPublic` with `fetchManualReviewSongs` throughout component
  - Added state management for `ManualReviewResponse` data structure
  - Maintains backward compatibility by extracting filenames for existing functionality
  
### Added
- **Manual Review Data Integration**: 
  - Added `manualReviewData` state to store complete API response
  - Pass manual review data to `DisplayGeneratedSongs` component for enhanced review capabilities
  - Updated component props to support review-specific functionality

### Technical Implementation
- **Frontend (`frontend/app/components/ModalSongs.tsx`)**:
  - Import `fetchManualReviewSongs` and `ManualReviewResponse` type from API
  - Updated `loadInitialData()` to fetch and store manual review data
  - Updated `handleGenerateSong()` to refresh review data after workflow completion
  - Enhanced cleanup logic to clear review data on modal close
  
- **Frontend (`frontend/app/components/DisplayGeneratedSongs.tsx`)**:
  - Added optional `manualReviewData` prop to component interface
  - Prepared component for future review-specific features

### Files Modified
- `frontend/app/components/ModalSongs.tsx`: Replaced data fetching logic with manual review API
- `frontend/app/components/DisplayGeneratedSongs.tsx`: Extended props to accept manual review data

---

## [2025-08-30] - Manual Review API Enhancement

### Added
- **Manual Review Endpoint**: New `/api/songs/manual-review` endpoint for fetching songs from `backend/songs/final_review/` directory
  - Supports filtering by `bookName`, `chapter`, and `verseRange` parameters
  - Returns ALL matching independent songs for comprehensive review
  - Parses song filenames to extract metadata (index, timestamp, creation date)
  
- **Frontend API Integration**: New `fetchManualReviewSongs()` function in `frontend/app/lib/api.ts`
  - TypeScript interfaces for type-safe manual review operations
  - Comprehensive error handling and logging
  - Standardized response format matching backend structure

- **Filename Parsing Logic**: 
  - Song naming convention: `{slug_title}_index_{intIndex}_{timestamp}.mp3`
  - Slugification system for consistent matching (e.g., "Ruth 1:1-11" → "ruth-1-1-11")
  - Support for negative indices (independent songs) and positive indices

### Technical Implementation
- **Backend (`backend/api/song/routes.py`)**:
  - `slugify_text()`: Converts text to URL-safe slug format
  - `parse_song_filename()`: Extracts structured metadata from filenames
  - `manual_review_endpoint()`: Main endpoint with filtering and sorting logic
  
- **Frontend (`frontend/app/lib/api.ts`)**:
  - `ManualReviewRequest`, `ParsedSongInfo`, `ManualReviewSongFile`, `ManualReviewResponse` interfaces
  - Async function with proper error boundaries and logging

### Files Modified
- `backend/api/song/routes.py`: Added manual review endpoint and helper functions
- `frontend/app/lib/api.ts`: Added API integration function and TypeScript interfaces

---

## [2025-08-30] - pg1_id Tracking and Review Process Improvements

### Fixed
- **pg1_id extraction issue**: Fixed the workflow failing when `pg1_id` was not properly extracted from database response
- **Unnecessary retries**: Removed hard failure when `pg1_id` is missing, preventing unnecessary song regeneration
- **Review process blocking**: Added fallback review strategy when `pg1_id` is unavailable
- **IndentationError**: Fixed incorrect indentation in try-except block for database save operation

### Changed
- **URL behavior documentation**: Added extensive comments explaining that Suno.com no longer redirects to song page after creation (stays at `/create`)
- **Database response handling**: Enhanced to check both 'pg1_id' and 'id' column names in response
- **Error handling**: Changed from blocking errors to warnings with graceful fallbacks
- **Wait time**: Increased from 60 to 90 seconds for Suno processing (per user configuration)

### Added
- **Comprehensive debugging logs**: Added detailed logging throughout the workflow for better troubleshooting
  - Database operation logs with full response structure
  - pg1_id tracking through each workflow step
  - Clear labeling of expected vs unexpected behaviors
- **Temporary ID generation**: System now generates temporary IDs when Suno song ID cannot be extracted from URL
- **Fallback review mechanism**: Songs without `pg1_id` now use simplified review with manual review recommendation
- **Debug output categories**: Structured logging with [DEBUG], [INFO], [WARNING], [ERROR], [DATABASE] prefixes

### Technical Details
- **Root cause**: Suno.com's UI behavior changed - no longer redirects to individual song page after creation
- **Impact**: Cannot extract song ID from URL, affecting database tracking and AI review process
- **Solution**: Implemented multi-layer fallback system to ensure workflow continues despite missing IDs

### Files Modified
- `backend/api/orchestrator/utils.py`: Enhanced workflow error handling and debugging
- `backend/api/song/utils.py`: Improved song ID extraction and database save logging