import VerseRangeCard from "./CardVerseRange";

interface ChapterCardProps {
  chapter: number;
  bookName: string;
  bookAbbr: string;
  isExpanded: boolean;
  isLoading: boolean;
  verseRanges: string[];
  isGenerating: boolean;
  generateError?: string;
  onToggleExpansion: (chapter: number) => void;
  onGenerateVerseRange: (bookAbbr: string, chapter: string) => void;
  onGenerateSong: (bookName: string, chapter: number, range: string) => void;
}

const ChapterCard = ({
  chapter,
  bookName,
  bookAbbr,
  isExpanded,
  isLoading,
  verseRanges,
  isGenerating,
  generateError,
  onToggleExpansion,
  onGenerateVerseRange,
  onGenerateSong,
}: ChapterCardProps) => {
  return (
    <div className="bg-white border border-slate-300 rounded-lg shadow-sm">
      <button
        onClick={() => onToggleExpansion(chapter)}
        className="w-full p-3 hover:bg-sky-50 hover:border-sky-300 transition-colors cursor-pointer text-left focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 rounded-lg"
      >
        <div className="flex justify-between items-center">
          <div className="text-sm font-medium text-sky-700">
            Chapter {chapter}
          </div>
          <div className="text-xs text-slate-400">{isExpanded ? "▼" : "▶"}</div>
        </div>
      </button>
      {isExpanded && (
        <div className="px-3 pb-3 pt-2">
          {isLoading ? (
            <div className="text-center py-4 text-slate-500 text-xs">
              Loading verse ranges...
            </div>
          ) : verseRanges ? (
            <div className="space-y-2">
              {verseRanges.length > 0 ? (
                verseRanges.map((range, index) => (
                  <VerseRangeCard
                    key={index}
                    range={range}
                    bookName={bookName}
                    chapter={chapter}
                    onGenerateSong={onGenerateSong}
                  />
                ))
              ) : (
                <div className="p-2 text-xs text-slate-500">
                  {generateError ? (
                    <div className="mb-2 p-2 bg-red-50 border border-red-200 rounded-md text-red-700">
                      Error: {generateError}
                    </div>
                  ) : null}
                  <button
                    className="px-3 py-2 bg-sky-500 text-white rounded-md hover:bg-sky-600 hover:scale-105 transform transition-all duration-200 ease-in-out shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                    onClick={() =>
                      onGenerateVerseRange(bookAbbr, chapter.toString())
                    }
                    disabled={isGenerating}
                  >
                    {isGenerating ? "Generating..." : "Generate Verse Range"}
                  </button>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};

export default ChapterCard;
