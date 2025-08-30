interface DisplayGeneratedSongsProps {
  stepCompleted: { song: boolean };
  songFiles: string[];
  isFetchingSongFiles: boolean;
  fetchSongFilesError: string | null;
}

const SONG_DIRECTORY = "/songs";

const DisplayGeneratedSongs = ({
  stepCompleted,
  songFiles,
  isFetchingSongFiles,
  fetchSongFilesError,
}: DisplayGeneratedSongsProps) => {
  if (!(stepCompleted.song || songFiles.length > 0)) {
    return null;
  }

  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      <h4 className="font-medium mb-3">Your Generated Songs</h4>
      {isFetchingSongFiles ? (
        <div className="text-center py-4">Loading songs...</div>
      ) : fetchSongFilesError ? (
        <div className="p-3 bg-red-100 border border-red-300 rounded text-red-700">
          {fetchSongFilesError}
        </div>
      ) : songFiles.length === 0 ? (
        <div className="text-center py-4 text-gray-500">
          No songs found. The generation process may still be in progress.
        </div>
      ) : (
        <div className="space-y-4 max-h-64 overflow-y-auto">
          {songFiles.map((fileName) => (
            <div key={fileName} className="p-3 bg-white border rounded">
              <p className="font-medium text-sm mb-2 break-all">{fileName}</p>
              <audio
                controls
                src={`${SONG_DIRECTORY}/${encodeURIComponent(fileName)}`}
                className="w-full mb-2"
              >
                <track kind="captions" srcLang="en" label="English captions" />
                Your browser does not support the audio element.
              </audio>
              <a
                href={`${SONG_DIRECTORY}/${encodeURIComponent(fileName)}`}
                download={fileName}
                className="text-blue-500 hover:text-blue-700 text-sm hover:underline"
              >
                Download MP3
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DisplayGeneratedSongs;