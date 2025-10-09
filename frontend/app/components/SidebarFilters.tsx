// app/components/SidebarFilters.tsx
import BookFilter from "./BookFilter"; // Changed from GenreFilter
import { FilterIcon } from "./ui/icon";

interface FilterData {
  // testaments: ("Old Testament" | "New Testament")[]; // Removed
  bookNames: string[]; // Changed from genres
}

export interface ActiveFilters {
  // Exporting for use in other components if needed
  bookName: string | null; // Changed from genre
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
    <aside className="flex w-full flex-col gap-6 rounded-lg border border-neutral-200 bg-white p-4 md:w-80 md:shrink-0 md:sticky md:top-8 md:max-h-[calc(100vh-4rem)] md:overflow-y-auto">
      <h2 className="flex items-center border-b border-neutral-200 pb-3 text-lg font-semibold text-neutral-800">
        <FilterIcon className="mr-2 h-5 w-5 text-neutral-500" />
        Filter Books
      </h2>
      <BookFilter
        bookNames={filters.bookNames}
        selectedBookName={activeFilters.bookName}
        onSelectBookName={(bookName: string) =>
          onFilterChange({
            bookName: activeFilters.bookName === bookName ? null : bookName,
          })
        }
      />
      <button
        type="button"
        onClick={() =>
          onFilterChange({
            bookName: null,
          })
        }
        className="w-full rounded-md border border-neutral-300 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-100"
      >
        Clear All Filters
      </button>
    </aside>
  );
}

