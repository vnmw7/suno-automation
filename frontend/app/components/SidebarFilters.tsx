// app/components/SidebarFilters.tsx
import TestamentFilter from "./TestamentFilter";
import BookFilter from "./BookFilter"; // Changed from GenreFilter
import ChaptersFilter from "./ChaptersFilter";
import { FilterIcon } from "./ui/icon";
import type { BibleBook } from "~/routes/main"; // Ensure this path is correct

interface FilterData {
  testaments: ("Old Testament" | "New Testament")[];
  bookNames: string[]; // Changed from genres
  maxChapters: number;
}

export interface ActiveFilters {
  // Exporting for use in other components if needed
  testament: BibleBook["testament"] | null; // Use the type from BibleBook
  bookName: string | null; // Changed from genre
  chapterRange: [number, number];
}

interface SidebarFiltersProps {
  filters: FilterData;
  activeFilters: ActiveFilters;
  onFilterChange: (newFilter: Partial<ActiveFilters>) => void;
}

export default function SidebarFilters({
  filters,
  activeFilters,
  onFilterChange,
}: SidebarFiltersProps) {
  return (
    <aside className="w-full md:w-1/4 space-y-6 p-4 bg-white rounded-lg shadow-sm border border-slate-200 self-start md:sticky md:top-8 md:max-h-[calc(100vh-4rem)] md:overflow-y-auto">
      <h2 className="text-xl font-semibold text-slate-700 border-b pb-2 mb-4 flex items-center sticky top-0 bg-white z-10">
        <FilterIcon className="w-5 h-5 mr-2 text-sky-600" />
        Filter Books
      </h2>
      <TestamentFilter
        testaments={filters.testaments}
        selectedTestament={activeFilters.testament}
        onSelectTestament={(testament: "Old Testament" | "New Testament") =>
          onFilterChange({
            testament: activeFilters.testament === testament ? null : testament,
          })
        }
      />
      <BookFilter
        bookNames={filters.bookNames}
        selectedBookName={activeFilters.bookName}
        onSelectBookName={(bookName: string) =>
          onFilterChange({
            bookName: activeFilters.bookName === bookName ? null : bookName,
          })
        }
      />
      <ChaptersFilter
        maxChapters={filters.maxChapters}
        currentRange={activeFilters.chapterRange}
        onRangeChange={(range: [number, number]) =>
          onFilterChange({ chapterRange: range })
        }
      />
      <button
        onClick={() =>
          onFilterChange({
            testament: null,
            bookName: null, // Corrected: was genre
            chapterRange: [0, filters.maxChapters],
          })
        }
        className="w-full mt-4 px-4 py-2 border border-slate-300 text-slate-700 rounded-md hover:bg-slate-100 text-sm"
      >
        Clear All Filters
      </button>
    </aside>
  );
}
