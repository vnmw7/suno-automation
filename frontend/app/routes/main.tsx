// app/routes/bible.books.tsx
import { useState } from "react";
import { useLoaderData, MetaFunction } from "@remix-run/react";
import type { LoaderFunctionArgs } from "@remix-run/node";
import SidebarFilters from "../components/SidebarFilters";
import BookCard from "../components/BookCard";
import BookDetailsView from "../components/BookDetailsView";
import SongSidebar, { type Song as SongItem } from "../components/SongSidebar";
import { ListIcon, ViewGridIcon, BookOpenIcon } from "../components/ui/icon";
import { supabase } from "../lib/supabase";
import {
  isCanonicalBook,
  getFullBookName,
} from "../constants/canonical-books";

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
        songs: [],
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
        songs: [],
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
          id: item.book_name,
          name: fullBookName,
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

    let songs: SongItem[] = [];
    try {
      const songsApiUrl = new URL("/api/list-songs", request.url);
      const songsResponse = await fetch(songsApiUrl.toString(), {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (songsResponse.ok) {
        const songsPayload = await songsResponse.json();
        songs =
          songsPayload.files?.map((fileName: string) => ({
            id: fileName,
            name: fileName.replace(/\.mp3$/, "").replace(/_/g, " "),
            fileName,
          })) ?? [];
      } else {
        console.error(
          "[main.tsx] Failed to fetch songs:",
          songsResponse.statusText
        );
      }
    } catch (songsError) {
      console.error("[main.tsx] Error fetching songs:", songsError);
    }

    return {
      books: databaseBooks,
      filters: filterData,
      songs,
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
      songs: [],
      totalPages: 0,
      currentPage: 1,
      query: queryFromUrl,
      viewMode: viewModeFromUrl,
    };
  }
}
export default function BibleBooksPage() {
  const { books, filters, songs } = useLoaderData<typeof loader>();
  const [detailsViewBook, setDetailsViewBook] = useState<BibleBook | null>(
    null
  );
  const [viewMode, setViewMode] = useState<"grid" | "list">("list");

  const [activeFilters, setActiveFilters] = useState<{
    bookName: string | null;
  }>({
    bookName: null,
  });
  const [selectedSong, setSelectedSong] = useState<SongItem | null>(null);

  const filteredBooks = books.filter((book: BibleBook) => {
    let pass = true;
    if (activeFilters.bookName && book.name !== activeFilters.bookName)
      pass = false;
    return pass;
  });

  return (
    <div className="min-h-screen flex flex-col bg-neutral-50 p-4 sm:p-6 md:p-8">
      <header className="mb-8 text-center space-y-3">
        <div className="inline-flex items-center justify-center gap-3 text-neutral-800">
          <BookOpenIcon className="w-10 h-10 text-neutral-500" />
          <h1 className="text-3xl font-semibold text-neutral-900">Song Automation</h1>
        </div>
        <p className="text-neutral-600">This is for automation purposes only.</p>
      </header>

      <div className="flex flex-col gap-6 md:flex-row md:items-start md:gap-8">
        <div className="order-2 md:order-1">
          <SidebarFilters
            filters={filters}
            activeFilters={activeFilters}
            onFilterChange={(newFilters) =>
              setActiveFilters((prev) => ({ ...prev, ...newFilters }))
            }
          />
        </div>

        <main className="order-1 w-full md:order-2 md:flex-1">
          <div className="mb-6 flex flex-col gap-3 rounded-lg border border-neutral-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-col gap-1 text-sm text-neutral-600">
              <span>{filteredBooks.length} books found</span>
              {selectedSong && (
                <span className="text-neutral-500">
                  Selected song:
                  <span className="ml-1 font-medium text-neutral-700">
                    {selectedSong.name}
                  </span>
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                title="Grid View"
                onClick={() => setViewMode("grid")}
                className={`h-9 w-9 rounded-md border border-neutral-300 text-neutral-700 transition-colors ${
                  viewMode === "grid"
                    ? "bg-neutral-900 text-white border-neutral-900"
                    : "bg-neutral-100 hover:bg-neutral-200"
                }`}
                aria-pressed={viewMode === "grid"}
              >
                <ViewGridIcon className="h-5 w-5" />
              </button>
              <button
                title="List View"
                onClick={() => setViewMode("list")}
                className={`h-9 w-9 rounded-md border border-neutral-300 text-neutral-700 transition-colors ${
                  viewMode === "list"
                    ? "bg-neutral-900 text-white border-neutral-900"
                    : "bg-neutral-100 hover:bg-neutral-200"
                }`}
                aria-pressed={viewMode === "list"}
              >
                <ListIcon className="h-5 w-5" />
              </button>
            </div>
          </div>

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
            <div className="py-10 text-center text-neutral-500">
              <p className="text-xl">No books match your current filters.</p>
              <p>Try adjusting your search criteria.</p>
            </div>
          )}
        </main>

        <div className="order-3 md:order-3">
          <SongSidebar
            songs={songs}
            selectedSong={selectedSong}
            onSongSelect={setSelectedSong}
          />
        </div>
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
