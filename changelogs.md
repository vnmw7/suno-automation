# Suno Automation Changelogs

## 2025-09-13

### Integrated V2 Downloader into Orchestrator Workflow
- **Changed**: Updated orchestrator's `utils.py` to use the enhanced V2 downloader
- **Replaced**: Switched from `download_song_handler` to `download_song_v2` for improved reliability
- **Added**: Full `song_id` parameter support throughout the workflow
- **Features**:
  - Direct navigation to song page using `song_id` when available
  - Passes `song_id` from generation result to download function
  - Enhanced error handling and element detection with "teleport" techniques
  - Better filename generation including song ID and timestamp
  - Maintains backward compatibility with title-based search as fallback
- **Benefits**:
  - Faster downloads by navigating directly to `/song/{song_id}` page
  - More reliable element detection and interaction
  - Reduced errors from duplicate titles or indexing issues
  - Improved tracking with unique song identifiers in filenames
- **Files Modified**:
  - `backend/api/orchestrator/utils.py`: Updated `download_both_songs()` function
  - Import changed from `..song.utils` to `utils.download_song_v2`

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