# Changelog

All notable changes to the Suno Automation project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Song File Naming Convention** - Standardized to use song_id format exclusively
  - Updated CLAUDE.md with explicit naming format: `{slug_title}_{song_id}_{timestamp}.mp3`
  - Removed support for index-based naming pattern
  - All song operations now expect UUID-based filenames

### Added
- **Standalone Executable Distribution** - Backend can now be bundled as a Windows executable using PyInstaller
  - Created `main.spec` configuration for PyInstaller bundling
  - Added `build.bat` script for automated building process
  - Implemented runtime hooks for Camoufox browser initialization
  - Added custom hooks for browserforge and language_tags data files
  - Created distribution documentation in `DISTRIBUTION_README.md`
  - Executable includes all Python dependencies, no Python installation required on target machines
  - Camoufox browser downloads automatically on first use (internet required once)
  - Distribution size: ~60MB (without browser), ~150MB (with browser)

### Fixed
- **Manual Review Songs Display Issue** - Fixed songs not appearing in frontend modal
  - Corrected path resolution in `manual_review_endpoint` from `backend/songs/final_review` to `songs/final_review`
  - Updated `parse_song_filename` function to handle UUID-based naming format: `{slug_title}_{song_id}_{timestamp}.mp3`
  - Removed index-based sorting logic, now sorts by timestamp
  - Songs in `backend/songs/final_review` now correctly display in Isaiah modal
- Resolved missing data files issue for browserforge package in PyInstaller bundle
- Fixed language_tags data files not being included in distribution
- Corrected runtime path resolution for bundled executable environment

### Technical Details
- PyInstaller configuration properly handles:
  - All FastAPI routes and middleware
  - Uvicorn server components
  - Camoufox browser automation
  - Environment variables and configuration files
  - Session data persistence
  - Logging infrastructure

## [Previous Versions]

### Song Management Features
- Song download functionality with Camoufox integration
- Song deletion API endpoints (local and remote)
- Enhanced error handling and teleport techniques
- Improved song ID extraction logic
- Reduced wait time for Suno processing

### API Endpoints
- `/` - Health check endpoint
- `/login` - Suno authentication
- `/login/microsoft` - Microsoft authentication
- `/debug/song-structures` - Debug endpoint for song structures
- Song management routes via song_router
- AI review routes via ai_review_router
- AI generation routes via ai_generation_router
- Orchestrator routes via orchestrator_router

### Dependencies
- FastAPI with CORS middleware
- Camoufox for browser automation
- Supabase for database operations
- Various AI and automation libraries