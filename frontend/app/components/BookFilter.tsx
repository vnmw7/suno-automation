interface BookFilterProps {
  bookNames: string[];
  selectedBookName: string | null;
  onSelectBookName: (bookName: string) => void;
}

export default function BookFilter({
  bookNames,
  selectedBookName,
  onSelectBookName,
}: BookFilterProps) {
  return (
    <div>
      <h3 className="text-md font-semibold mb-2 text-slate-600">Book</h3>
      <div className="space-y-1.5">
        {bookNames.map((bookName) => (
          <button
            key={bookName}
            onClick={() => onSelectBookName(bookName)}
            className={`w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors
              ${
                selectedBookName === bookName
                  ? "bg-sky-600 text-white font-medium"
                  : "bg-slate-100 hover:bg-slate-200 text-slate-700"
              }`}
          >
            {bookName}
          </button>
        ))}
      </div>
    </div>
  );
}
