# Step 3: Component Enhancement - Detailed Breakdown

## Overview
This document breaks down the component enhancement tasks for `DisplayGeneratedSongs.tsx` into actionable sub-tasks.

## 3.1 Playback Speed Controls

### 3.1.1 Add Speed Control UI
- [ ] Create speed selector component (dropdown or button group)
- [ ] Add buttons for 1x, 2x, 3x speed options
- [ ] Style buttons to match existing UI theme
- [ ] Position controls near audio player

### 3.1.2 Implement Speed Functionality
- [ ] Add state management for current playback speed
- [ ] Implement `playbackRate` property on audio element
- [ ] Add event handlers for speed changes
- [ ] Ensure speed persists during playback

### 3.1.3 Visual Indicators
- [ ] Display current speed on/near player
- [ ] Highlight active speed button
- [ ] Add tooltip showing current speed
- [ ] Consider adding speed badge on audio waveform

### 3.1.4 Persistence
- [ ] Implement localStorage for speed preference
- [ ] Decide on per-song vs global preference
- [ ] Add logic to restore speed on component mount
- [ ] Handle preference migration/versioning

## 3.2 Enhanced Audio Player Features

### 3.2.1 Keyboard Shortcuts
- [ ] Implement Space bar for play/pause
- [ ] Add Left/Right arrow keys for seek (5s or 10s)
- [ ] Add Up/Down arrows for volume control
- [ ] Add number keys (1,2,3) for speed control
- [ ] Create keyboard shortcut help tooltip

### 3.2.2 Progress Bar Enhancement
- [ ] Create custom progress bar component
- [ ] Implement click-to-seek functionality
- [ ] Add hover preview of time position
- [ ] Show buffered range indicator
- [ ] Add time labels (current/total)

### 3.2.3 Volume Control
- [ ] Add volume slider component
- [ ] Implement mute/unmute toggle
- [ ] Store volume preference in localStorage
- [ ] Add volume percentage display
- [ ] Consider keyboard shortcuts for volume

### 3.2.4 Loop Functionality
- [ ] Add loop toggle button
- [ ] Implement loop logic in audio player
- [ ] Visual indicator when loop is active
- [ ] Per-song loop preference

### 3.2.5 Individual Song Controls
- [ ] Ensure each song player is independent
- [ ] Prevent multiple songs playing simultaneously (optional)
- [ ] Add "Stop All" button if multiple can play
- [ ] Independent volume/speed per song

## 3.3 Multiple Independent Songs Display

### 3.3.1 Grouping Logic
- [ ] Parse verse reference (e.g., "ruth-1-1-11")
- [ ] Group songs by verse reference
- [ ] Create collapsible sections per verse
- [ ] Add verse reference as section header

### 3.3.2 Song Identification
- [ ] Display song index numbers clearly
- [ ] Format and display creation timestamps
- [ ] Create unique identifier display (e.g., "Song #2 - 2:30 PM")
- [ ] Add copy-to-clipboard for song ID

### 3.3.3 Timestamp Sorting
- [ ] Parse creation timestamps from data
- [ ] Implement sort by newest first
- [ ] Add sort toggle (newest/oldest)
- [ ] Display relative time (e.g., "2 hours ago")

### 3.3.4 Individual Review Interface
- [ ] Remove comparison UI elements
- [ ] Add individual review buttons per song
- [ ] Implement single-song review workflow
- [ ] Clear indication of which song is being reviewed

## 3.4 Review Status Tracking

### 3.4.1 Status Indicators
- [ ] Define status states: Pending, In Review, Approved, Rejected
- [ ] Create status badge component
- [ ] Color-code status indicators
- [ ] Add status icons for quick recognition

### 3.4.2 Review Actions
- [ ] Add "Start Review" button
- [ ] Implement "Approve" action
- [ ] Implement "Reject" action with reason
- [ ] Add "Request Changes" option
- [ ] Include review notes/comments field

### 3.4.3 Status Persistence
- [ ] Design review status data structure
- [ ] Implement backend API for status updates
- [ ] Add optimistic UI updates
- [ ] Handle offline/sync scenarios

### 3.4.4 Review History
- [ ] Track who reviewed and when
- [ ] Store review comments/reasons
- [ ] Display review history timeline
- [ ] Allow re-review if needed

## Implementation Priority

### Phase 1 (Core Functionality)
1. Playback speed controls (3.1.1, 3.1.2)
2. Basic keyboard shortcuts (3.2.1 - Space bar only)
3. Individual song controls (3.2.5)

### Phase 2 (Enhanced UX)
1. Progress bar with seek (3.2.2)
2. Volume control (3.2.3)
3. Visual indicators for speed (3.1.3)
4. Song grouping and display (3.3.1, 3.3.2)

### Phase 3 (Review Features)
1. Review status indicators (3.4.1)
2. Review actions (3.4.2)
3. Status persistence (3.4.3)

### Phase 4 (Polish)
1. All keyboard shortcuts (3.2.1)
2. Loop functionality (3.2.4)
3. Speed persistence (3.1.4)
4. Review history (3.4.4)
5. Timestamp sorting options (3.3.3)

## Testing Checklist

### Unit Tests
- [ ] Speed control state management
- [ ] Keyboard event handlers
- [ ] Volume control logic
- [ ] Song grouping algorithm
- [ ] Review status transitions

### Integration Tests
- [ ] Audio playback at different speeds
- [ ] Seek functionality accuracy
- [ ] Multiple song players independence
- [ ] Review workflow end-to-end
- [ ] Data persistence and retrieval

### User Acceptance Tests
- [ ] Speed controls are intuitive
- [ ] Keyboard shortcuts work as expected
- [ ] Songs display clearly with identifiers
- [ ] Review process is straightforward
- [ ] Performance with multiple songs

## Dependencies and Considerations

### Technical Dependencies
- Audio API browser compatibility
- LocalStorage availability
- Backend API for review status
- React state management approach

### UX Considerations
- Mobile responsiveness
- Accessibility (ARIA labels, keyboard nav)
- Loading states for audio
- Error handling for failed audio loads
- Performance with many songs

### Design Decisions Needed
- Maximum number of songs displayed
- Auto-pause when starting another song?
- Default playback speed
- Review status colors/icons
- Keyboard shortcut conflicts