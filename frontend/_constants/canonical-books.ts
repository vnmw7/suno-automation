import bookAbbreviations from "./book-abrv.json";

// The 66 canonical books of the Christian Bible
export const CANONICAL_BOOKS = [
  // Old Testament (39 books)
  "Genesis",
  "Exodus",
  "Leviticus",
  "Numbers",
  "Deuteronomy",
  "Joshua",
  "Judges",
  "Ruth",
  "1 Samuel",
  "2 Samuel",
  "1 Kings",
  "2 Kings",
  "1 Chronicles",
  "2 Chronicles",
  "Ezra",
  "Nehemiah",
  "Esther",
  "Job",
  "Psalms",
  "Proverbs",
  "Ecclesiastes",
  "Song of Solomon",
  "Isaiah",
  "Jeremiah",
  "Lamentations",
  "Ezekiel",
  "Daniel",
  "Hosea",
  "Joel",
  "Amos",
  "Obadiah",
  "Jonah",
  "Micah",
  "Nahum",
  "Habakkuk",
  "Zephaniah",
  "Haggai",
  "Zechariah",
  "Malachi",

  // New Testament (27 books)
  "Matthew",
  "Mark",
  "Luke",
  "John",
  "Acts",
  "Romans",
  "1 Corinthians",
  "2 Corinthians",
  "Galatians",
  "Ephesians",
  "Philippians",
  "Colossians",
  "1 Thessalonians",
  "2 Thessalonians",
  "1 Timothy",
  "2 Timothy",
  "Titus",
  "Philemon",
  "Hebrews",
  "James",
  "1 Peter",
  "2 Peter",
  "1 John",
  "2 John",
  "3 John",
  "Jude",
  "Revelation",
];

const ABBREVIATION_TO_FULL_NAME: Record<string, string> = {};
for (const [fullName, abbreviation] of Object.entries(bookAbbreviations)) {
  ABBREVIATION_TO_FULL_NAME[abbreviation] = fullName;
}

export function isCanonicalBook(bookName: string): boolean {
  // Check if it's already a full name
  if (CANONICAL_BOOKS.includes(bookName)) {
    return true;
  }

  const fullName = ABBREVIATION_TO_FULL_NAME[bookName];
  if (fullName && CANONICAL_BOOKS.includes(fullName)) {
    return true;
  }

  return false;
}

export function getFullBookName(bookName: string): string {
  if (CANONICAL_BOOKS.includes(bookName)) {
    return bookName;
  }

  const fullName = ABBREVIATION_TO_FULL_NAME[bookName];
  if (fullName && CANONICAL_BOOKS.includes(fullName)) {
    return fullName;
  }

  return bookName;
}
