import { useState, useEffect } from "react";
import {
  generateSongStructure as callGenerateSongStructureAPI,
  fetchSongStructures,
  fetchStyles,
  fetchSongFilesFromPublic,
  orchestratorWorkflow,
  type SongStructure,
  type Style,
  type OrchestratorRequest,
} from "../lib/api";

const SONG_DIRECTORY = "/songs";

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

  const [songStructures, setSongStructures] = useState<SongStructure[]>([]);
  const [styles, setStyles] = useState<Style[]>([]);
  const [isFetchingStructuresStyles, setIsFetchingStructuresStyles] = useState(false);
  const [fetchStructuresStylesError, setFetchStructuresStylesError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);
  const [showStructures, setShowStructures] = useState(false);
  const [showStyles, setShowStyles] = useState(false);
  const [stepCompleted, setStepCompleted] = useState({
    structure: false,
    style: false,
    song: false,
  });
  const [generatingStyle, setGeneratingStyle] = useState<string | null>(null);
  const [selectedStyle, setSelectedStyle] = useState<string | null>(null);
  const [songFiles, setSongFiles] = useState<string[]>([]);
  const [isFetchingSongFiles, setIsFetchingSongFiles] = useState(false);
  const [fetchSongFilesError, setFetchSongFilesError] = useState<string | null>(null);

  useEffect(() => {
    const loadInitialData = async () => {
      // Fetch structures and styles
      setIsFetchingStructuresStyles(true);
      setFetchStructuresStylesError(null);
      try {
        const [structuresResponse, stylesResponse] = await Promise.all([
          fetchSongStructures(range),
          fetchStyles(range),
        ]);

        const errors: string[] = [];
        if (structuresResponse.success && structuresResponse.result) {
          setSongStructures(structuresResponse.result);
          if (structuresResponse.result.length > 0) {
            setStepCompleted(prev => ({ ...prev, structure: true }));
          }
        } else {
          const error =
            structuresResponse.error || "Error fetching structures";
          console.error("Failed to fetch song structures:", error);
          errors.push(error);
        }

        if (stylesResponse.success && stylesResponse.result) {
          setStyles(stylesResponse.result);
        } else {
          const error = stylesResponse.error || "Error fetching styles";
          console.error("Failed to fetch styles:", error);
          errors.push(error);
        }

        if (errors.length > 0) {
          setFetchStructuresStylesError(errors.join(" "));
        }
      } catch (err) {
        setFetchStructuresStylesError(
          "An unexpected error occurred while fetching structures/styles."
        );
        console.error("Error fetching structures/styles data:", err);
      } finally {
        setIsFetchingStructuresStyles(false);
      }

      // Fetch song files from the public directory
      setIsFetchingSongFiles(true);
      setFetchSongFilesError(null);
      try {
        const songFilesResponse = await fetchSongFilesFromPublic(
          bookName,
          chapter,
          range
        );
        if (songFilesResponse.success && songFilesResponse.result) {
          setSongFiles(songFilesResponse.result);
        } else {
          setFetchSongFilesError(
            songFilesResponse.error || "Failed to load song files."
          );
          console.error(
            "Failed to load song files from public:",
            songFilesResponse.error
          );
        }
      } catch (err) {
        setFetchSongFilesError(
          "An unexpected error occurred while fetching song files."
        );
        console.error("Error fetching song files from public:", err);
      } finally {
        setIsFetchingSongFiles(false);
      }
    };

    if (isOpen) {
      loadInitialData();
    } else {
      // Clear data on close
      setSongStructures([]);
      setStyles([]);
      setSongFiles([]);
      setMessage(null);
      setError(null);
      setStructureMessage(null);
      setStructureError(null);
      setFetchStructuresStylesError(null);
      setFetchSongFilesError(null);
      setCurrentStep(1);
      setShowStructures(false);
      setShowStyles(false);
      setStepCompleted({ structure: false, style: false, song: false });
      setSelectedStyle(null);
    }
  }, [isOpen, range, bookName, chapter]);

  const handleGenerateSong = async (selectedStyle: string) => {
    setIsLoading(true);
    setGeneratingStyle(selectedStyle);
    setMessage(null);
    setError(null);
    
    try {
      const title = `${bookName} ${chapter}:${range}`;
      const requestPayload: OrchestratorRequest = {
        strBookName: bookName,
        intBookChapter: chapter,
        strVerseRange: range,
        strStyle: selectedStyle,
        strTitle: title,
        song_structure_id: songStructures.length > 0 ? songStructures[0].id : undefined
      };

      console.log("🎼 [FRONTEND] Sending orchestrator request:", requestPayload);
      setMessage(`🎼 Starting automated song workflow with style '${selectedStyle}'...`);

      // Use the API function instead of direct fetch
      const result = await orchestratorWorkflow(requestPayload);
      console.log("🎼 [FRONTEND] Orchestrator completed:", result);

      if (result.success) {
        // Workflow completed successfully
        const goodSongs = result.good_songs || 0;
        const reRolledSongs = result.re_rolled_songs || 0;
        const attempts = result.total_attempts || 1;
        
        setMessage(
          `🎼 Workflow completed successfully! ` +
          `Generated ${goodSongs} high-quality song(s) in ${attempts} attempt(s). ` +
          `${reRolledSongs > 0 ? `${reRolledSongs} song(s) were re-rolled for quality.` : ''} ` +
          `✅ FINAL SONGS are now available in: backend/songs/final_review`
        );
        
        setStepCompleted((prev) => ({ ...prev, song: true }));
        
      } else {
        // Workflow failed after all attempts
        const attempts = result.total_attempts || 0;
        const errorDetails = result.error ? ` (${result.error})` : '';
        
        setError(
          `🎼 Workflow failed after ${attempts} attempt(s): ${result.message}${errorDetails}`
        );
      }

      // Refresh the song files list
      const songFilesResponse = await fetchSongFilesFromPublic(bookName, chapter, range);
      if (songFilesResponse.success && songFilesResponse.result) {
        setSongFiles(songFilesResponse.result);
      }

    } catch (err) {
      console.error("🎼 [FRONTEND] Orchestrator error:", err);
      setError("🎼 Network error occurred while communicating with the orchestrator");
    } finally {
      setIsLoading(false);
      setGeneratingStyle(null);
    }
  };

  const handleGenerateOrRegenerateStructure = async () => {
    setIsStructureLoading(true);
    setStructureMessage(null);
    setStructureError(null);

    try {
      // First, fetch the current structures from the database for this range.
      const response = await fetchSongStructures(range);

      if (!response.success || !response.result) {
        setStructureError(
          response.error || "Failed to fetch song structures from the database."
        );
        setIsStructureLoading(false);
        return;
      }

      const existingStructures = response.result;
      setSongStructures(existingStructures); // Update state with the latest data

      // Now, decide whether to generate or regenerate based on the fetched data.
      if (existingStructures.length > 0) {
        // Regenerate the first existing structure.
        const structureId = String(existingStructures[0].id);
        console.log("Regenerating structure with ID:", structureId);

        const requestPayload = {
          strBookName: bookName,
          intBookChapter: chapter,
          strVerseRange: range,
          structureId: structureId,
        };

        const result = await callGenerateSongStructureAPI(requestPayload);

        if (result.success) {
          setStructureMessage("Song structure regenerated successfully!");
          console.log("Regenerated structure result:", result.result);
        } else {
          setStructureError(
            result.error ||
              result.message ||
              "Failed to regenerate song structure"
          );
        }
      } else {
        // No existing structure, so generate a new one.
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
            result.error ||
              result.message ||
              "Failed to generate song structure"
          );
        }
      }

      // Mark structure step as completed
      setStepCompleted((prev) => ({ ...prev, structure: true }));

      // Refetch updated song structures and styles to ensure UI is in sync
      await fetchAndSetSongStructures();
      await fetchAndSetStyles();
    } catch (err) {
      setStructureError("An unexpected error occurred");
      console.error("Error in structure generation:", err);
    } finally {
      setIsStructureLoading(false);
    }
  };

  const fetchAndSetSongStructures = async () => {
    try {
      const response = await fetchSongStructures(range);
      if (response.success && response.result) {
        setSongStructures(response.result);
      } else {
        console.error("Failed to fetch song structures:", response.error);
      }
    } catch (err) {
      console.error("Error fetching song structures:", err);
    }
  };

  const fetchAndSetStyles = async () => {
    try {
      const stylesResponse = await fetchStyles(range);
      if (stylesResponse.success && stylesResponse.result) {
        setStyles(stylesResponse.result);
      } else {
        console.error("Failed to refresh styles:", stylesResponse.error);
      }
    } catch (err) {
      console.error("Error refreshing styles:", err);
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

        {/* Step Progress Indicator */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              {[1, 2, 3].map((step) => (
                <div key={step} className="flex items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      currentStep === step
                        ? "bg-blue-500 text-white"
                        : stepCompleted[step === 1 ? 'structure' : step === 2 ? 'style' : 'song']
                        ? "bg-green-500 text-white"
                        : "bg-gray-200 text-gray-600"
                    }`}
                  >
                    {stepCompleted[step === 1 ? 'structure' : step === 2 ? 'style' : 'song'] ? "✓" : step}
                  </div>
                  <div className="ml-2">
                    <div className={`text-sm font-medium ${
                      currentStep === step ? "text-blue-600" : "text-gray-600"
                    }`}>
                      {step === 1 ? "Generate Structure" : step === 2 ? "Select Style" : "Generate Song"}
                    </div>
                    <div className="text-xs text-gray-500">
                      {step === 1 ? "Create song structure" : step === 2 ? "Choose musical style" : "Create final song"}
                    </div>
                  </div>
                  {step < 3 && (
                    <div className={`w-8 h-0.5 ml-4 ${
                      stepCompleted[step === 1 ? 'structure' : 'style'] ? "bg-green-500" : "bg-gray-200"
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </div>
          
          {/* Step Navigation */}
          <div className="flex justify-between">
            <button
              className={`px-4 py-2 text-sm font-medium rounded ${
                currentStep === 1
                  ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
              onClick={() => setCurrentStep(Math.max(1, currentStep - 1) as 1 | 2 | 3)}
              disabled={currentStep === 1}
            >
              ← Previous
            </button>
            <button
              className={`px-4 py-2 text-sm font-medium rounded ${
                currentStep === 3 || !stepCompleted[currentStep === 1 ? 'structure' : 'style']
                  ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                  : "bg-blue-500 text-white hover:bg-blue-600"
              }`}
              onClick={() => setCurrentStep(Math.min(3, currentStep + 1) as 1 | 2 | 3)}
              disabled={currentStep === 3 || !stepCompleted[currentStep === 1 ? 'structure' : 'style']}
            >
              Next →
            </button>
          </div>
        </div>

        <div className="space-y-4">
          {/* Step 1: Generate Structure */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-lg font-medium text-blue-900 mb-2">Step 1: Generate Song Structure</h3>
                <p className="text-sm text-blue-700 mb-4">
                  First, we&apos;ll analyze the biblical text and create a structured outline for your song.
                  This includes determining the tone, themes, and overall flow.
                </p>
                
                <div className="flex gap-2">
                  <div className="flex gap-2 w-full">
                    <button
                      className={`flex-1 px-4 py-2 text-white rounded text-sm transition-colors ${
                        isStructureLoading
                          ? "bg-gray-400 cursor-not-allowed"
                          : "bg-blue-500 hover:bg-blue-600"
                      }`}
                      onClick={handleGenerateOrRegenerateStructure}
                      disabled={isStructureLoading || isLoading}
                    >
                      {isStructureLoading
                        ? "Processing Structure..."
                        : songStructures.length > 0
                          ? "Regenerate Structure"
                          : "Generate Structure"}
                    </button>
                    
                    <button
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
                      onClick={() => setShowStructures(!showStructures)}
                    >
                      {showStructures ? "Hide" : "View"} Structures
                    </button>
                  </div>
                </div>

                {structureMessage && (
                  <div className="mt-3 p-3 bg-green-100 border border-green-300 rounded text-green-700">
                    {structureMessage}
                  </div>
                )}

                {structureError && (
                  <div className="mt-3 p-3 bg-red-100 border border-red-300 rounded text-red-700">
                    {structureError}
                  </div>
                )}
              </div>

              {/* Existing Structures View */}
              {showStructures && (
                <div className="border rounded-lg p-4 bg-gray-50">
                  <h4 className="font-medium mb-3">Existing Song Structures</h4>
                  {isFetchingStructuresStyles ? (
                    <div className="text-center py-4">Loading song structures...</div>
                  ) : fetchStructuresStylesError ? (
                    <div className="p-3 bg-red-100 border border-red-300 rounded text-red-700">
                      {fetchStructuresStylesError}
                    </div>
                  ) : songStructures.length === 0 ? (
                    <div className="text-center py-4 text-gray-500">
                      No song structures found. Generate one above to continue.
                    </div>
                  ) : (
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {songStructures.map((structure) => (
                        <div key={structure.id} className="p-3 bg-white border rounded">
                          <h5 className="font-medium text-sm mb-2">
                            {structure.book_name} {structure.chapter}:{structure.verse_range}
                          </h5>
                          <pre className="text-xs bg-gray-50 p-2 rounded border whitespace-pre-wrap">
                            {structure.song_structure}
                          </pre>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Step 2: Select Style */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="text-lg font-medium text-green-900 mb-2">Step 2: Select Musical Style</h3>
                <p className="text-sm text-green-700 mb-4">
                  Choose a musical style that best fits your song structure. Each style has unique characteristics 
                  that will influence the melody, rhythm, and overall feel of your song.
                </p>
                
                <div className="flex gap-2 mb-4">
                  <button
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
                    onClick={() => setShowStyles(!showStyles)}
                  >
                    {showStyles ? "Hide" : "View"} Available Styles ({styles.length})
                  </button>
                </div>

                {!stepCompleted.structure && (
                  <div className="p-3 bg-yellow-100 border border-yellow-300 rounded text-yellow-700">
                    Please complete Step 1 (Generate Structure) before selecting a style.
                  </div>
                )}
              </div>

              {/* Available Styles */}
              {showStyles && (
                <div className="border rounded-lg p-4 bg-gray-50">
                  <h4 className="font-medium mb-3">Available Musical Styles</h4>
                  {isFetchingStructuresStyles ? (
                    <div className="text-center py-4">Loading styles...</div>
                  ) : fetchStructuresStylesError ? (
                    <div className="p-3 bg-red-100 border border-red-300 rounded text-red-700">
                      {fetchStructuresStylesError}
                    </div>
                  ) : styles.length === 0 ? (
                    <div className="text-center py-4 text-gray-500">
                      No styles found
                    </div>
                  ) : (
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                      {styles.map((style, index) => (
                        <div key={style.id || index} className="p-3 bg-white border rounded">
                          <div className="flex justify-between items-center mb-2">
                            <div>
                              <h5 className="font-medium text-sm">{style.name}</h5>
                              <span className="text-xs text-gray-500">
                                Used in{" "}
                                {songStructures.filter((s) => s.styles.includes(style.name)).length}{" "}
                                structures
                              </span>
                            </div>
                            <button
                              className={`px-3 py-1 text-white rounded text-xs transition-colors ${
                                !stepCompleted.structure
                                  ? "bg-gray-300 cursor-not-allowed"
                                  : selectedStyle === style.name
                                  ? "bg-blue-500 hover:bg-blue-600"
                                  : "bg-green-500 hover:bg-green-600"
                              }`}
                              onClick={() => {
                                setSelectedStyle(style.name);
                                setStepCompleted((prev) => ({ ...prev, style: true }));
                                setCurrentStep(3);
                              }}
                              disabled={!stepCompleted.structure || generatingStyle === style.name}
                            >
                              {generatingStyle === style.name
                                ? "Processing..."
                                : selectedStyle === style.name
                                ? "Selected ✓"
                                : "Select Style"}
                            </button>
                          </div>
                          {style.description && (
                            <p className="text-xs text-gray-600">{style.description}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Step 3: Generate Song */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h3 className="text-lg font-medium text-purple-900 mb-2">Step 3: Generate Your Song</h3>
                <p className="text-sm text-purple-700 mb-4">
                  Now we&apos;ll run the complete automated workflow: generate 2 songs, download them, 
                  AI review for quality, and automatically retry up to 3 times until we get high-quality results.
                  This single process takes about 6-10 minutes and handles everything automatically - no more manual steps!
                </p>

                {selectedStyle && (
                  <div className="mb-4 p-3 bg-white border rounded">
                    <span className="text-sm font-medium">Selected Style: </span>
                    <span className="text-sm text-purple-700">{selectedStyle}</span>
                  </div>
                )}

                {!stepCompleted.style && (
                  <div className="p-3 bg-yellow-100 border border-yellow-300 rounded text-yellow-700 mb-4">
                    Please complete Step 2 (Select Style) before generating your song.
                  </div>
                )}

                {message && (
                  <div className="p-3 mb-4 bg-green-100 border border-green-300 rounded text-green-700">
                    <div className="font-medium mb-1">🎼 Automated Workflow Progress</div>
                    {message}
                  </div>
                )}

                {error && (
                  <div className="p-3 mb-4 bg-red-100 border border-red-300 rounded text-red-700">
                    <div className="font-medium mb-1">🎼 Workflow Error</div>
                    {error}
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    className={`flex-1 px-4 py-2 text-white rounded text-sm transition-colors ${
                      isLoading || !stepCompleted.style || !selectedStyle
                        ? "bg-gray-400 cursor-not-allowed"
                        : "bg-purple-500 hover:bg-purple-600"
                    }`}
                    onClick={() => {
                      if (selectedStyle) {
                        handleGenerateSong(selectedStyle);
                        setStepCompleted((prev) => ({ ...prev, song: true }));
                      }
                    }}
                    disabled={isLoading || !stepCompleted.style || !selectedStyle}
                  >
                    {isLoading && generatingStyle === selectedStyle
                      ? `🎼 Running Automated Workflow (${generatingStyle})...`
                      : "🎼 Generate & Review Songs (Automated)"}
                  </button>
                </div>
              </div>

              {/* Generated Songs Display */}
              {(stepCompleted.song || songFiles.length > 0) && (
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
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ModalSongs;
