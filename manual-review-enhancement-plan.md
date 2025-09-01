# Manual Review Enhancement Plan

## Overview
Enhance the song manual review system to fetch songs from the backend's `final_review` directory and add playback speed options (2x, 3x) for efficient review.

## Current State Analysis
- Songs are currently fetched from `/songs` public directory via `fetchSongFilesFromPublic` API
- `DisplayGeneratedSongs` component shows basic audio player with standard controls
- Manual review happens in `backend/songs/final_review/` directory
- No playback speed controls for faster review

## Proposed Changes

### 1. Backend API Enhancement
**File**: `backend/api/song/routes.py` (or create new endpoint)

**New Endpoint**: `/api/songs/manual-review`
- **Purpose**: Fetch songs from `backend/songs/final_review/` directory
- **Song Naming Convention**: `{slug_title}_index_{intIndex}_{timestamp}.mp3`
  - Example: `amazing-grace-verse-1-5_index_-1_20250830143022.mp3`
  - `slug_title`: Slugified title (special chars removed, spaces->hyphens, lowercase)
  - `intIndex`: Song index number
  - `timestamp`: YYYYMMDDHHMMSS format
- **Filtering Logic**: 
  - Parse filename to extract title components
  - Match against `bookName`, `chapter`, `verseRange` by:
    - Converting request params to slugified format: `{bookName}-{chapter}-{verseRange}`
    - Match ALL songs with the same title slug (display all independent songs)
    - Example: Frontend sends `bookName="Ruth"`, `chapter=1`, `verseRange="1-11"`
    - Backend creates search pattern: `ruth-1-1-11_index_`
    - Returns ALL files matching: 
      - `ruth-1-1-11_index_-1_20250830143022.mp3` (independent song #1)
      - `ruth-1-1-11_index_-2_20250830115445.mp3` (independent song #2)
      - `ruth-1-1-11_index_0_20250830120030.mp3` (independent song #3)
      - etc.
  - **Purpose**: Display all independent songs for the same verse range for comprehensive review
- **Parameters**: 
  - `bookName` (string) - will be slugified for matching
  - `chapter` (number) - included in slug matching
  - `verseRange` (string) - included in slug matching
- **Response**: List of ALL matching song files with parsed metadata
  ```json
  {
    "files": [
      {
        "filename": "ruth-1-1-11_index_-2_20250830115445.mp3",
        "parsed": {
          "title_slug": "ruth-1-1-11",
          "index": -2,
          "timestamp": "20250830115445",
          "created_date": "2025-08-30 11:54:45"
        },
        "path": "/songs/ruth-1-1-11_index_-2_20250830115445.mp3"
      },
      {
        "filename": "ruth-1-1-11_index_-1_20250830143022.mp3",
        "parsed": {
          "title_slug": "ruth-1-1-11",
          "index": -1,
          "timestamp": "20250830143022",
          "created_date": "2025-08-30 14:30:22"
        },
        "path": "/songs/ruth-1-1-11_index_-1_20250830143022.mp3"
      },
      {
        "filename": "ruth-1-1-11_index_0_20250830120030.mp3",
        "parsed": {
          "title_slug": "ruth-1-1-11",
          "index": 0,
          "timestamp": "20250830120030",
          "created_date": "2025-08-30 12:00:30"
        },
        "path": "/songs/ruth-1-1-11_index_0_20250830120030.mp3"
      }
    ],
    "total_songs": 3,
    "verse_reference": "Ruth 1:1-11"
  }
  ```
- **Security**: Validate file paths and sanitize slugified inputs

### 2. Frontend API Integration
**File**: `frontend/app/lib/api.ts`

**New Function**: `fetchManualReviewSongs(bookName, chapter, verseRange)`
- Call the new backend endpoint
- Return standardized response format
- Handle errors appropriately

### 3. Component Enhancement
**File**: `frontend/app/components/DisplayGeneratedSongs.tsx`

#### 3.1 Playback Speed Controls
- Add speed control buttons (1x, 2x, 3x)
- Implement `playbackRate` property on audio element
- Add visual indicators for current playback speed
- Persist speed preference per song or globally

#### 3.2 Enhanced Audio Player
```tsx
// New features to add:
- Playback speed selector (1x, 2x, 3x)
- Current speed indicator
- Keyboard shortcuts (Space, Arrow keys)
- Progress bar with click-to-seek
- Volume control
- Loop option for repeated listening
- Individual song controls (each song is independent)
```

#### 3.3 Multiple Independent Songs Display
- **Grouped by Verse Reference**: All independent songs for "ruth-1-1-11" displayed together
- **Song Identifiers**: Show index numbers and timestamps (e.g., "Song Index -2 (11:54 AM)", "Song Index -1 (2:30 PM)")
- **Timestamp Sorting**: Order by creation time (newest first)
- **Individual Review**: Each song reviewed independently (no comparison needed)

#### 3.3 Review Status Tracking
- Add review status indicators (Pending, In Review, Approved, Rejected)
- Allow marking songs for different review outcomes
- Save review decisions locally or to backend

### 4. Data Flow Updates
**File**: `frontend/app/components/ModalSongs.tsx`

- Replace `fetchSongFilesFromPublic` with `fetchManualReviewSongs`
- Pass additional props for review functionality
- Handle manual review specific state management

### 5. UI/UX Enhancements

#### 5.1 Review Interface
- **Header**: "Songs for Manual Review" instead of "Your Generated Songs"
- **Song Cards**: Enhanced with review actions
- **Batch Operations**: Select multiple songs for bulk actions
- **Review Notes**: Optional text area for reviewer comments

#### 5.2 Playback Speed UI
```
┌─────────────────────────────────────┐
│ Ruth 1:1-11 - Index -2 (11:54 AM)   │
├─────────────────────────────────────┤
│ [▶] ████████░░░░ 2:30 / 4:15        │
│ Speed: [1x] [2x] [3x]    Vol: ▊▊▊▊░ │
├─────────────────────────────────────┤
│ Review: [✓ Approve] [✗ Reject] [?]  │
│ Notes: [___________________]         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Ruth 1:1-11 - Index -1 (2:30 PM)    │
├─────────────────────────────────────┤
│ [▶] ████████░░░░ 1:45 / 3:22        │
│ Speed: [1x] [2x] [3x]    Vol: ▊▊▊▊░ │
├─────────────────────────────────────┤
│ Review: [✓ Approve] [✗ Reject] [?]  │
│ Notes: [___________________]         │
└─────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Backend API
1. Create `/api/songs/manual-review` endpoint
2. Implement file listing from `final_review` directory
3. Add proper error handling and validation
4. Test with existing songs in final_review

### Phase 2: Frontend API Integration
1. Add `fetchManualReviewSongs` to `api.ts`
2. Update TypeScript interfaces for manual review data
3. Test API integration

### Phase 3: Enhanced Audio Player
1. Add playback speed controls to `DisplayGeneratedSongs`
2. Implement speed change functionality
3. Add visual feedback for current speed
4. Test cross-browser compatibility

### Phase 4: Review Interface
1. Add review status indicators
2. Implement review action buttons
3. Add notes/comments functionality
4. Connect to backend for saving review decisions

### Phase 5: Integration & Polish
1. Update `ModalSongs` to use manual review API
2. Add loading states and error handling
3. Implement keyboard shortcuts
4. Add responsive design improvements
5. User testing and feedback

## Technical Considerations

### Security
- Validate file paths in backend to prevent directory traversal
- Sanitize user input for review notes
- Implement proper authentication for review actions

### Performance
- Lazy load audio files to improve page load times
- Cache playback speed preferences
- Optimize for large numbers of songs

### Browser Compatibility
- Test playback speed controls across browsers
- Fallback for browsers that don't support `playbackRate`
- Ensure audio formats are widely supported

### Error Handling
- Handle missing files gracefully
- Provide clear error messages for network issues
- Implement retry mechanisms for failed requests

## Files to Modify/Create

### Backend
- `backend/api/song/routes.py` - Add manual review endpoint
- `backend/api/song/utils.py` - Add helper functions for file operations

### Frontend
- `frontend/app/lib/api.ts` - Add manual review API calls
- `frontend/app/components/DisplayGeneratedSongs.tsx` - Enhanced player
- `frontend/app/components/ModalSongs.tsx` - Integration updates
- `frontend/app/types/` - Add TypeScript interfaces

### Configuration
- Update API documentation
- Add environment variables if needed

## Success Criteria
1. ✅ Songs from `final_review` directory are displayed in UI
2. ✅ Playback speed controls (2x, 3x) work reliably
3. ✅ Review interface allows efficient song evaluation
4. ✅ No performance degradation with multiple songs
5. ✅ Cross-browser compatibility maintained
6. ✅ Error handling provides clear user feedback

## Future Enhancements
- Waveform visualization for detailed audio analysis
- A/B comparison between original and generated songs
- Batch export of approved songs
- Integration with external review tools
- Analytics on review patterns and efficiency