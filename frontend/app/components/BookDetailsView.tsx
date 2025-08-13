// app/components/BookDetailsView.tsx
import { useEffect, useRef } from "react";
import type { BibleBook } from "~/routes/main";

interface BookDetailsViewProps {
  book: BibleBook;
  onClose: () => void;
}

export default function BookDetailsView({
  book,
  onClose,
}: BookDetailsViewProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  // Handle Escape key press
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscKey);
    return () => {
      document.removeEventListener("keydown", handleEscKey);
    };
  }, [onClose]);

  // Focus the dialog when it mounts
  useEffect(() => {
    if (dialogRef.current) {
      dialogRef.current.focus();
    }
  }, []); // Empty dependency array: run once on mount

  return (
    <div
      ref={dialogRef}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="book-details-title"
      tabIndex={-1} // Make the div focusable
    >
      <div
        className="bg-white p-6 sm:p-8 rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto relative border border-slate-200"
        role="document"
      >
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-slate-400 hover:text-slate-600 transition-colors p-1 rounded-full hover:bg-slate-100"
          aria-label="Close details"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="w-6 h-6"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
        <h2
          className="text-3xl font-bold text-sky-700 mb-3"
          id="book-details-title"
        >
          {book.name}
        </h2>{" "}
        {/* <p className="text-sm text-slate-500 mb-1">{book.testament}</p>
        <p className="text-sm text-slate-500 mb-6">Chapters: {book.chapters}</p>
        <div className="space-y-4">
          <div>
            <h4 className="font-semibold text-slate-700 mb-1">Summary:</h4>
            <p className="text-slate-600 leading-relaxed text-sm sm:text-base">
              {book.summary}
            </p>
          </div>

          {book.author && (
            <div>
              <h4 className="font-semibold text-slate-700 mb-1">Author:</h4>
              <p className="text-slate-600 text-sm sm:text-base">
                {book.author}
              </p>
            </div>
          )}

          {book.writtenDate && (
            <div>
              <h4 className="font-semibold text-slate-700 mb-1">
                Approx. Written Date:
              </h4>
              <p className="text-slate-600 text-sm sm:text-base">
                {book.writtenDate}
              </p>
            </div>
          )}
        </div> */}
        <button
          onClick={onClose}
          className="mt-8 w-full px-4 py-2.5 bg-sky-600 text-white rounded-md hover:bg-sky-700 transition-colors font-medium text-sm sm:text-base"
        >
          Close
        </button>
      </div>
    </div>
  );
}
