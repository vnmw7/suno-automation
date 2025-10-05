/*
System: Suno Automation
Module: Song Sidebar Component
Purpose: Sidebar component for displaying and navigating songs
*/

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

export default function SongSidebar({
  songs,
  selectedSong,
  onSongSelect,
}: SongSidebarProps) {
  return (
    <aside className="flex w-full flex-col gap-6 rounded-lg border border-neutral-200 bg-white p-4 md:w-80 md:shrink-0 md:p-6 md:sticky md:top-8 md:max-h-[calc(100vh-4rem)] md:overflow-y-auto">
      <h2 className="flex items-center border-b border-neutral-200 pb-3 text-lg font-semibold text-neutral-800">
        <MusicIcon className="mr-2 h-5 w-5 text-neutral-500" />
        Songs
      </h2>

      {songs.length > 0 ? (
        <div className="space-y-2">
          {songs.map((song) => (
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
                      selectedSong?.id === song.id
                        ? "text-neutral-200"
                        : "text-neutral-500"
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

      {songs.length > 0 && (
        <div className="mt-auto border-t border-neutral-200 pt-4">
          <div className="text-center text-sm text-neutral-600">
            {songs.length} {songs.length === 1 ? "song" : "songs"} available
          </div>
        </div>
      )}
    </aside>
  );
}
