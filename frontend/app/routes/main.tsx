// app/routes/bible.books.tsx
import { useState } from "react";
import { useLoaderData, MetaFunction } from "@remix-run/react";
import SidebarFilters from "~/components/SidebarFilters";
import BookCard from "../components/BookCard";
import BookDetailsView from "../components/BookDetailsView";
import { Dropdown } from "../components/ui/dropdown";
import { ListIcon, ViewGridIcon, BookOpenIcon } from "../components/ui/icon";
import { supabase } from "~/lib/supabase";

export interface BibleBook {
  id: string;
  name: string;
  testament: "Old Testament" | "New Testament";
  chapters: number;
  summary: string;
  author?: string;
  writtenDate?: string;
}

interface FilterData {
  testaments: ("Old Testament" | "New Testament")[];
  bookNames: string[];
}

const bibleBooksNIV: BibleBook[] = [
  {
    id: "gen",
    name: "Genesis",
    testament: "Old Testament",
    chapters: 50,
    summary: "Creation, early human history, and the patriarchs.",
    author: "Moses (traditionally)",
  },
  {
    id: "exo",
    name: "Exodus",
    testament: "Old Testament",
    chapters: 40,
    summary: "Israel's deliverance from Egypt and the giving of the Law.",
    author: "Moses (traditionally)",
  },
  {
    id: "lev",
    name: "Leviticus",
    testament: "Old Testament",
    chapters: 27,
    summary: "Laws and regulations for worship and holy living.",
    author: "Moses (traditionally)",
  },
  {
    id: "num",
    name: "Numbers",
    testament: "Old Testament",
    chapters: 36,
    summary: "The Israelites' journey through the wilderness.",
    author: "Moses (traditionally)",
  },
  {
    id: "deu",
    name: "Deuteronomy",
    testament: "Old Testament",
    chapters: 34,
    summary: "Moses' farewell speeches and a restatement of the Law.",
    author: "Moses (traditionally)",
  },
  {
    id: "jos",
    name: "Joshua",
    testament: "Old Testament",
    chapters: 24,
    summary: "The conquest and division of Canaan.",
  },
  {
    id: "jud",
    name: "Judges",
    testament: "Old Testament",
    chapters: 21,
    summary: "The period of the judges in Israel.",
  },
  {
    id: "rut",
    name: "Ruth",
    testament: "Old Testament",
    chapters: 4,
    summary: "A story of loyalty and redemption.",
  },
  {
    id: "1sa",
    name: "1 Samuel",
    testament: "Old Testament",
    chapters: 31,
    summary: "The rise of the Israelite monarchy (Saul and David).",
  },
  {
    id: "2sa",
    name: "2 Samuel",
    testament: "Old Testament",
    chapters: 24,
    summary: "The reign of King David.",
  },
  {
    id: "1ki",
    name: "1 Kings",
    testament: "Old Testament",
    chapters: 22,
    summary: "The reign of Solomon and the division of the kingdom.",
  },
  {
    id: "2ki",
    name: "2 Kings",
    testament: "Old Testament",
    chapters: 25,
    summary: "The history of the divided kingdom until the exile.",
  },
  {
    id: "1ch",
    name: "1 Chronicles",
    testament: "Old Testament",
    chapters: 29,
    summary:
      "A priestly perspective on the history of Israel, focusing on David.",
  },
  {
    id: "2ch",
    name: "2 Chronicles",
    testament: "Old Testament",
    chapters: 36,
    summary:
      "A priestly perspective on the history of Judah, focusing on Solomon and the Temple.",
  },
  {
    id: "ezr",
    name: "Ezra",
    testament: "Old Testament",
    chapters: 10,
    summary: "The return from exile and the rebuilding of the Temple.",
  },
  {
    id: "neh",
    name: "Nehemiah",
    testament: "Old Testament",
    chapters: 13,
    summary: "The rebuilding of Jerusalem's walls.",
  },
  {
    id: "est",
    name: "Esther",
    testament: "Old Testament",
    chapters: 10,
    summary: "God's deliverance of the Jewish people through Esther.",
  },
  {
    id: "job",
    name: "Job",
    testament: "Old Testament",
    chapters: 42,
    summary: "A righteous man's suffering and his struggle with faith.",
  },
  {
    id: "psa",
    name: "Psalms",
    testament: "Old Testament",
    chapters: 150,
    summary: "A collection of prayers, hymns, and poems.",
  },
  {
    id: "pro",
    name: "Proverbs",
    testament: "Old Testament",
    chapters: 31,
    summary: "A collection of wise sayings and instructions.",
  },
  {
    id: "ecc",
    name: "Ecclesiastes",
    testament: "Old Testament",
    chapters: 12,
    summary: "Reflections on the meaning of life.",
  },
  {
    id: "sos",
    name: "Song of Solomon",
    testament: "Old Testament",
    chapters: 8,
    summary: "A love poem celebrating marital love.",
  },
  {
    id: "isa",
    name: "Isaiah",
    testament: "Old Testament",
    chapters: 66,
    summary: "Prophecies about judgment, comfort, and the coming Messiah.",
  },
  {
    id: "jer",
    name: "Jeremiah",
    testament: "Old Testament",
    chapters: 52,
    summary: "Prophecies of judgment on Judah and calls for repentance.",
  },
  {
    id: "lam",
    name: "Lamentations",
    testament: "Old Testament",
    chapters: 5,
    summary: "Laments over the destruction of Jerusalem.",
  },
  {
    id: "eze",
    name: "Ezekiel",
    testament: "Old Testament",
    chapters: 48,
    summary: "Prophecies of judgment and future restoration for Israel.",
  },
  {
    id: "dan",
    name: "Daniel",
    testament: "Old Testament",
    chapters: 12,
    summary: "Stories of faithfulness in exile and apocalyptic visions.",
  },
  {
    id: "hos",
    name: "Hosea",
    testament: "Old Testament",
    chapters: 14,
    summary: "God's unfailing love for unfaithful Israel.",
  },
  {
    id: "joe",
    name: "Joel",
    testament: "Old Testament",
    chapters: 3,
    summary: "The Day of the Lord and the outpouring of the Spirit.",
  },
  {
    id: "amo",
    name: "Amos",
    testament: "Old Testament",
    chapters: 9,
    summary: "Prophecies of social justice and judgment.",
  },
  {
    id: "oba",
    name: "Obadiah",
    testament: "Old Testament",
    chapters: 1,
    summary: "Judgment on Edom.",
  },
  {
    id: "jon",
    name: "Jonah",
    testament: "Old Testament",
    chapters: 4,
    summary: "A prophet's reluctance and God's compassion for Nineveh.",
  },
  {
    id: "mic",
    name: "Micah",
    testament: "Old Testament",
    chapters: 7,
    summary: "Prophecies of judgment and hope for a righteous ruler.",
  },
  {
    id: "nah",
    name: "Nahum",
    testament: "Old Testament",
    chapters: 3,
    summary: "Prophecy of Nineveh's destruction.",
  },
  {
    id: "hab",
    name: "Habakkuk",
    testament: "Old Testament",
    chapters: 3,
    summary: "A prophet's dialogue with God about injustice and faith.",
  },
  {
    id: "zep",
    name: "Zephaniah",
    testament: "Old Testament",
    chapters: 3,
    summary: "The Day of the Lord and future blessing.",
  },
  {
    id: "hag",
    name: "Haggai",
    testament: "Old Testament",
    chapters: 2,
    summary: "Encouragement to rebuild the Temple.",
  },
  {
    id: "zec",
    name: "Zechariah",
    testament: "Old Testament",
    chapters: 14,
    summary: "Visions of the future and the coming Messiah.",
  },
  {
    id: "mal",
    name: "Malachi",
    testament: "Old Testament",
    chapters: 4,
    summary: "A call to faithfulness and the promise of Elijah's return.",
  },
  // New Testament
  {
    id: "mat",
    name: "Matthew",
    testament: "New Testament",
    chapters: 28,
    summary:
      "The life, teachings, death, and resurrection of Jesus Christ, presented to a Jewish audience.",
    author: "Matthew",
  },
  {
    id: "mar",
    name: "Mark",
    testament: "New Testament",
    chapters: 16,
    summary:
      "The life, teachings, death, and resurrection of Jesus Christ, emphasizing his actions.",
    author: "Mark",
  },
  {
    id: "luk",
    name: "Luke",
    testament: "New Testament",
    chapters: 24,
    summary:
      "A detailed account of the life and ministry of Jesus, written for a Gentile audience.",
    author: "Luke",
  },
  {
    id: "joh",
    name: "John",
    testament: "New Testament",
    chapters: 21,
    summary: "A theological presentation of Jesus as the Son of God.",
    author: "John",
  },
  {
    id: "act",
    name: "Acts",
    testament: "New Testament",
    chapters: 28,
    summary:
      "The early history of the Christian church and the spread of the Gospel.",
    author: "Luke",
  },
  {
    id: "rom",
    name: "Romans",
    testament: "New Testament",
    chapters: 16,
    summary: "A systematic explanation of Christian doctrine.",
    author: "Paul",
  },
  {
    id: "1co",
    name: "1 Corinthians",
    testament: "New Testament",
    chapters: 16,
    summary: "Paul's instructions to the church in Corinth on various issues.",
    author: "Paul",
  },
  {
    id: "2co",
    name: "2 Corinthians",
    testament: "New Testament",
    chapters: 13,
    summary: "Paul's defense of his apostleship and call for reconciliation.",
    author: "Paul",
  },
  {
    id: "gal",
    name: "Galatians",
    testament: "New Testament",
    chapters: 6,
    summary: "Justification by faith and freedom in Christ.",
    author: "Paul",
  },
  {
    id: "eph",
    name: "Ephesians",
    testament: "New Testament",
    chapters: 6,
    summary: "The unity of believers in Christ and the nature of the church.",
    author: "Paul",
  },
  {
    id: "phi",
    name: "Philippians",
    testament: "New Testament",
    chapters: 4,
    summary: "Joy, humility, and Christ-likeness.",
    author: "Paul",
  },
  {
    id: "col",
    name: "Colossians",
    testament: "New Testament",
    chapters: 4,
    summary: "The supremacy of Christ and warnings against false teachings.",
    author: "Paul",
  },
  {
    id: "1th",
    name: "1 Thessalonians",
    testament: "New Testament",
    chapters: 5,
    summary: "Encouragement and instruction regarding Christ's return.",
    author: "Paul",
  },
  {
    id: "2th",
    name: "2 Thessalonians",
    testament: "New Testament",
    chapters: 3,
    summary: "Further clarification on Christ's return and godly living.",
    author: "Paul",
  },
  {
    id: "1ti",
    name: "1 Timothy",
    testament: "New Testament",
    chapters: 6,
    summary: "Instructions on church leadership and conduct.",
    author: "Paul",
  },
  {
    id: "2ti",
    name: "2 Timothy",
    testament: "New Testament",
    chapters: 4,
    summary: "Paul's final encouragement to Timothy to remain faithful.",
    author: "Paul",
  },
  {
    id: "tit",
    name: "Titus",
    testament: "New Testament",
    chapters: 3,
    summary: "Instructions on church order and sound doctrine.",
    author: "Paul",
  },
  {
    id: "phm",
    name: "Philemon",
    testament: "New Testament",
    chapters: 1,
    summary: "A plea for forgiveness and reconciliation.",
    author: "Paul",
  },
  {
    id: "heb",
    name: "Hebrews",
    testament: "New Testament",
    chapters: 13,
    summary: "The superiority of Christ and the new covenant.",
  },
  {
    id: "jam",
    name: "James",
    testament: "New Testament",
    chapters: 5,
    summary: "Practical Christian living and the importance of good works.",
    author: "James",
  },
  {
    id: "1pe",
    name: "1 Peter",
    testament: "New Testament",
    chapters: 5,
    summary: "Encouragement to suffering Christians.",
    author: "Peter",
  },
  {
    id: "2pe",
    name: "2 Peter",
    testament: "New Testament",
    chapters: 3,
    summary:
      "Warnings against false teachers and encouragement to grow in faith.",
    author: "Peter",
  },
  {
    id: "1jo",
    name: "1 John",
    testament: "New Testament",
    chapters: 5,
    summary:
      "Fellowship with God, love for one another, and assurance of salvation.",
    author: "John",
  },
  {
    id: "2jo",
    name: "2 John",
    testament: "New Testament",
    chapters: 1,
    summary: "Warning against false teachers and emphasis on truth and love.",
    author: "John",
  },
  {
    id: "3jo",
    name: "3 John",
    testament: "New Testament",
    chapters: 1,
    summary: "Commendation for hospitality and warning against opposition.",
    author: "John",
  },
  {
    id: "jud_nt", // Changed ID to be unique
    name: "Jude",
    testament: "New Testament",
    chapters: 1,
    summary: "A call to contend for the faith against false teachings.",
    author: "Jude",
  },
  {
    id: "rev",
    name: "Revelation",
    testament: "New Testament",
    chapters: 22,
    summary:
      "Prophetic visions concerning the end times and Christ's ultimate victory.",
    author: "John",
  },
];

const filterOptions: FilterData = {
  testaments: ["Old Testament", "New Testament"],
  bookNames: bibleBooksNIV.map((book) => book.name),
};

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

export async function loader() {
  try {
    // Call the RPC function to get distinct books
    const { data: rpcData, error } = await supabase.rpc("get_distinct_books");

    if (error) {
      console.error("Supabase RPC error:", error);
      return { books: bibleBooksNIV, filters: filterOptions };
    }

    if (!rpcData || rpcData.length === 0) {
      console.warn(
        "No distinct books data found from RPC, returning static data."
      );
      return { books: bibleBooksNIV, filters: filterOptions };
    }

    const booksData = rpcData.map((item: { book_name: string }) => ({
      book: item.book_name,
    }));

    console.log("Fetched distinct books data:", booksData);

    // The booksData is already an array of unique objects, so we can directly extract book names
    const uniqueBooks = booksData.map((item: { book: string }) => item.book);

    const dynamicBooks: BibleBook[] = uniqueBooks.map(
      (bookName: string, index: number) => {
        const staticBook = bibleBooksNIV.find(
          (book) =>
            book.name.toLowerCase() === bookName.toLowerCase() ||
            book.name.toLowerCase().includes(bookName.toLowerCase()) ||
            bookName.toLowerCase().includes(book.name.toLowerCase())
        );

        return {
          id: staticBook?.id || `book_${index}`,
          name: bookName,
          testament: staticBook?.testament || "Old Testament",
          chapters: staticBook?.chapters || 1,
          summary: staticBook?.summary || `Book of ${bookName}`,
          author: staticBook?.author,
          writtenDate: staticBook?.writtenDate,
        };
      }
    );
    const dynamicFilterOptions: FilterData = {
      testaments: ["Old Testament", "New Testament"],
      bookNames: dynamicBooks.map((book) => book.name),
    };

    return { books: dynamicBooks, filters: dynamicFilterOptions };
  } catch (error) {
    console.error("Error fetching books:", error);

    return { books: bibleBooksNIV, filters: filterOptions };
  }
}

export default function BibleBooksPage() {
  const { books, filters } = useLoaderData<typeof loader>();
  const [detailsViewBook, setDetailsViewBook] = useState<BibleBook | null>(
    null
  );
  const [viewMode, setViewMode] = useState<"grid" | "list">("list");
  const [sortOrder, setSortOrder] = useState<string>("default");

  const maxChapters = Math.max(...books.map((book) => book.chapters));

  const [activeFilters, setActiveFilters] = useState<{
    testament: "Old Testament" | "New Testament" | null;
    bookName: string | null;
    chapterRange: [number, number];
  }>({
    testament: null,
    bookName: null,
    chapterRange: [0, maxChapters],
  });

  const filteredBooks = books.filter((book) => {
    let pass = true;
    if (activeFilters.testament && book.testament !== activeFilters.testament)
      pass = false;
    if (activeFilters.bookName && book.name !== activeFilters.bookName)
      pass = false; // Filter by book name
    if (
      book.chapters < activeFilters.chapterRange[0] ||
      book.chapters > activeFilters.chapterRange[1]
    )
      pass = false;
    return pass;
  });

  // Apply sorting
  const sortedBooks = [...filteredBooks].sort((a, b) => {
    switch (sortOrder) {
      case "chapters_asc":
        return a.chapters - b.chapters;
      case "chapters_desc":
        return b.chapters - a.chapters;
      case "name_asc":
        return a.name.localeCompare(b.name);
      case "default":
      default:
        return (
          books.findIndex((book: BibleBook) => book.id === a.id) -
          books.findIndex((book: BibleBook) => book.id === b.id)
        );
    }
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
          maxChapters={maxChapters}
          activeFilters={activeFilters}
          onFilterChange={(newFilters) =>
            setActiveFilters((prev) => ({ ...prev, ...newFilters }))
          }
        />
        <main className="w-full md:w-3/4">
          {/* Sort & View Options Bar */}
          <div className="bg-white p-3 rounded-md shadow-sm flex justify-between items-center mb-6 border border-slate-200">
            <div className="flex gap-3">
              <Dropdown
                label="Sort By"
                options={[
                  { value: "default", label: "Canonical Order" },
                  { value: "chapters_asc", label: "Chapters: Low to High" },
                  { value: "chapters_desc", label: "Chapters: High to Low" },
                  { value: "name_asc", label: "Name: A-Z" },
                ]}
                onSelect={(value: string) => setSortOrder(value)}
                buttonClassName="bg-slate-100 hover:bg-slate-200 text-slate-700"
                menuClassName="bg-white border-slate-200"
                itemClassName="hover:bg-sky-50"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-600 mr-2">
                {sortedBooks.length} books found
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
          {sortedBooks.length > 0 ? (
            <div
              className={`grid gap-6 ${
                viewMode === "grid"
                  ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                  : "grid-cols-1"
              }`}
            >
              {sortedBooks.map((book) => (
                <BookCard
                  key={book.id}
                  book={book}
                  onViewDetails={() => setDetailsViewBook(book)}
                  viewMode={viewMode}
                />
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
