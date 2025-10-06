# Changelog

## 2025-10-06
- **Added**: Published Docker backend image to Docker Hub as `vnmw7/suno-backend:latest`
  - Built complete backend container with Python 3.11, Camoufox browser, and all dependencies
  - Image size: 1.58GB with multi-stage build optimization
  - Includes health checks, proper volume mounting, and production-ready configuration
  - Users can now run backend via Docker: `docker run -d -p 8000:8000 vnmw7/suno-backend:latest`
  - Provides alternative to manual backend executable installation
- **Fixed**: Replaced failing aiohttp CDN download with Camoufox browser automation
  - Replaced `downloadSongsFromCdn` function in `backend/api/orchestrator/utils.py`
  - Removed aiohttp HTTP requests causing 403 Forbidden errors from CDN server
  - Implemented Camoufox browser automation to navigate directly to CDN URLs
  - Added multiple download strategies: automatic download, manual trigger, and direct content fetch fallbacks
  - Used proven `download.save_as()` pattern from existing codebase
  - Maintained same function signature and return format for API compatibility
  - Added proper browser headers and configuration to bypass CDN bot detection
  - Preserved all error handling and file verification logic
- **Fixed**: Resolved XPath selector strict mode violation in song generation automation
  - Updated song count detection selector from generic `//div[contains(text(), 'songs')]` to specific `//div[contains(@class, 'e1qr1dqp4')]//div[contains(text(), 'songs')]`
  - Applied fix to initial count detection, JavaScript wait expression, final count verification, and fallback verification
  - Eliminated conflicts between notification div and target song count div
  - Improved reliability of song generation workflow

## 2025-10-05
- Added side panel for song list on `/main` and removed the legacy `/songs` route.
- Updated the `/main` loader to fetch song metadata alongside Bible books for a unified page state.
- Restyled filter and song panels with the new neutral palette and three-column desktop layout.
- Simplified the `/main` header by removing the redundant link to `/songs`.
- Enabled manual review playback in the song sidebar with inline audio controls.
- Limited the song sidebar review panel to approve/regenerate toggles and playback speed adjustments.