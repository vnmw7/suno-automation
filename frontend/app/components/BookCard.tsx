// app/components/BookCard.tsx
import { useState } from "react";
import type { BibleBook } from "~/routes/main";
import { BookOpenIcon, ChevronDownIcon, ChevronUpIcon } from "./ui/icon";

interface BookCardProps {
  book: BibleBook;
  onViewDetails: () => void;
  viewMode: "grid" | "list";
}

export default function BookCard({
  book,
  onViewDetails,
  viewMode,
}: BookCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      setIsExpanded(!isExpanded);
    }
  };

  if (viewMode === "list") {
    return (
      <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-slate-200">
        <div className="flex items-center justify-between">
          <div
            className="flex-grow cursor-pointer"
            onClick={() => setIsExpanded(!isExpanded)}
            onKeyDown={handleKeyDown}
            role="button"
            tabIndex={0}
          >
            {" "}
            <h3 className="text-lg font-semibold text-sky-700">{book.name}</h3>
            <p className="text-sm text-slate-500">{book.testament}</p>
            <p className="text-sm text-slate-600 mt-1">
              Chapters: {book.chapters}
            </p>
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            aria-expanded={isExpanded}
            aria-controls={`book-details-${book.id}`}
            className="ml-4 px-4 py-2 bg-sky-500 text-white text-sm rounded-md hover:bg-sky-600 transition-colors flex items-center"
          >
            {isExpanded ? (
              <ChevronUpIcon className="w-4 h-4 mr-2" />
            ) : (
              <ChevronDownIcon className="w-4 h-4 mr-2" />
            )}
            {isExpanded ? "Hide" : "Show"} Details
          </button>
        </div>
        {isExpanded && (
          <div
            id={`book-details-${book.id}`}
            className="mt-4 pt-4 border-t border-slate-200"
          >
            <h4 className="font-semibold text-slate-700 mb-1">Summary:</h4>
            <p className="text-slate-600 leading-relaxed text-sm sm:text-base mb-2">
              {book.summary}
            </p>
            {book.author && (
              <div className="mb-2">
                <h4 className="font-semibold text-slate-700 mb-0.5">Author:</h4>
                <p className="text-slate-600 text-sm sm:text-base">
                  {book.author}
                </p>
              </div>
            )}
            {book.writtenDate && (
              <div>
                <h4 className="font-semibold text-slate-700 mb-0.5">
                  Approx. Written Date:
                </h4>
                <p className="text-slate-600 text-sm sm:text-base">
                  {book.writtenDate}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Grid View - remains the same, uses onViewDetails for modal
  return (
    <div className="bg-white p-5 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-slate-200 flex flex-col h-full">
      <h3 className="text-xl font-semibold text-sky-700 mb-2">{book.name}</h3>{" "}
      <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
        {book.testament}
      </p>
      <p className="text-sm text-slate-600 mb-3 flex-grow line-clamp-3">
        {book.summary}
      </p>
      <div className="text-sm text-slate-500 mb-4">
        <span className="font-medium">Chapters:</span> {book.chapters}
      </div>
      <button
        onClick={onViewDetails} // This will trigger the modal in grid view
        className="mt-auto w-full px-4 py-2 bg-sky-500 text-white text-sm rounded-md hover:bg-sky-600 transition-colors flex items-center justify-center"
      >
        <BookOpenIcon className="w-4 h-4 mr-2" />
        View Details
      </button>
    </div>
  );
}
