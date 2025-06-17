// app/components/BookCard.tsx
import { useState } from "react";
import type { BibleBook } from "~/routes/main";
import { BookOpenIcon } from "./ui/icon";
import bookAbbreviations from "../../_constants/book-abrv.json";
import { supabase } from "~/lib/supabase";
import ChapterCard from "./CardChapter";

interface BookCardProps {
  book: BibleBook;
  viewMode: "grid" | "list";
}

export async function get_verse_range(bookAbbr: string, chapter: string) {
  if (!bookAbbr) {
    return { error: "Book abbreviation is required", data: null };
  }

  const abbrToFullName: { [key: string]: string } = {};
  for (const fullName in bookAbbreviations) {
    if (Object.prototype.hasOwnProperty.call(bookAbbreviations, fullName)) {
      abbrToFullName[
        bookAbbreviations[fullName as keyof typeof bookAbbreviations]
      ] = fullName;
    }
  }

  const bookName = abbrToFullName[bookAbbr.toUpperCase()];

  if (!bookName) {
    console.error(`Full book name not found for abbreviation: ${bookAbbr}`);
    return { error: `Invalid book abbreviation: ${bookAbbr}`, data: null };
  }
  try {
    console.log(
      `[get_verse_range] Fetching verse range for book: ${bookName} (abbr: ${bookAbbr}), chapter: ${chapter}`
    );
    const { data, error } = await supabase
      .from("song_structure_tbl")
      .select("verse_range")
      .eq("book_name", bookName)
      .eq("chapter", chapter);

    console.log("[get_verse_range] Supabase query result:", data);

    if (error) {
      console.error("Error fetching verse range:", error);
      return { error: error.message, data: null };
    }

    // Extract unique verse_range values from the data array
    const verseRanges = data?.map((item) => item.verse_range) || [];
    const uniqueVerseRanges = [...new Set(verseRanges)];
    return { error: null, data: uniqueVerseRanges };
  } catch (error) {
    console.error("Unexpected error fetching verse range:", error);
    let errorMessage = "An unexpected error occurred.";
    if (error instanceof Error) {
      errorMessage = error.message;
    }
    return { error: errorMessage, data: null };
  }
}

export async function generate_verse_range(bookAbbr: string, chapter: string) {
  if (!bookAbbr) {
    return { error: "Book abbreviation is required", data: null };
  }

  const abbrToFullName: { [key: string]: string } = {};
  for (const fullName in bookAbbreviations) {
    if (Object.prototype.hasOwnProperty.call(bookAbbreviations, fullName)) {
      abbrToFullName[
        bookAbbreviations[fullName as keyof typeof bookAbbreviations]
      ] = fullName;
    }
  }

  const bookName = abbrToFullName[bookAbbr.toUpperCase()];

  if (!bookName) {
    console.error(`Full book name not found for abbreviation: ${bookAbbr}`);
    return { error: `Invalid book abbreviation: ${bookAbbr}`, data: null };
  }

  try {
    console.log(
      `[generate_verse_range] Generating verse range for book: ${bookName} (abbr: ${bookAbbr}), chapter: ${chapter}`
    );
    const response = await fetch(
      `http://127.0.0.1:8000/generate-verse-ranges?book_name=${encodeURIComponent(
        bookName
      )}&book_chapter=${chapter}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Error response from server:", errorText);
      return {
        error: `Server error: ${response.status} ${response.statusText}`,
        data: null,
      };
    }

    const result = await response.json();
    console.log("[generate_verse_range] Server response:", result);

    return { error: null, data: result };
  } catch (error) {
    console.error("Error generating verse range:", error);
    let errorMessage = "Failed to generate verse range.";
    if (error instanceof Error) {
      errorMessage = error.message;
    }
    return { error: errorMessage, data: null };
  }
}

export default function BookCard({ book, viewMode }: BookCardProps) {
  const [showChapters, setShowChapters] = useState(false);
  const [verseRanges, setVerseRanges] = useState<Record<string, string[]>>({});
  const [loadingChapters, setLoadingChapters] = useState<Set<number>>(
    new Set()
  );
  const [expandedChapter, setExpandedChapter] = useState<number | null>(null);
  const [generatingChapters, setGeneratingChapters] = useState<Set<number>>(
    new Set()
  );
  const [generateErrors, setGenerateErrors] = useState<Record<string, string>>(
    {}
  );
  const bookAbbr =
    bookAbbreviations[book.name as keyof typeof bookAbbreviations] || "";

  const generateChapters = (maxChapter: number) => {
    return Array.from({ length: maxChapter }, (_, i) => i + 1);
  };
  const fetchVerseRanges = async (chapter: number) => {
    console.log("[BookCard.tsx] Fetching verse ranges for chapter:", chapter);
    if (verseRanges[chapter.toString()]?.length > 0) {
      return;
    }

    setLoadingChapters((prev) => new Set(prev).add(chapter));
    try {
      const result = await get_verse_range(bookAbbr, chapter.toString());
      if (result.error) {
        console.error("Error fetching verse ranges:", result.error);
      } else {
        setVerseRanges((prev) => ({
          ...prev,
          [chapter.toString()]: result.data || [],
        }));
      }
    } catch (error) {
      console.error("Error fetching verse ranges:", error);
    } finally {
      setLoadingChapters((prev) => {
        const newSet = new Set(prev);
        newSet.delete(chapter);
        return newSet;
      });
    }
  };

  const toggleChapterExpansion = async (chapter: number) => {
    if (expandedChapter === chapter) {
      setExpandedChapter(null);
    } else {
      setExpandedChapter(chapter);
      await fetchVerseRanges(chapter);
    }
  };

  const handleGenerateSong = (
    bookName: string,
    chapter: number,
    range: string
  ) => {
    console.log(
      `Generate song for ${bookName} Chapter ${chapter}, Verses: ${range}`
    );
  };

  const handleGenerateVerseRange = async (
    bookAbbr: string,
    chapter: string
  ) => {
    setGenerateErrors((prev) => {
      const newErrors = { ...prev };
      delete newErrors[chapter.toString()];
      return newErrors;
    });

    setGeneratingChapters((prev) => new Set(prev).add(parseInt(chapter, 10)));

    try {
      const result = await generate_verse_range(bookAbbr, chapter.toString());

      if (result.error) {
        setGenerateErrors((prev) => ({
          ...prev,
          [chapter.toString()]: result.error,
        }));
      } else {
        await fetchVerseRanges(parseInt(chapter, 10));
      }
    } catch (error) {
      console.error("Error generating verse range:", error);
      setGenerateErrors((prev) => ({
        ...prev,
        [chapter.toString()]: "Failed to generate verse range",
      }));
    } finally {
      setGeneratingChapters((prev) => {
        const newSet = new Set(prev);
        newSet.delete(parseInt(chapter, 10));
        return newSet;
      });
    }
  };

  if (viewMode === "list") {
    return (
      <div className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-slate-200">
        <div className="flex items-center justify-between">
          <div className="flex-grow">
            <h3 className="text-lg font-semibold text-sky-700">
              {book.name} {bookAbbr && `(${bookAbbr})`}
            </h3>{" "}
          </div>{" "}
          <button
            onClick={() => setShowChapters(!showChapters)}
            className="ml-4 px-4 py-2 bg-sky-500 text-white text-sm rounded-md hover:bg-sky-600 transition-colors flex items-center"
          >
            <BookOpenIcon className="w-4 h-4 mr-2" />
            View Progress
          </button>
        </div>{" "}
        {showChapters && (
          <div className="mt-4 max-h-60 overflow-y-auto border border-slate-200 rounded-md p-3 bg-slate-50">
            {" "}
            <div className="grid grid-cols-1 gap-2">
              {generateChapters(book.maxChapter).map((chapter) => (
                <ChapterCard
                  key={chapter}
                  chapter={chapter}
                  bookName={book.name}
                  bookAbbr={bookAbbr}
                  isExpanded={expandedChapter === chapter}
                  isLoading={loadingChapters.has(chapter)}
                  verseRanges={verseRanges[chapter.toString()] || []}
                  isGenerating={generatingChapters.has(chapter)}
                  generateError={generateErrors[chapter.toString()]}
                  onToggleExpansion={toggleChapterExpansion}
                  onGenerateVerseRange={handleGenerateVerseRange}
                  onGenerateSong={handleGenerateSong}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }
  return (
    <div className="bg-white p-5 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-slate-200 flex flex-col h-full">
      <h3 className="text-xl font-semibold text-sky-700 mb-2">
        {book.name} {bookAbbr && `(${bookAbbr})`}
      </h3>{" "}
      <div className="mt-auto">
        {" "}
        <button
          onClick={() => setShowChapters(!showChapters)}
          className="w-full px-4 py-2 bg-sky-500 text-white text-sm rounded-md hover:bg-sky-600 transition-colors flex items-center justify-center mb-2"
        >
          <BookOpenIcon className="w-4 h-4 mr-2" />
          View Progress
        </button>{" "}
        {showChapters && (
          <div className="max-h-60 overflow-y-auto border border-slate-200 rounded-md p-2 bg-slate-50">
            {" "}
            <div className="grid grid-cols-1 gap-2">
              {generateChapters(book.maxChapter).map((chapter) => (
                <ChapterCard
                  key={chapter}
                  chapter={chapter}
                  bookName={book.name}
                  bookAbbr={bookAbbr}
                  isExpanded={expandedChapter === chapter}
                  isLoading={loadingChapters.has(chapter)}
                  verseRanges={verseRanges[chapter.toString()] || []}
                  isGenerating={generatingChapters.has(chapter)}
                  generateError={generateErrors[chapter.toString()]}
                  onToggleExpansion={toggleChapterExpansion}
                  onGenerateVerseRange={handleGenerateVerseRange}
                  onGenerateSong={handleGenerateSong}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
