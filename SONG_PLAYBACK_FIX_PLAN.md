# Song Playback Fix Plan - NS_BINDING_ABORTED Error

## Problem Analysis

### Current Issue
- **Error**: `NS_BINDING_ABORTED` when trying to play songs
- **URL**: `http://localhost:5173/songs/ruth-1-1-11_index_-2_20250830115445.mp3`
- **Component**: `DisplayGeneratedSongs.tsx`
- **Line**: Audio source set at line 654

### Root Causes
1. **Static File Serving**: The frontend dev server (Vite on port 5173) may not be configured to serve static files from `/songs` directory
2. **File Path Mismatch**: Songs might be stored in backend but frontend is trying to access them directly
3. **CORS Issues**: If songs are served from different origin
4. **Missing Middleware**: No static file serving middleware configured

## Solution Architecture

### Option 1: Backend API Endpoint (Recommended)
Create a dedicated API endpoint to stream audio files from backend to frontend.

**Pros:**
- Centralized file access control
- Better security (can add authentication)
- Works across different environments
- No CORS issues

**Cons:**
- Slightly more complex implementation
- Additional backend load

### Option 2: Static File Serving via Frontend
Configure Vite to serve files from a public directory.

**Pros:**
- Simple implementation
- Direct file access
- Better performance (no backend proxy)

**Cons:**
- Files must be in frontend directory
- Less secure
- Environment-specific configuration

### Option 3: Proxy Configuration
Configure Vite proxy to forward `/songs` requests to backend.

**Pros:**
- Minimal code changes
- Uses existing file structure
- Development-friendly

**Cons:**
- Requires production setup separately
- Proxy configuration complexity

## Implementation Plan

### Phase 1: Backend API Endpoint (Recommended Solution)

#### 1.1 Create Audio Streaming Endpoint
**File**: `backend/routes/songs.py` (new)
- Create GET endpoint: `/api/songs/:filename`
- Implement file streaming with proper headers
- Add error handling for missing files
- Set correct MIME type (`audio/mpeg`)

#### 1.2 Update Frontend Audio Source
**File**: `frontend/app/components/DisplayGeneratedSongs.tsx`
- Change line 654 from: `${SONG_DIRECTORY}/${encodeURIComponent(song.fileName)}`
- To: `${API_BASE_URL}/api/songs/${encodeURIComponent(song.fileName)}`
- Update SONG_DIRECTORY constant or create new API_SONGS_URL

#### 1.3 Add Backend Route Registration
**File**: `backend/main.py`
- Import and register the new songs blueprint
- Ensure proper route mounting

### Phase 2: Vite Proxy Configuration (Alternative/Additional)

#### 2.1 Configure Vite Proxy
**File**: `frontend/vite.config.ts`
```javascript
proxy: {
  '/songs': {
    target: 'http://localhost:5000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/songs/, '/api/songs')
  }
}
```

### Phase 3: Error Handling & Validation

#### 3.1 Add Loading States
- Show loading indicator while fetching audio
- Handle network errors gracefully
- Add retry mechanism for failed loads

#### 3.2 Validate File Existence
- Check if file exists before setting audio source
- Provide user feedback for missing files
- Log errors for debugging

### Phase 4: Testing & Verification

#### 4.1 Test Cases
1. Verify songs play correctly
2. Test with different file names (special characters)
3. Check error handling for missing files
4. Validate CORS headers if needed
5. Test in different browsers

#### 4.2 Performance Testing
- Monitor network requests
- Check audio buffering
- Validate streaming efficiency

## File Changes Summary

### Backend Changes
1. **New File**: `backend/routes/songs.py`
   - Audio streaming endpoint
   - File validation
   - Proper headers

2. **Modified**: `backend/main.py`
   - Register songs blueprint
   - Add route mounting

### Frontend Changes
1. **Modified**: `frontend/app/components/DisplayGeneratedSongs.tsx`
   - Update audio source URL (line 654)
   - Add error handling
   - Update constants

2. **Modified**: `frontend/app/lib/api.ts`
   - Add songs API endpoint constant
   - Add helper function for song URLs

3. **Optional**: `frontend/vite.config.ts`
   - Add proxy configuration

## Environment Variables
```env
# Backend
SONGS_DIRECTORY=./songs

# Frontend
VITE_API_BASE_URL=http://localhost:5000
```

## Security Considerations
1. Validate file names to prevent directory traversal
2. Restrict file types to audio only
3. Add rate limiting for streaming endpoint
4. Consider authentication for production

## Rollback Plan
If issues persist:
1. Revert frontend changes
2. Remove new backend endpoint
3. Investigate alternative storage solutions (CDN, S3)

## Success Criteria
- [ ] Songs play without NS_BINDING_ABORTED error
- [ ] Audio controls work (play, pause, seek)
- [ ] No CORS errors in console
- [ ] Files stream efficiently
- [ ] Error handling for missing files
- [ ] Works in Chrome, Firefox, Safari, Edge

## Timeline
- **Immediate Fix**: 30 minutes (Backend API endpoint)
- **Full Implementation**: 1-2 hours (with testing)
- **Production Ready**: 2-3 hours (with security & optimization)