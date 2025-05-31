// app/components/BookCard.tsx
import type { BibleBook } from "~/routes/main"; // Ensure this path is correct
import { BookOpenIcon } from "./ui/icon"; // Assuming you have this icon

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
  if (viewMode === "list") {
    return (
      <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-slate-200 flex items-center justify-between">
        <div className="flex-grow">
          <h3 className="text-lg font-semibold text-sky-700">{book.name}</h3>
          <p className="text-sm text-slate-500">
            {book.testament} - {book.genre}
          </p>
          <p className="text-sm text-slate-600 mt-1">
            Chapters: {book.chapters}
          </p>
        </div>
        <button
          onClick={onViewDetails}
          className="ml-4 px-4 py-2 bg-sky-500 text-white text-sm rounded-md hover:bg-sky-600 transition-colors flex items-center"
        >
          <BookOpenIcon className="w-4 h-4 mr-2" />
          View Details
        </button>
      </div>
    );
  }

  // Grid View
  return (
    <div className="bg-white p-5 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-slate-200 flex flex-col h-full">
      <h3 className="text-xl font-semibold text-sky-700 mb-2">{book.name}</h3>
      <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
        {book.testament} &bull; {book.genre}
      </p>
      <p className="text-sm text-slate-600 mb-3 flex-grow line-clamp-3">
        {book.summary}
      </p>
      <div className="text-sm text-slate-500 mb-4">
        <span className="font-medium">Chapters:</span> {book.chapters}
      </div>
      <button
        onClick={onViewDetails}
        className="mt-auto w-full px-4 py-2 bg-sky-500 text-white text-sm rounded-md hover:bg-sky-600 transition-colors flex items-center justify-center"
      >
        <BookOpenIcon className="w-4 h-4 mr-2" />
        View Details
      </button>
    </div>
  );
}
