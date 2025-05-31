// app/components/TestamentFilter.tsx
import type { BibleBook } from "~/routes/main"; // Ensure this path is correct

interface TestamentFilterProps {
  testaments: ("Old Testament" | "New Testament")[];
  selectedTestament: BibleBook["testament"] | null;
  onSelectTestament: (testament: "Old Testament" | "New Testament") => void;
}

export default function TestamentFilter({
  testaments,
  selectedTestament,
  onSelectTestament,
}: TestamentFilterProps) {
  return (
    <div>
      <h3 className="text-md font-semibold mb-2 text-slate-600">Testament</h3>
      <div className="space-y-1.5">
        {testaments.map((testament) => (
          <button
            key={testament}
            onClick={() => onSelectTestament(testament)}
            className={`w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors
              ${
                selectedTestament === testament
                  ? "bg-sky-600 text-white font-medium"
                  : "bg-slate-100 hover:bg-slate-200 text-slate-700"
              }`}
          >
            {testament}
          </button>
        ))}
      </div>
    </div>
  );
}
