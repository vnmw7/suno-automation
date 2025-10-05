/*
System: Suno Automation
Module: Song Sidebar Component
Purpose: Sidebar component for displaying and navigating songs
*/

import { useEffect, useMemo, useRef, useState } from "react";
import { MusicIcon } from "./ui/icon";

export interface Song {
  id: string;
  name: string;
  fileName: string;
}

interface SongSidebarProps {
  songs: Song[];
  selectedSong: Song | null;
  onSongSelect: (song: Song) => void;
}

type ReviewStatus = "pending" | "approved" | "regenerate";
type PlaybackSpeed = 0.25 | 0.5 | 0.75 | 1 | 1.25 | 1.5 | 1.75 | 2 | 2.25 | 2.5 | 2.75 | 3;

const SONGS_PUBLIC_DIRECTORY = "/songs";
const PLAYBACK_SPEED_OPTIONS: PlaybackSpeed[] = [
  0.25,
  0.5,
  0.75,
  1,
  1.25,
  1.5,
  1.75,
  2,
  2.25,
  2.5,
  2.75,
  3,
];

export default function SongSidebar({
  songs,
  selectedSong,
  onSongSelect,
}: SongSidebarProps) {
  const [errPlaybackMessage, setErrPlaybackMessage] = useState<string | null>(null);
  const [strActionMessage, setStrActionMessage] = useState<string | null>(null);
  const [objPlaybackSpeeds, setObjPlaybackSpeeds] = useState<Record<string, PlaybackSpeed>>({});
  const [objReviewStatuses, setObjReviewStatuses] = useState<Record<string, ReviewStatus>>({});

  const refAudioElement = useRef<HTMLAudioElement | null>(null);

  const arrVisibleSongs = useMemo(() => songs, [songs]);

  const strSelectedSongPath = useMemo(() => {
    if (!selectedSong) {
      return null;
    }
    return `${SONGS_PUBLIC_DIRECTORY}/${encodeURIComponent(selectedSong.fileName)}`;
  }, [selectedSong]);

  const numSelectedSongSpeed: PlaybackSpeed = selectedSong
    ? objPlaybackSpeeds[selectedSong.id] ?? 1
    : 1;

  useEffect(() => {
    if (songs.length === 0) {
      setObjPlaybackSpeeds({});
      setObjReviewStatuses({});
      return;
    }

    setObjPlaybackSpeeds((objPrev) => {
      const objNext = { ...objPrev };
      songs.forEach((song) => {
        if (objNext[song.id] === undefined) {
          objNext[song.id] = 1;
        }
      });
      return objNext;
    });

    setObjReviewStatuses((objPrev) => {
      const objNext = { ...objPrev };
      songs.forEach((song) => {
        if (objNext[song.id] === undefined) {
          objNext[song.id] = "pending";
        }
      });
      return objNext;
    });
  }, [songs]);

  useEffect(() => {
    setErrPlaybackMessage(null);
    setStrActionMessage(null);
  }, [selectedSong]);

  useEffect(() => {
    if (refAudioElement.current && selectedSong) {
      refAudioElement.current.playbackRate = numSelectedSongSpeed;
    }
  }, [selectedSong, numSelectedSongSpeed]);

  const fncHandleSpeedChange = (songId: string, speedValue: PlaybackSpeed) => {
    setObjPlaybackSpeeds((objPrev) => ({
      ...objPrev,
      [songId]: speedValue,
    }));

    if (selectedSong?.id === songId && refAudioElement.current) {
      refAudioElement.current.playbackRate = speedValue;
    }
  };

  const fncHandleReviewStatus = (songId: string, statusValue: ReviewStatus) => {
    setObjReviewStatuses((objPrev) => ({
      ...objPrev,
      [songId]: statusValue,
    }));

    const strStatusLabel =
      statusValue === "approved" ? "Song approved for use." : "Song flagged for regeneration.";
    setStrActionMessage(strStatusLabel);
  };

  return (
    <aside className="flex w-full flex-col gap-6 rounded-lg border border-neutral-200 bg-white p-4 md:w-80 md:shrink-0 md:p-6 md:sticky md:top-8 md:max-h-[calc(100vh-4rem)] md:overflow-y-auto">
      <h2 className="flex items-center border-b border-neutral-200 pb-3 text-lg font-semibold text-neutral-800">
        <MusicIcon className="mr-2 h-5 w-5 text-neutral-500" />
        Songs
      </h2>

      {arrVisibleSongs.length > 0 ? (
        <div className="space-y-2">
          {arrVisibleSongs.map((song) => (
            <button
              key={song.id}
              type="button"
              onClick={() => onSongSelect(song)}
              className={`w-full rounded-md border px-3 py-2 text-left transition-all ${
                selectedSong?.id === song.id
                  ? "bg-neutral-900 border-neutral-900 text-white shadow-sm"
                  : "border-neutral-200 bg-white text-neutral-700 hover:bg-neutral-100"
              }`}
            >
              <div className="flex items-center gap-3">
                <MusicIcon
                  className={`h-4 w-4 flex-shrink-0 ${
                    selectedSong?.id === song.id ? "text-white" : "text-neutral-500"
                  }`}
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">
                    {song.name}
                  </p>
                  <p
                    className={`truncate text-xs ${
                      selectedSong?.id === song.id ? "text-neutral-200" : "text-neutral-500"
                    }`}
                  >
                    {song.fileName}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div className="py-10 text-center text-neutral-500">
          <MusicIcon className="mx-auto mb-4 h-10 w-10 text-neutral-300" />
          <p className="text-sm font-medium">No songs found</p>
          <p className="mt-1 text-xs text-neutral-400">
            Add some MP3 files to the public/songs directory
          </p>
        </div>
      )}

      {arrVisibleSongs.length > 0 && (
        <div className="mt-auto space-y-3 border-t border-neutral-200 pt-4">
          <div className="text-sm text-neutral-600">
            {arrVisibleSongs.length} {arrVisibleSongs.length === 1 ? "song" : "songs"} available for manual review.
          </div>

          <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
            {selectedSong && strSelectedSongPath ? (
              <div className="space-y-3">
                <div>
                  <p className="text-xs uppercase tracking-wide text-neutral-500">Now Reviewing</p>
                  <p className="truncate text-sm font-medium text-neutral-800">
                    {selectedSong.name}
                  </p>
                  <p className="truncate text-xs text-neutral-500">{selectedSong.fileName}</p>
                </div>

                <audio
                  key={`${selectedSong.id}-${strSelectedSongPath}`}
                  ref={(element) => {
                    refAudioElement.current = element;
                    if (element) {
                      element.playbackRate = numSelectedSongSpeed;
                    }
                  }}
                  controls
                  autoPlay
                  src={strSelectedSongPath}
                  className="w-full"
                  onError={() =>
                    setErrPlaybackMessage("Unable to load this song preview. Please review from the source if needed.")
                  }
                >
                  Your browser does not support the audio element.
                </audio>

                <div className="flex flex-col gap-2 text-xs text-neutral-600">
                  <div className="flex items-center justify-between gap-2">
                    <span>Playback speed</span>
                    <select
                      aria-label="Playback speed"
                      className="rounded border border-neutral-300 bg-white px-2 py-1 text-xs text-neutral-700"
                      value={numSelectedSongSpeed}
                      onChange={(event) =>
                        fncHandleSpeedChange(
                          selectedSong.id,
                          Number(event.target.value) as PlaybackSpeed
                        )
                      }
                    >
                      {PLAYBACK_SPEED_OPTIONS.map((speedOption) => (
                        <option key={speedOption} value={speedOption}>
                          {speedOption}x
                        </option>
                      ))}
                    </select>
                  </div>

                  <span>Use the controls above to play, pause, or scrub through the track.</span>
                </div>

                <div className="flex flex-wrap gap-2 text-sm">
                  <button
                    type="button"
                    onClick={() => fncHandleReviewStatus(selectedSong.id, "approved")}
                    className={`rounded px-3 py-1 transition-colors ${
                      objReviewStatuses[selectedSong.id] === "approved"
                        ? "bg-green-500 text-white"
                        : "bg-green-100 text-green-700 hover:bg-green-200"
                    }`}
                  >
                    ✓ Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => fncHandleReviewStatus(selectedSong.id, "regenerate")}
                    className={`rounded px-3 py-1 transition-colors ${
                      objReviewStatuses[selectedSong.id] === "regenerate"
                        ? "bg-red-500 text-white"
                        : "bg-red-100 text-red-700 hover:bg-red-200"
                    }`}
                  >
                    ✗ Regenerate
                  </button>
                </div>

                {strActionMessage && (
                  <p className="text-xs text-green-600">{strActionMessage}</p>
                )}

                {errPlaybackMessage && (
                  <p className="text-xs text-red-600">{errPlaybackMessage}</p>
                )}

                <p className="text-xs text-neutral-500">
                  Current status: {objReviewStatuses[selectedSong.id]?.replace("_", " ") ?? "pending"}
                </p>
              </div>
            ) : (
              <p className="text-xs text-neutral-500">
                Select a song from the list to preview it here before approving in the automation workflow.
              </p>
            )}
          </div>
        </div>
      )}
    </aside>
  );
}