feat: Enhance SunoDownloader with improved error handling and download retries

- Updated download_song_v2.py to include a retry mechanism for downloads, allowing up to 3 attempts on failure.
- Improved logging for download processes, including detailed messages for each step and error encountered.
- Enhanced song ID extraction logic to ensure accurate identification from song elements.
- Updated filename generation to include song ID and timestamp for better tracking.
- Adjusted navigation messages for clarity during the download process.