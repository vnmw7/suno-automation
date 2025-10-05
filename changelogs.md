# Changelog

## 2025-10-06
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