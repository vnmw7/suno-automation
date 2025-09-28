# Test Plan for Reject Button Functionality

## Implementation Summary
The reject button in DisplayGeneratedSongs component has been updated to:
1. Call the backend delete API when a song is rejected
2. Show a confirmation dialog before deletion
3. Delete the song from both local storage and Suno.com
4. Remove the song from the UI after successful deletion

## Files Modified
1. `frontend/app/lib/api.ts` - Added `deleteSong` function
2. `frontend/app/components/DisplayGeneratedSongs.tsx` - Updated reject button handler

## Test Steps
1. Start the backend server: `cd backend && python main.py`
2. Start the frontend: `cd frontend && npm run dev`
3. Navigate to a book/chapter with existing songs
4. Click on a song's reject button
5. Verify confirmation dialog appears
6. Click "Delete Song" to confirm
7. Verify the song is removed from the UI
8. Check backend logs to confirm deletion from both local and Suno

## Key Features
- Extracts song_id from filename pattern: `{title}_{song_id}_{timestamp}.mp3`
- Uses file path from manualReviewData for accurate file deletion
- Always deletes from both local storage AND Suno.com (no toggle option)
- Shows loading state during deletion
- Displays error messages if deletion fails

## Backend Endpoints Used
- `POST /api/v1/song/delete` with parameters:
  - `song_id`: Extracted from filename
  - `file_path`: From manualReviewData
  - `delete_from_suno`: Always true