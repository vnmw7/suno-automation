import { json, type LoaderFunctionArgs } from "@remix-run/node";
import fs from "node:fs/promises"; // Using Node.js file system module
import path from "node:path";

export async function loader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const bookName = url.searchParams.get("bookName");
  const chapterParam = url.searchParams.get("chapter");
  const range = url.searchParams.get("range"); // e.g., "1-11"

  // Construct the absolute path to your public/songs directory
  // process.cwd() typically gives the root of your Remix project
  const songsPublicDir = path.join(process.cwd(), "public", "songs");

  try {
    const dirents = await fs.readdir(songsPublicDir, { withFileTypes: true });
    let mp3Files = dirents
      .filter((dirent) => dirent.isFile() && dirent.name.endsWith(".mp3"))
      .map((dirent) => dirent.name);

    // Optional but recommended: Filter files based on book, chapter, range
    if (bookName && chapterParam && range) {
      const normalizedBookName = bookName.replace(/ /g, "_"); // Example: "Exodus" -> "Exodus"
      // Your filenames are like "Exodus_1-1-11_index_-1.mp3"
      // The props are bookName="Exodus", chapter=1, range="1-11"
      // The expected prefix in the filename would be "Exodus_1-1-11"
      const expectedFilePrefix = `${normalizedBookName}_${chapterParam}-${range}`.toLowerCase();

      mp3Files = mp3Files.filter((fileName) =>
        fileName.toLowerCase().startsWith(expectedFilePrefix)
      );
    }

    return json({ success: true, files: mp3Files });
  } catch (error: any) {
    console.error(`Error listing song files from ${songsPublicDir}:`, error);
    if (error.code === "ENOENT") {
      // Directory not found
      return json(
        { success: false, error: `Song directory not found on server at ${songsPublicDir}` },
        { status: 404 }
      );
    }
    return json(
      { success: false, error: "Failed to list song files from server." },
      { status: 500 }
    );
  }
}
