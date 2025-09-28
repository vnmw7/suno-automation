import React, { useState, useRef, useEffect, useCallback } from 'react';
import { API_SONGS_URL, deleteSong } from '../lib/api';
import type { ManualReviewResponse } from '../lib/api';

interface Song {
  fileName: string;
  timestamp?: string;
  index?: number;
  verseReference?: string;
}

interface DisplayGeneratedSongsProps {
  stepCompleted: { song: boolean };
  songFiles: string[];
  isFetchingSongFiles: boolean;
  fetchSongFilesError: string | null;
  manualReviewData?: ManualReviewResponse | null;
}

interface SongState {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  isLooping: boolean;
  playbackSpeed: PlaybackSpeed;
  reviewStatus: ReviewStatus;
  reviewNotes: string;
  isSelected: boolean;
  loadError?: string;
  isLoading?: boolean;
}

type ReviewStatus = 'pending' | 'in_review' | 'approved' | 'rejected';
type PlaybackSpeed = 0.25 | 0.5 | 0.75 | 1 | 1.25 | 1.5 | 1.75 | 2 | 2.25 | 2.5 | 2.75 | 3;

const PLAYBACK_SPEEDS: PlaybackSpeed[] = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3];

const DisplayGeneratedSongs = ({
  stepCompleted,
  songFiles,
  isFetchingSongFiles,
  fetchSongFilesError,
  manualReviewData,
}: DisplayGeneratedSongsProps) => {
  // Create a mapping of filenames to their full paths
  const filePathMap = React.useMemo(() => {
    const map = new Map<string, string>();
    if (manualReviewData?.files) {
      console.log('[DisplayGeneratedSongs] Building file path map from manual review data:', manualReviewData.files);
      manualReviewData.files.forEach(file => {
        // Use the path from backend which includes the subdirectory
        map.set(file.filename, file.path);
        console.log(`[DisplayGeneratedSongs] Mapped ${file.filename} -> ${file.path}`);
      });
    } else {
      console.log('[DisplayGeneratedSongs] No manual review data available for path mapping');
    }
    return map;
  }, [manualReviewData]);
  
  const audioRefs = useRef<{ [key: string]: HTMLAudioElement | null }>({});
  const progressRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  
  const [songStates, setSongStates] = useState<{ [key: string]: SongState }>({});
  const [globalPlaybackSpeed, setGlobalPlaybackSpeed] = useState<PlaybackSpeed>(1);
  const [useGlobalSpeed, setUseGlobalSpeed] = useState(true);
  const [debugMode, setDebugMode] = useState(false); // Toggle with Ctrl+Shift+D
  const [selectAllChecked, setSelectAllChecked] = useState(false);
  const [bulkReviewStatus, setBulkReviewStatus] = useState<ReviewStatus>('pending');
  const [deleteConfirmation, setDeleteConfirmation] = useState<{ show: boolean; fileName: string | null }>({
    show: false,
    fileName: null
  });
  const [isDeleting, setIsDeleting] = useState(false);

  // Parse song metadata from filename
  const parseSongMetadata = (fileName: string): Song => {
    const match = fileName.match(/(.+?)_index(-?\d+)_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})/);
    if (match) {
      const [, verseRef, index, timestamp] = match;
      const formattedTime = new Date(timestamp.replace(/_/g, ' ')).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      });
      return {
        fileName,
        verseReference: verseRef.replace(/_/g, ' '),
        index: parseInt(index),
        timestamp: formattedTime,
      };
    }
    return { fileName };
  };

  // Group songs by verse reference
  const groupSongsByVerse = (files: string[]): Map<string, Song[]> => {
    const grouped = new Map<string, Song[]>();
    
    files.forEach(file => {
      const song = parseSongMetadata(file);
      const key = song.verseReference || 'ungrouped';
      
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)!.push(song);
    });

    // Sort songs within each group by timestamp (newest first)
    grouped.forEach((songs) => {
      songs.sort((a, b) => {
        if (a.index !== undefined && b.index !== undefined) {
          return b.index - a.index; // Higher index (newer) first
        }
        return 0;
      });
    });

    return grouped;
  };

  // Initialize song states
  useEffect(() => {
    const initialStates: { [key: string]: SongState } = {};
    songFiles.forEach(file => {
      if (!songStates[file]) {
        initialStates[file] = {
          isPlaying: false,
          currentTime: 0,
          duration: 0,
          volume: 1,
          isLooping: false,
          playbackSpeed: globalPlaybackSpeed,
          reviewStatus: 'pending',
          reviewNotes: '',
          isSelected: false,
        };
      }
    });
    
    if (Object.keys(initialStates).length > 0) {
      setSongStates(prev => ({ ...prev, ...initialStates }));
    }
  }, [songFiles, globalPlaybackSpeed, songStates]);

  // Handle play/pause
  const togglePlayPause = useCallback(async (fileName: string) => {
    console.log(`[DisplayGeneratedSongs] Toggle play/pause for: ${fileName}`);
    const audio = audioRefs.current[fileName];
    if (!audio) {
      console.error(`[DisplayGeneratedSongs] No audio element found for: ${fileName}`);
      return;
    }

    // Check if there's a load error
    if (songStates[fileName]?.loadError) {
      console.error(`[DisplayGeneratedSongs] Cannot play song with load error: ${fileName}`, songStates[fileName].loadError);
      return;
    }

    if (songStates[fileName]?.isPlaying) {
      console.log(`[DisplayGeneratedSongs] Pausing: ${fileName}`);
      audio.pause();
    } else {
      console.log(`[DisplayGeneratedSongs] Playing: ${fileName}`);
      // Pause all other songs
      Object.keys(audioRefs.current).forEach(key => {
        if (key !== fileName && audioRefs.current[key]) {
          audioRefs.current[key]!.pause();
        }
      });
      
      try {
        // Set loading state
        setSongStates(prev => ({
          ...prev,
          [fileName]: {
            ...prev[fileName],
            isLoading: true,
            loadError: undefined,
          },
        }));
        
        await audio.play();
        console.log(`[DisplayGeneratedSongs] Successfully started playback: ${fileName}`);
      } catch (error) {
        console.error(`[DisplayGeneratedSongs] Failed to play: ${fileName}`, error);
        setSongStates(prev => ({
          ...prev,
          [fileName]: {
            ...prev[fileName],
            isPlaying: false,
            isLoading: false,
            loadError: error instanceof Error ? error.message : 'Failed to play audio',
          },
        }));
      }
    }

    setSongStates(prev => ({
      ...prev,
      [fileName]: {
        ...prev[fileName],
        isPlaying: !prev[fileName]?.isPlaying,
      },
    }));
  }, [songStates]);

  // Handle playback speed change
  const changePlaybackSpeed = useCallback((fileName: string, speed: PlaybackSpeed) => {
    const audio = audioRefs.current[fileName];
    if (audio) {
      audio.playbackRate = speed;
    }
    
    setSongStates(prev => ({
      ...prev,
      [fileName]: {
        ...prev[fileName],
        playbackSpeed: speed,
      },
    }));
  }, []);

  // Handle global speed change
  const changeGlobalSpeed = useCallback((speed: PlaybackSpeed) => {
    setGlobalPlaybackSpeed(speed);
    
    if (useGlobalSpeed) {
      Object.keys(audioRefs.current).forEach(fileName => {
        changePlaybackSpeed(fileName, speed);
      });
    }
  }, [useGlobalSpeed, changePlaybackSpeed]);

  // Handle seek
  const handleSeek = useCallback((fileName: string, event: React.MouseEvent<HTMLDivElement> | React.KeyboardEvent<HTMLDivElement>) => {
    const audio = audioRefs.current[fileName];
    const progressBar = progressRefs.current[fileName];
    if (!audio || !progressBar) return;

    // Only handle mouse events for actual seeking
    if ('clientX' in event) {
      const rect = progressBar.getBoundingClientRect();
      const percent = (event.clientX - rect.left) / rect.width;
      const newTime = percent * audio.duration;
      
      audio.currentTime = newTime;
      setSongStates(prev => ({
        ...prev,
        [fileName]: {
          ...prev[fileName],
          currentTime: newTime,
        },
      }));
    }
  }, []);

  // Handle volume change
  const changeVolume = useCallback((fileName: string, volume: number) => {
    const audio = audioRefs.current[fileName];
    if (audio) {
      audio.volume = volume;
    }
    
    setSongStates(prev => ({
      ...prev,
      [fileName]: {
        ...prev[fileName],
        volume,
      },
    }));
  }, []);

  // Handle loop toggle
  const toggleLoop = useCallback((fileName: string) => {
    const audio = audioRefs.current[fileName];
    if (audio) {
      audio.loop = !audio.loop;
    }
    
    setSongStates(prev => ({
      ...prev,
      [fileName]: {
        ...prev[fileName],
        isLooping: !prev[fileName]?.isLooping,
      },
    }));
  }, []);

  // Extract song ID from filename
  const extractSongId = (fileName: string): string | null => {
    // Pattern: {title}_{song_id}_{timestamp}.mp3
    // Example: isaiah-1-1-10_0536dd17-8cfd-4bca-9fd7-831621daac10_20250913152839.mp3
    const match = fileName.match(/[^_]+_([a-f0-9-]{36})_\d+\.mp3/i);
    return match ? match[1] : null;
  };

  // Handle song deletion
  const handleDeleteSong = useCallback(async (fileName: string) => {
    setIsDeleting(true);

    try {
      // Extract song ID from filename
      const songId = extractSongId(fileName);

      // Get the full file path from manualReviewData
      const filePath = filePathMap.get(fileName);

      console.log(`[DisplayGeneratedSongs] Deleting song - fileName: ${fileName}, songId: ${songId}, filePath: ${filePath}`);

      // Call the delete API
      const result = await deleteSong(songId || undefined, filePath || undefined);

      if (result.success) {
        console.log(`[DisplayGeneratedSongs] Song deleted successfully: ${fileName}`);

        // Remove the song from the UI
        setSongStates(prev => {
          const newStates = { ...prev };
          delete newStates[fileName];
          return newStates;
        });

        // Also remove from localStorage
        const reviewData = JSON.parse(localStorage.getItem('songReviews') || '{}');
        delete reviewData[fileName];
        localStorage.setItem('songReviews', JSON.stringify(reviewData));

        // Show success message (you could add a toast notification here)
        alert(`Song deleted successfully from both local storage and Suno.com`);
      } else {
        console.error(`[DisplayGeneratedSongs] Failed to delete song: ${fileName}`, result.errors);
        alert(`Failed to delete song: ${result.errors.join(', ')}`);
      }
    } catch (error) {
      console.error(`[DisplayGeneratedSongs] Error deleting song: ${fileName}`, error);
      alert(`Error deleting song: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsDeleting(false);
      setDeleteConfirmation({ show: false, fileName: null });
    }
  }, [filePathMap]);

  // Handle review status change
  const changeReviewStatus = useCallback((fileName: string, status: ReviewStatus) => {
    // If status is rejected, show confirmation dialog
    if (status === 'rejected') {
      setDeleteConfirmation({ show: true, fileName });
      return;
    }

    setSongStates(prev => ({
      ...prev,
      [fileName]: {
        ...prev[fileName],
        reviewStatus: status,
      },
    }));

    // Save to localStorage for persistence
    const reviewData = JSON.parse(localStorage.getItem('songReviews') || '{}');
    if (!reviewData[fileName]) reviewData[fileName] = {};
    reviewData[fileName].status = status;
    localStorage.setItem('songReviews', JSON.stringify(reviewData));
  }, []);

  // Handle review notes change
  const changeReviewNotes = useCallback((fileName: string, notes: string) => {
    setSongStates(prev => ({
      ...prev,
      [fileName]: {
        ...prev[fileName],
        reviewNotes: notes,
      },
    }));
    
    // Save to localStorage for persistence
    const reviewData = JSON.parse(localStorage.getItem('songReviews') || '{}');
    if (!reviewData[fileName]) reviewData[fileName] = {};
    reviewData[fileName].notes = notes;
    localStorage.setItem('songReviews', JSON.stringify(reviewData));
  }, []);

  // Handle song selection
  const toggleSongSelection = useCallback((fileName: string) => {
    setSongStates(prev => ({
      ...prev,
      [fileName]: {
        ...prev[fileName],
        isSelected: !prev[fileName]?.isSelected,
      },
    }));
  }, []);

  // Handle select all toggle
  const toggleSelectAll = useCallback(() => {
    const newSelectState = !selectAllChecked;
    setSelectAllChecked(newSelectState);
    
    setSongStates(prev => {
      const updated = { ...prev };
      songFiles.forEach(fileName => {
        if (updated[fileName]) {
          updated[fileName].isSelected = newSelectState;
        }
      });
      return updated;
    });
  }, [selectAllChecked, songFiles]);

  // Handle bulk review status change
  const applyBulkReviewStatus = useCallback(() => {
    const selectedSongs = Object.keys(songStates).filter(
      fileName => songStates[fileName]?.isSelected
    );
    
    if (selectedSongs.length === 0) {
      alert('Please select at least one song to apply bulk action');
      return;
    }
    
    selectedSongs.forEach(fileName => {
      changeReviewStatus(fileName, bulkReviewStatus);
    });
    
    // Clear selections after bulk action
    setSongStates(prev => {
      const updated = { ...prev };
      selectedSongs.forEach(fileName => {
        if (updated[fileName]) {
          updated[fileName].isSelected = false;
        }
      });
      return updated;
    });
    setSelectAllChecked(false);
  }, [songStates, bulkReviewStatus, changeReviewStatus]);

  // Load review statuses and notes from localStorage
  useEffect(() => {
    const reviewData = JSON.parse(localStorage.getItem('songReviews') || '{}');
    
    setSongStates(prev => {
      const updated = { ...prev };
      Object.keys(reviewData).forEach(fileName => {
        if (updated[fileName]) {
          if (typeof reviewData[fileName] === 'string') {
            // Old format compatibility
            updated[fileName].reviewStatus = reviewData[fileName] as ReviewStatus;
          } else {
            // New format with status and notes
            updated[fileName].reviewStatus = (reviewData[fileName].status || 'pending') as ReviewStatus;
            updated[fileName].reviewNotes = reviewData[fileName].notes || '';
          }
        }
      });
      return updated;
    });
  }, [songFiles]);

  // Update audio playback rate when speed changes
  useEffect(() => {
    Object.keys(audioRefs.current).forEach(fileName => {
      const audio = audioRefs.current[fileName];
      const state = songStates[fileName];
      if (audio && state) {
        const targetSpeed = useGlobalSpeed ? globalPlaybackSpeed : state.playbackSpeed;
        if (audio.playbackRate !== targetSpeed) {
          audio.playbackRate = targetSpeed;
          console.log(`[DisplayGeneratedSongs] Updated playback rate for ${fileName} to ${targetSpeed}x`);
        }
      }
    });
  }, [songStates, globalPlaybackSpeed, useGlobalSpeed]);

  // Setup audio event listeners
  const setupAudioListeners = useCallback((audio: HTMLAudioElement, fileName: string) => {
    console.log(`[DisplayGeneratedSongs] Setting up audio listeners for: ${fileName}`);
    
    const handleTimeUpdate = () => {
      setSongStates(prev => ({
        ...prev,
        [fileName]: {
          ...prev[fileName],
          currentTime: audio.currentTime,
          duration: audio.duration,
        },
      }));
    };

    const handleEnded = () => {
      console.log(`[DisplayGeneratedSongs] Song ended: ${fileName}`);
      setSongStates(prev => ({
        ...prev,
        [fileName]: {
          ...prev[fileName],
          isPlaying: false,
          currentTime: 0,
        },
      }));
    };

    const handlePlay = () => {
      console.log(`[DisplayGeneratedSongs] Play event: ${fileName}`);
      // Pause all other songs
      Object.keys(audioRefs.current).forEach(key => {
        if (key !== fileName && audioRefs.current[key] && !audioRefs.current[key]!.paused) {
          audioRefs.current[key]!.pause();
          setSongStates(prev => ({
            ...prev,
            [key]: {
              ...prev[key],
              isPlaying: false,
            },
          }));
        }
      });

      setSongStates(prev => ({
        ...prev,
        [fileName]: {
          ...prev[fileName],
          isPlaying: true,
          isLoading: false,
          loadError: undefined,
        },
      }));
    };

    const handlePause = () => {
      console.log(`[DisplayGeneratedSongs] Pause event: ${fileName}`);
      setSongStates(prev => ({
        ...prev,
        [fileName]: {
          ...prev[fileName],
          isPlaying: false,
        },
      }));
    };

    const handleError = (e: Event) => {
      const error = e as ErrorEvent;
      console.error(`[DisplayGeneratedSongs] Audio error for ${fileName}:`, error);
      console.error(`[DisplayGeneratedSongs] Audio src: ${audio.src}`);
      console.error(`[DisplayGeneratedSongs] Audio error code: ${audio.error?.code}`);
      console.error(`[DisplayGeneratedSongs] Audio error message: ${audio.error?.message}`);
      
      let errorMessage = 'Failed to load audio';
      if (audio.error) {
        switch (audio.error.code) {
          case 1: // MEDIA_ERR_ABORTED
            errorMessage = 'Audio loading was aborted';
            break;
          case 2: // MEDIA_ERR_NETWORK
            errorMessage = 'Network error while loading audio';
            break;
          case 3: // MEDIA_ERR_DECODE
            errorMessage = 'Audio decoding error';
            break;
          case 4: // MEDIA_ERR_SRC_NOT_SUPPORTED
            errorMessage = 'Audio format not supported or file not found';
            break;
        }
      }
      
      setSongStates(prev => ({
        ...prev,
        [fileName]: {
          ...prev[fileName],
          isPlaying: false,
          isLoading: false,
          loadError: errorMessage,
        },
      }));
    };

    const handleLoadStart = () => {
      console.log(`[DisplayGeneratedSongs] Load started for: ${fileName}`);
      console.log(`[DisplayGeneratedSongs] Audio source URL: ${audio.src}`);
      setSongStates(prev => ({
        ...prev,
        [fileName]: {
          ...prev[fileName],
          isLoading: true,
          loadError: undefined,
        },
      }));
    };

    const handleCanPlay = () => {
      console.log(`[DisplayGeneratedSongs] Can play: ${fileName}`);
      setSongStates(prev => ({
        ...prev,
        [fileName]: {
          ...prev[fileName],
          isLoading: false,
        },
      }));
    };

    const handleLoadedMetadata = () => {
      console.log(`[DisplayGeneratedSongs] Metadata loaded for ${fileName}: duration=${audio.duration}s`);
      handleTimeUpdate();
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('error', handleError);
    audio.addEventListener('loadstart', handleLoadStart);
    audio.addEventListener('canplay', handleCanPlay);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('loadstart', handleLoadStart);
      audio.removeEventListener('canplay', handleCanPlay);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
    };
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Toggle debug mode with Ctrl+Shift+D
      if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        setDebugMode(prev => !prev);
        console.log(`[DisplayGeneratedSongs] Debug mode: ${!debugMode ? 'ON' : 'OFF'}`);
        return;
      }

      // Find the currently playing song
      const playingSong = Object.keys(songStates).find(
        fileName => songStates[fileName]?.isPlaying
      );

      if (!playingSong) return;

      const audio = audioRefs.current[playingSong];
      if (!audio) return;

      switch (e.key) {
        case ' ':
          e.preventDefault();
          togglePlayPause(playingSong);
          break;
        case 'ArrowLeft':
          e.preventDefault();
          audio.currentTime = Math.max(0, audio.currentTime - 5);
          break;
        case 'ArrowRight':
          e.preventDefault();
          audio.currentTime = Math.min(audio.duration, audio.currentTime + 5);
          break;
        case 'ArrowUp':
          e.preventDefault();
          changeVolume(playingSong, Math.min(1, (songStates[playingSong]?.volume || 1) + 0.1));
          break;
        case 'ArrowDown':
          e.preventDefault();
          changeVolume(playingSong, Math.max(0, (songStates[playingSong]?.volume || 1) - 0.1));
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [songStates, togglePlayPause, changeVolume, debugMode]);

  // Format time display
  const formatTime = (seconds: number): string => {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get review status color and label
  const getReviewStatusStyle = (status: ReviewStatus) => {
    switch (status) {
      case 'pending':
        return { color: 'bg-gray-100 text-gray-700', label: 'Pending Review' };
      case 'in_review':
        return { color: 'bg-blue-100 text-blue-700', label: 'In Review' };
      case 'approved':
        return { color: 'bg-green-100 text-green-700', label: 'Approved' };
      case 'rejected':
        return { color: 'bg-red-100 text-red-700', label: 'Rejected' };
    }
  };

  if (!(stepCompleted.song || songFiles.length > 0)) {
    return null;
  }

  const groupedSongs = groupSongsByVerse(songFiles);

  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      <div className="flex justify-between items-center mb-4">
        <h4 className="font-medium text-lg">Songs for Manual Review</h4>
        
        {/* Global Speed Control */}
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={useGlobalSpeed}
              onChange={(e) => setUseGlobalSpeed(e.target.checked)}
              className="rounded"
            />
            Global Speed
          </label>
          
          {useGlobalSpeed && (
            <select
              value={globalPlaybackSpeed}
              onChange={(e) => changeGlobalSpeed(parseFloat(e.target.value) as PlaybackSpeed)}
              className="text-sm border rounded px-2 py-1 bg-white"
            >
              {PLAYBACK_SPEEDS.map(speed => (
                <option key={speed} value={speed}>
                  {speed}x
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Batch Operations Bar */}
      {songFiles.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectAllChecked}
                  onChange={toggleSelectAll}
                  className="rounded"
                />
                <span className="text-sm font-medium">Select All</span>
              </label>
              
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Bulk Action:</span>
                <select
                  value={bulkReviewStatus}
                  onChange={(e) => setBulkReviewStatus(e.target.value as ReviewStatus)}
                  className="text-sm border rounded px-2 py-1"
                >
                  <option value="pending">Mark as Pending</option>
                  <option value="in_review">Mark as In Review</option>
                  <option value="approved">Mark as Approved</option>
                  <option value="rejected">Mark as Rejected</option>
                </select>
                <button
                  onClick={applyBulkReviewStatus}
                  className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
                >
                  Apply to Selected
                </button>
              </div>
            </div>
            
            <div className="text-sm text-gray-600">
              {Object.values(songStates).filter(s => s?.isSelected).length} selected
            </div>
          </div>
        </div>
      )}

      {/* Keyboard Shortcuts Info */}
      <div className="text-xs text-gray-500 mb-3 p-2 bg-gray-100 rounded">
        <span className="font-medium">Keyboard Shortcuts:</span> Space (play/pause), ← → (seek 5s), ↑ ↓ (volume)
      </div>

      {isFetchingSongFiles ? (
        <div className="text-center py-4">Loading songs...</div>
      ) : fetchSongFilesError ? (
        <div className="p-3 bg-red-100 border border-red-300 rounded text-red-700">
          {fetchSongFilesError}
        </div>
      ) : songFiles.length === 0 ? (
        <div className="text-center py-4 text-gray-500">
          <p>No songs found. The generation process may still be in progress.</p>
          <p className="text-xs mt-4 italic">Tip: Press Ctrl+Shift+D to toggle debug mode for troubleshooting</p>
        </div>
      ) : (
        <div className="space-y-6 max-h-[600px] overflow-y-auto">
          {Array.from(groupedSongs.entries()).map(([verseRef, songs]) => (
            <div key={verseRef} className="border border-gray-200 rounded-lg p-4 bg-white">
              <h5 className="font-semibold text-md mb-3 text-blue-600">
                {verseRef === 'ungrouped' ? 'Other Songs' : verseRef}
              </h5>
              
              <div className="space-y-3">
                {songs.map((song) => {
                  const state = songStates[song.fileName] || {
                    isPlaying: false,
                    currentTime: 0,
                    duration: 0,
                    volume: 1,
                    isLooping: false,
                    playbackSpeed: globalPlaybackSpeed,
                    reviewStatus: 'pending' as ReviewStatus,
                    reviewNotes: '',
                    isSelected: false,
                  };
                  
                  const reviewStyle = getReviewStatusStyle(state.reviewStatus);
                  
                  return (
                    <div key={song.fileName} className={`p-3 border rounded-lg transition-colors ${
                      state.isSelected ? 'bg-blue-50 border-blue-300' : 'bg-gray-50'
                    }`}>
                      {/* Song Header with Selection Checkbox */}
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-start gap-3">
                          <input
                            type="checkbox"
                            checked={state.isSelected}
                            onChange={() => toggleSongSelection(song.fileName)}
                            className="mt-1 rounded"
                          />
                          <div>
                          <p className="font-medium text-sm">
                            {song.index !== undefined && `Song Index ${song.index}`}
                            {song.timestamp && ` (${song.timestamp})`}
                          </p>
                          <p className="text-xs text-gray-500 mt-1 break-all">{song.fileName}</p>
                          </div>
                        </div>
                        
                        {/* Review Status */}
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 text-xs rounded ${reviewStyle.color}`}>
                            {reviewStyle.label}
                          </span>
                          <select
                            value={state.reviewStatus}
                            onChange={(e) => changeReviewStatus(song.fileName, e.target.value as ReviewStatus)}
                            className="text-xs border rounded px-1 py-0.5"
                          >
                            <option value="pending">Pending</option>
                            <option value="in_review">In Review</option>
                            <option value="approved">Approved</option>
                            <option value="rejected">Rejected</option>
                          </select>
                        </div>
                      </div>

                      {/* Custom Audio Player */}
                      <div className="space-y-2">
                        {/* Error Display */}
                        {state.loadError && (
                          <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-md text-sm mb-2">
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <strong>Error:</strong> {state.loadError}
                                <div className="text-xs mt-1 text-red-600">
                                  File: {song.fileName}
                                </div>
                              </div>
                              <button
                                onClick={() => {
                                  console.log(`[DisplayGeneratedSongs] Retrying audio load for: ${song.fileName}`);
                                  const audio = audioRefs.current[song.fileName];
                                  if (audio) {
                                    // Clear error state
                                    setSongStates(prev => ({
                                      ...prev,
                                      [song.fileName]: {
                                        ...prev[song.fileName],
                                        loadError: undefined,
                                        isLoading: true,
                                      },
                                    }));
                                    // Force reload
                                    audio.load();
                                  }
                                }}
                                className="ml-2 px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                              >
                                Retry
                              </button>
                            </div>
                          </div>
                        )}

                        {/* Loading Indicator */}
                        {state.isLoading && (
                          <div className="bg-blue-50 border border-blue-200 text-blue-700 px-3 py-2 rounded-md text-sm mb-2">
                            Loading audio...
                          </div>
                        )}

                        {/* Debug Info */}
                        {debugMode && (
                          <div className="bg-gray-100 border border-gray-300 text-gray-700 px-3 py-2 rounded-md text-xs mb-2 font-mono">
                            <div><strong>Filename:</strong> {song.fileName}</div>
                            <div><strong>Mapped Path:</strong> {filePathMap.get(song.fileName) || 'Not mapped'}</div>
                            <div><strong>Audio URL:</strong> {`${API_SONGS_URL}/${encodeURIComponent(filePathMap.get(song.fileName) || song.fileName)}`}</div>
                            <div><strong>State:</strong> {JSON.stringify({
                              isPlaying: state.isPlaying,
                              isLoading: state.isLoading,
                              hasError: !!state.loadError,
                            })}</div>
                          </div>
                        )}

                        {/* Hidden HTML5 Audio Element */}
                        <audio
                          ref={(el) => {
                            audioRefs.current[song.fileName] = el;
                            if (el) {
                              const audioSrc = `${API_SONGS_URL}/${encodeURIComponent(filePathMap.get(song.fileName) || song.fileName)}`;
                              console.log(`[DisplayGeneratedSongs] Setting audio source for ${song.fileName}:`, audioSrc);
                              el.volume = state.volume;
                              el.playbackRate = useGlobalSpeed ? globalPlaybackSpeed : state.playbackSpeed;
                              el.loop = state.isLooping;
                              setupAudioListeners(el, song.fileName);
                            }
                          }}
                          src={`${API_SONGS_URL}/${encodeURIComponent(filePathMap.get(song.fileName) || song.fileName)}`}
                        >
                          <track kind="captions" srcLang="en" label="English captions" />
                        </audio>

                        {/* Progress Bar */}
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-600 w-12">
                            {formatTime(state.currentTime)}
                          </span>
                          <div
                            ref={(el) => { progressRefs.current[song.fileName] = el; }}
                            className="flex-1 h-2 bg-gray-200 rounded-full cursor-pointer relative"
                            onClick={(e) => handleSeek(song.fileName, e)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                togglePlayPause(song.fileName);
                              }
                            }}
                            role="slider"
                            tabIndex={0}
                            aria-label="Seek slider"
                            aria-valuemin={0}
                            aria-valuemax={state.duration || 100}
                            aria-valuenow={state.currentTime}
                          >
                            <div
                              className="h-full bg-blue-500 rounded-full"
                              style={{
                                width: `${state.duration ? (state.currentTime / state.duration) * 100 : 0}%`
                              }}
                            />
                          </div>
                          <span className="text-xs text-gray-600 w-12">
                            {formatTime(state.duration)}
                          </span>
                        </div>

                        {/* Controls Row */}
                        <div className="flex items-center justify-between">
                          {/* Play Controls */}
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => togglePlayPause(song.fileName)}
                              disabled={!!state.loadError}
                              className={`p-2 rounded transition-colors ${
                                state.loadError 
                                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                                  : 'bg-blue-500 text-white hover:bg-blue-600'
                              }`}
                            >
                              {state.isPlaying ? (
                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M5 4h3v12H5V4zm7 0h3v12h-3V4z" />
                                </svg>
                              ) : (
                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M5 4l10 6-10 6V4z" />
                                </svg>
                              )}
                            </button>

                            {/* Loop Toggle */}
                            <button
                              onClick={() => toggleLoop(song.fileName)}
                              className={`p-2 rounded transition-colors ${
                                state.isLooping
                                  ? 'bg-blue-500 text-white'
                                  : 'bg-gray-200 hover:bg-gray-300'
                              }`}
                              title="Loop"
                            >
                              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                              </svg>
                            </button>
                          </div>

                          {/* Speed Controls */}
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-600">Speed:</span>
                            <select
                              value={useGlobalSpeed ? globalPlaybackSpeed : state.playbackSpeed}
                              onChange={(e) => changePlaybackSpeed(song.fileName, parseFloat(e.target.value) as PlaybackSpeed)}
                              disabled={useGlobalSpeed}
                              className={`text-xs border rounded px-2 py-1 ${
                                useGlobalSpeed 
                                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                                  : 'bg-white'
                              }`}
                            >
                              {PLAYBACK_SPEEDS.map(speed => (
                                <option key={speed} value={speed}>
                                  {speed}x
                                </option>
                              ))}
                            </select>
                          </div>

                          {/* Volume Control */}
                          <div className="flex items-center gap-2">
                            <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" />
                            </svg>
                            <input
                              type="range"
                              min="0"
                              max="1"
                              step="0.1"
                              value={state.volume}
                              onChange={(e) => changeVolume(song.fileName, parseFloat(e.target.value))}
                              className="w-20"
                            />
                            <span className="text-xs text-gray-600 w-8">
                              {Math.round(state.volume * 100)}%
                            </span>
                          </div>

                          {/* Download Link */}
                          <a
                            href={`${API_SONGS_URL}/${encodeURIComponent(filePathMap.get(song.fileName) || song.fileName)}`}
                            download={song.fileName}
                            className="text-blue-500 hover:text-blue-700 text-sm hover:underline"
                          >
                            Download
                          </a>
                        </div>

                        {/* Review Actions Row */}
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => changeReviewStatus(song.fileName, 'approved')}
                              className={`px-3 py-1 text-sm rounded transition-colors ${
                                state.reviewStatus === 'approved'
                                  ? 'bg-green-500 text-white'
                                  : 'bg-green-100 text-green-700 hover:bg-green-200'
                              }`}
                            >
                              ✓ Approve
                            </button>
                            <button
                              onClick={() => changeReviewStatus(song.fileName, 'rejected')}
                              className={`px-3 py-1 text-sm rounded transition-colors ${
                                state.reviewStatus === 'rejected'
                                  ? 'bg-red-500 text-white'
                                  : 'bg-red-100 text-red-700 hover:bg-red-200'
                              }`}
                            >
                              ✗ Reject
                            </button>
                            <button
                              onClick={() => changeReviewStatus(song.fileName, 'in_review')}
                              className={`px-3 py-1 text-sm rounded transition-colors ${
                                state.reviewStatus === 'in_review'
                                  ? 'bg-blue-500 text-white'
                                  : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                              }`}
                            >
                              ⟳ Mark for Review
                            </button>
                          </div>
                          
                          {/* Review Notes */}
                          <div className="mt-3">
                            <label htmlFor={`review-notes-${song.fileName}`} className="block text-xs font-medium text-gray-700 mb-1">
                              Review Notes (optional)
                            </label>
                            <textarea
                              id={`review-notes-${song.fileName}`}
                              value={state.reviewNotes}
                              onChange={(e) => changeReviewNotes(song.fileName, e.target.value)}
                              placeholder="Add any notes about this song..."
                              className="w-full px-2 py-1 text-sm border rounded resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                              rows={2}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteConfirmation.show && deleteConfirmation.fileName && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Confirm Song Deletion</h3>
            <p className="mb-6 text-gray-700">
              Are you sure you want to delete this song?
              <br />
              <br />
              <strong className="text-red-600">This will permanently remove the song from both local storage and Suno.com.</strong>
              <br />
              <br />
              <span className="text-sm text-gray-600 break-all">File: {deleteConfirmation.fileName}</span>
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteConfirmation({ show: false, fileName: null })}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteSong(deleteConfirmation.fileName!)}
                className={`px-4 py-2 text-white rounded transition-colors ${
                  isDeleting
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-red-500 hover:bg-red-600'
                }`}
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete Song'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DisplayGeneratedSongs;