interface VerseRangeCardProps {
  range: string;
  bookName: string;
  chapter: number;
  onGenerateSong: (bookName: string, chapter: number, range: string) => void;
}

const VerseRangeCard = ({
  range,
  bookName,
  chapter,
  onGenerateSong,
}: VerseRangeCardProps) => {
  return (
    <div className="p-2 bg-sky-50 border border-sky-200 rounded-md text-xs text-slate-700 shadow-sm">
      <div className="flex justify-between items-center">
        <span>Verses: {range}</span>
        <button
          className="ml-2 px-2 py-1 bg-green-500 text-white rounded text-xs hover:bg-green-600 transition-colors"
          onClick={() => onGenerateSong(bookName, chapter, range)}
        >
          Generate Song
        </button>
      </div>
    </div>
  );
};

export default VerseRangeCard;
