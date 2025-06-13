// app/routes/bible.books.tsx
import { useState } from "react";
import { useLoaderData, MetaFunction } from "@remix-run/react";
import type { LoaderFunctionArgs } from "@remix-run/node";
import SidebarFilters from "~/components/SidebarFilters";
import BookCard from "../components/BookCard";
import BookDetailsView from "../components/BookDetailsView";
import { ListIcon, ViewGridIcon, BookOpenIcon } from "../components/ui/icon";
import { supabase } from "~/lib/supabase";
import {
  isCanonicalBook,
  getFullBookName,
} from "../../_constants/canonical-books";

export interface BibleBook {
  id: string;
  name: string;
  maxChapter: number;
}

interface FilterData {
  bookNames: string[];
}

export const meta: MetaFunction = () => {
  return [
    { title: "Automation" },
    {
      name: "description",
      content:
        "Explore the books of the Bible with filters for testament, genre, and chapters.",
    },
  ];
};

export async function loader({ request }: LoaderFunctionArgs) {
  try {
    const url = new URL(request.url);
    const queryFromUrl = url.searchParams.get("query") || "";
    const viewModeFromUrl =
      (url.searchParams.get("viewMode") as "grid" | "list") || "list";
    console.log(
      "[main.tsx] Fetching unique book names from Supabase using RPC 'get_unique_book_names_from_verses'..."
    );
    const { data: uniqueBooksData, error: rpcError } = await supabase.rpc(
      "get_unique_book_names_from_verses"
    );
    console.log(
      "[main.tsx] Supabase RPC call completed, processing results and filtering for 66 canonical books..."
    );
    console.log(uniqueBooksData);
    if (rpcError) {
      console.error("Supabase RPC error:", rpcError);
      return {
        books: [],
        filters: { bookNames: [] },
        totalPages: 0,
        currentPage: 1,
        query: queryFromUrl,
        viewMode: viewModeFromUrl,
      };
    }
    if (!uniqueBooksData || uniqueBooksData.length === 0) {
      console.warn(
        "No unique book names found from RPC call 'get_unique_book_names_from_verses'."
      );
      return {
        books: [],
        filters: { bookNames: [] },
        totalPages: 0,
        currentPage: 1,
        query: queryFromUrl,
        viewMode: viewModeFromUrl,
      };
    }
    const databaseBooks: BibleBook[] = [];
    const bookNamesArray: string[] = [];
    for (const item of uniqueBooksData) {
      console.log("[main.tsx] Processing item from RPC:", item);
      if (item && item.book_name && isCanonicalBook(item.book_name)) {
        const fullBookName = getFullBookName(item.book_name);
        databaseBooks.push({
          id: item.book_name, // Keep the abbreviated ID for database consistency
          name: fullBookName, // Use the full name for display
          maxChapter: item.max_chapter_number || 1,
        });
        bookNamesArray.push(fullBookName);
      }
    }

    console.log("Processed canonical books from RPC:", databaseBooks.length);
    console.log("Canonical books found:", bookNamesArray);
    const filterData: FilterData = {
      bookNames: bookNamesArray,
    };

    return {
      books: databaseBooks,
      filters: filterData,
      totalPages: 1,
      currentPage: 1,
      query: queryFromUrl,
      viewMode: viewModeFromUrl,
    };
  } catch (error) {
    console.error("Error in loader fetching books:", error);

    let queryFromUrl = "";
    let viewModeFromUrl: "grid" | "list" = "list";
    if (request) {
      try {
        const url = new URL(request.url);
        queryFromUrl = url.searchParams.get("query") || "";
        viewModeFromUrl =
          (url.searchParams.get("viewMode") as "grid" | "list") || "list";
      } catch (e) {
        console.error("Error parsing request URL in catch block:", e);
      }
    }
    return {
      books: [],
      filters: { bookNames: [] },
      totalPages: 0,
      currentPage: 1,
      query: queryFromUrl,
      viewMode: viewModeFromUrl,
    };
  }
}

export default function BibleBooksPage() {
  const { books, filters } = useLoaderData<typeof loader>();
  const [detailsViewBook, setDetailsViewBook] = useState<BibleBook | null>(
    null
  );
  const [viewMode, setViewMode] = useState<"grid" | "list">("list");

  const [activeFilters, setActiveFilters] = useState<{
    bookName: string | null;
  }>({
    bookName: null,
  });

  const filteredBooks = books.filter((book: BibleBook) => {
    let pass = true;
    if (activeFilters.bookName && book.name !== activeFilters.bookName)
      pass = false;
    return pass;
  });

  return (
    <div className="min-h-screen flex flex-col p-4 sm:p-6 md:p-8">
      <header className="mb-8 text-center">
        <div className="inline-flex items-center text-sky-700 mb-2">
          <BookOpenIcon className="w-10 h-10 mr-3" />
          <h1 className="text-4xl font-bold">Song Automation</h1>
        </div>
        <p className="text-slate-600">This is for automation purposes only.</p>
      </header>

      <div className="flex flex-col md:flex-row gap-8 flex-grow">
        {" "}
        <SidebarFilters
          filters={filters}
          activeFilters={activeFilters}
          onFilterChange={(newFilters) =>
            setActiveFilters((prev) => ({ ...prev, ...newFilters }))
          }
        />
        <main className="w-full md:w-3/4">
          {/* Sort & View Options Bar */}
          <div className="bg-white p-3 rounded-md shadow-sm flex justify-between items-center mb-6 border border-slate-200">
            <div className="flex gap-3"> </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600 mr-2">
                {filteredBooks.length} books found
              </span>
              <button
                title="Grid View"
                onClick={() => setViewMode("grid")}
                className={`p-2 rounded ${
                  viewMode === "grid"
                    ? "bg-sky-600 text-white"
                    : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                }`}
              >
                <ViewGridIcon className="w-5 h-5" />
              </button>
              <button
                title="List View"
                onClick={() => setViewMode("list")}
                className={`p-2 rounded ${
                  viewMode === "list"
                    ? "bg-sky-600 text-white"
                    : "bg-slate-100 hover:bg-slate-200 text-slate-700"
                }`}
              >
                <ListIcon className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Books Grid/List */}
          {filteredBooks.length > 0 ? (
            <div
              className={`grid gap-6 ${
                viewMode === "grid"
                  ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                  : "grid-cols-1"
              }`}
            >
              {filteredBooks.map((book: BibleBook) => (
                <BookCard key={book.id} book={book} viewMode={viewMode} />
              ))}
            </div>
          ) : (
            <div className="text-center py-10 text-slate-500">
              <p className="text-xl">No books match your current filters.</p>
              <p>Try adjusting your search criteria.</p>
            </div>
          )}
          {/* Pagination could go here if many books */}
        </main>
      </div>

      {detailsViewBook && (
        <BookDetailsView
          book={detailsViewBook}
          onClose={() => setDetailsViewBook(null)}
        />
      )}
    </div>
  );
}
