# Suno Automation Changelogs

## 2025-09-08

### Enhanced Song Download Naming Convention
- **Changed**: Updated `download_song_v2.py` to use song ID in downloaded filenames instead of index
- **Before**: Files were named as `{title}_index_{index}_{timestamp}.mp3`
- **After**: Files are now named as `{title}_{songId}_{timestamp}.mp3`
- **Features**:
  - Automatically extracts song ID from song elements when downloading from `/me` page
  - Falls back to index-based naming if song ID cannot be extracted
  - Direct song page downloads use the provided song ID
- **Example**: 
  - Old: `string_index_0_20250909053053.mp3`
  - New: `string_abc123def456_20250909053053.mp3`