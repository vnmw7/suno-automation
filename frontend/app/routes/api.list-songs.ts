/*
System: Suno Automation
Module: API List Songs
Purpose: Provide a listing of final review songs available for manual review
*/

import { json, type LoaderFunctionArgs } from "@remix-run/node";
import fs from "node:fs/promises";
import path from "node:path";

function isErrorWithCode(err: unknown): err is { code: string } {
  return typeof err === "object" && err !== null && "code" in err;
}

const SONGS_FINAL_REVIEW_DIRECTORY = path.resolve(
  process.cwd(),
  "..",
  "backend",
  "songs",
  "final_review"
);

const STR_AUDIO_EXTENSION = ".mp3";

function fncNormalizeRelativePath(strInput: string): string {
  return strInput.replace(/\\/g, "/");
}

async function fncCollectMp3Files(
  strBaseDirectory: string,
  strRelativeDirectory = ""
): Promise<string[]> {
  const strTargetDirectory = path.join(strBaseDirectory, strRelativeDirectory);
  const arrEntries = await fs.readdir(strTargetDirectory, { withFileTypes: true });

  const arrCollected: string[] = [];

  for (const objEntry of arrEntries) {
    const strEntryRelativePath = strRelativeDirectory
      ? path.join(strRelativeDirectory, objEntry.name)
      : objEntry.name;

    if (objEntry.isDirectory()) {
      const arrNested = await fncCollectMp3Files(
        strBaseDirectory,
        strEntryRelativePath
      );
      arrCollected.push(...arrNested);
    } else if (
      objEntry.isFile() &&
      objEntry.name.toLowerCase().endsWith(STR_AUDIO_EXTENSION)
    ) {
      arrCollected.push(fncNormalizeRelativePath(strEntryRelativePath));
    }
  }

  return arrCollected;
}

export async function loader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const bookName = url.searchParams.get("bookName");
  const chapterParam = url.searchParams.get("chapter");
  const range = url.searchParams.get("range"); // e.g., "1-11"

  try {
    let arrMp3Files = await fncCollectMp3Files(SONGS_FINAL_REVIEW_DIRECTORY);

    arrMp3Files = arrMp3Files.sort((strA, strB) => strA.localeCompare(strB));

    // Optional but recommended: Filter files based on book, chapter, range
    if (bookName && chapterParam && range) {
      const normalizedBookName = bookName.replace(/ /g, "_"); // Example: "Exodus" -> "Exodus"
      // Your filenames are like "Exodus_1-1-11_index_-1.mp3"
      // The props are bookName="Exodus", chapter=1, range="1-11"
      // The expected prefix in the filename would be "Exodus_1-1-11"
      const expectedFilePrefix = `${normalizedBookName}_${chapterParam}-${range}`.toLowerCase();

      arrMp3Files = arrMp3Files.filter((strFilePath) =>
        path.basename(strFilePath).toLowerCase().startsWith(expectedFilePrefix)
      );
    }

    return json({ success: true, files: arrMp3Files });
  } catch (error: unknown) {
    console.error(
      `Error listing song files from ${SONGS_FINAL_REVIEW_DIRECTORY}:`,
      error
    );
    if (isErrorWithCode(error) && error.code === "ENOENT") {
      // Directory not found
      return json(
        {
          success: false,
          error: `Song directory not found on server at ${SONGS_FINAL_REVIEW_DIRECTORY}`,
        },
        { status: 404 }
      );
    }
    return json(
      { success: false, error: "Failed to list song files from server." },
      { status: 500 }
    );
  }
}
