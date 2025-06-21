import { useState, useEffect } from "react";
import {
  generateSong as callGenerateSongAPI,
  generateSongStructure as callGenerateSongStructureAPI,
  fetchSongStructures,
  fetchStyles,
  type SongStructure,
  type Style,
} from "../lib/api";

interface ModalSongsProps {
  isOpen: boolean;
  onClose: () => void;
  range: string;
  bookName: string;
  chapter: number;
}

const ModalSongs = ({
  isOpen,
  onClose,
  range,
  bookName,
  chapter,
}: ModalSongsProps) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isStructureLoading, setIsStructureLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [structureMessage, setStructureMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [structureError, setStructureError] = useState<string | null>(null);

  // New state for fetched data
  const [songStructures, setSongStructures] = useState<SongStructure[]>([]);
  const [styles, setStyles] = useState<Style[]>([]);
  const [isFetching, setIsFetching] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<
    "generate" | "structures" | "styles"
  >("generate");
  const [generatingStyle, setGeneratingStyle] = useState<string | null>(null);

  // Fetch data when modal opens
  useEffect(() => {
    if (isOpen) {
      fetchData();
    }
  }, [isOpen]);

  const fetchData = async () => {
    setIsFetching(true);
    setFetchError(null);

    try {
      const [structuresResponse, stylesResponse] = await Promise.all([
        fetchSongStructures(),
        fetchStyles(),
      ]);

      if (structuresResponse.success && structuresResponse.result) {
        setSongStructures(structuresResponse.result);
      } else {
        console.error(
          "Failed to fetch song structures:",
          structuresResponse.error
        );
      }

      if (stylesResponse.success && stylesResponse.result) {
        setStyles(stylesResponse.result);
      } else {
        console.error("Failed to fetch styles:", stylesResponse.error);
      }
    } catch (err) {
      setFetchError("Failed to fetch data");
      console.error("Error fetching data:", err);
    } finally {
      setIsFetching(false);
    }
  };

  const handleGenerateSong = async (selectedStyle: string) => {
    setIsLoading(true);
    setGeneratingStyle(selectedStyle);
    setMessage(null);
    setError(null);
    try {
      const title = `${bookName} ${chapter}:${range}`;
      const requestPayload = {
        strBookName: bookName,
        intBookChapter: chapter,
        strVerseRange: range,
        strStyle: selectedStyle,
        strTitle: title,
      };

      console.log("Sending request payload:", requestPayload);

      const result = await callGenerateSongAPI(requestPayload);

      if (result.success) {
        setMessage(
          `Song with style '${selectedStyle}' generated successfully!`
        );
        console.log("Song generation result:", result.result);
      } else {
        setError(result.error || result.message || "Failed to generate song");
      }
    } catch (err) {
      setError("An unexpected error occurred");
      console.error("Error generating song:", err);
    } finally {
      setIsLoading(false);
      setGeneratingStyle(null);
    }
  };

  const handleGenerateSongStructure = async () => {
    setIsStructureLoading(true);
    setStructureMessage(null);
    setStructureError(null);

    try {
      const requestPayload = {
        strBookName: bookName,
        intBookChapter: chapter,
        strVerseRange: range,
      };

      console.log("Sending song structure request payload:", requestPayload);

      const result = await callGenerateSongStructureAPI(requestPayload);

      if (result.success) {
        setStructureMessage("Song structure generated successfully!");
        console.log("Song structure generation result:", result.result);
      } else {
        setStructureError(
          result.error || result.message || "Failed to generate song structure"
        );
      }
    } catch (err) {
      setStructureError("An unexpected error occurred");
      console.error("Error generating song structure:", err);
    } finally {
      setIsStructureLoading(false);
    }
  };

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">
            Song Management - {bookName} {chapter}:{range}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl font-bold"
          >
            ×
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 mb-4 border-b">
          <button
            className={`px-4 py-2 text-sm font-medium rounded-t-lg ${
              activeTab === "generate"
                ? "bg-blue-500 text-white border-blue-500"
                : "text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => setActiveTab("generate")}
          >
            Generate
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium rounded-t-lg ${
              activeTab === "structures"
                ? "bg-blue-500 text-white border-blue-500"
                : "text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => setActiveTab("structures")}
          >
            Song Structures ({songStructures.length})
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium rounded-t-lg ${
              activeTab === "styles"
                ? "bg-blue-500 text-white border-blue-500"
                : "text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => setActiveTab("styles")}
          >
            Styles ({styles.length})
          </button>
        </div>

        {/* Tab Content */}
        <div className="space-y-4">
          {/* Generate Tab */}
          {activeTab === "generate" && (
            <>
              <div className="flex gap-2">
                <button
                  className={`flex-1 px-4 py-2 text-white rounded text-sm transition-colors ${
                    isStructureLoading
                      ? "bg-gray-400 cursor-not-allowed"
                      : "bg-blue-500 hover:bg-blue-600"
                  }`}
                  onClick={handleGenerateSongStructure}
                  disabled={isStructureLoading || isLoading}
                >
                  {isStructureLoading ? "Generating..." : "Generate Structure"}
                </button>
              </div>

              {structureMessage && (
                <div className="p-3 bg-blue-100 border border-blue-300 rounded text-blue-700">
                  {structureMessage}
                </div>
              )}

              {structureError && (
                <div className="p-3 bg-red-100 border border-red-300 rounded text-red-700">
                  {structureError}
                </div>
              )}
            </>
          )}

          {/* Song Structures Tab */}
          {activeTab === "structures" && (
            <div>
              {isFetching ? (
                <div className="text-center py-4">
                  Loading song structures...
                </div>
              ) : fetchError ? (
                <div className="p-3 bg-red-100 border border-red-300 rounded text-red-700">
                  {fetchError}
                </div>
              ) : songStructures.length === 0 ? (
                <div className="text-center py-4 text-gray-500">
                  No song structures found
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {songStructures.map((structure) => (
                    <div
                      key={structure.id}
                      className="p-3 bg-gray-50 border rounded"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-medium text-sm">
                          {structure.book_name} {structure.chapter}:
                          {structure.verse_range}
                        </h4>
                        <div className="text-xs text-gray-500">
                          <span>Tone: {structure.tone}</span>
                        </div>
                      </div>
                      <div className="mb-2">
                        <span className="text-xs font-medium text-gray-600">
                          Styles:{" "}
                        </span>
                        <span className="text-xs text-gray-700">
                          {structure.styles}
                        </span>
                      </div>
                      <pre className="text-xs bg-white p-2 rounded border whitespace-pre-wrap">
                        {structure.song_structure}
                      </pre>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Styles Tab */}
          {activeTab === "styles" && (
            <div>
              {message && (
                <div className="p-3 mb-4 bg-green-100 border border-green-300 rounded text-green-700">
                  {message}
                </div>
              )}

              {error && (
                <div className="p-3 mb-4 bg-red-100 border border-red-300 rounded text-red-700">
                  {error}
                </div>
              )}
              {isFetching ? (
                <div className="text-center py-4">Loading styles...</div>
              ) : fetchError ? (
                <div className="p-3 bg-red-100 border border-red-300 rounded text-red-700">
                  {fetchError}
                </div>
              ) : styles.length === 0 ? (
                <div className="text-center py-4 text-gray-500">
                  No styles found
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {styles.map((style, index) => (
                    <div
                      key={style.id || index}
                      className="p-3 bg-gray-50 border rounded"
                    >
                      <div className="flex justify-between items-center mb-2">
                        <div>
                          <h4 className="font-medium text-sm">{style.name}</h4>
                          <span className="text-xs text-gray-500">
                            Used in{" "}
                            {
                              songStructures.filter((s) =>
                                s.styles.includes(style.name)
                              ).length
                            }{" "}
                            structures
                          </span>
                        </div>
                        <button
                          className={`px-3 py-1 text-white rounded text-xs transition-colors ${
                            isLoading && generatingStyle === style.name
                              ? "bg-gray-400 cursor-not-allowed"
                              : "bg-green-500 hover:bg-green-600"
                          }`}
                          onClick={() => handleGenerateSong(style.name)}
                          disabled={isLoading || isStructureLoading}
                        >
                          {isLoading && generatingStyle === style.name
                            ? "Generating..."
                            : "Generate Song"}
                        </button>
                      </div>
                      {style.description && (
                        <p className="text-xs text-gray-600">
                          {style.description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ModalSongs;
