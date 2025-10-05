/*
System: Suno Automation
Module: API Song File
Purpose: Stream final review song audio for preview playback
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

const STR_DEFAULT_AUDIO_CONTENT_TYPE = "audio/mpeg";

export async function loader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const strRequestedFileName = url.searchParams.get("fileName");

  if (!strRequestedFileName) {
    return json(
      { success: false, error: "fileName query parameter is required." },
      { status: 400 }
    );
  }

  const strResolvedPath = path.resolve(
    SONGS_FINAL_REVIEW_DIRECTORY,
    strRequestedFileName
  );
  const strRelativeFromBase = path.relative(
    SONGS_FINAL_REVIEW_DIRECTORY,
    strResolvedPath
  );

  if (strRelativeFromBase.startsWith("..") || path.isAbsolute(strRelativeFromBase)) {
    return json(
      {
        success: false,
        error: "Invalid file request.",
      },
      { status: 400 }
    );
  }

  try {
    const arrFileBuffer = await fs.readFile(strResolvedPath);
    const strFileExtension = path.extname(strResolvedPath).toLowerCase();
    const strContentType =
      strFileExtension === ".wav" ? "audio/wav" : STR_DEFAULT_AUDIO_CONTENT_TYPE;

    return new Response(arrFileBuffer as unknown as BodyInit, {
      status: 200,
      headers: {
        "Content-Type": strContentType,
        "Content-Length": arrFileBuffer.length.toString(),
        "Content-Disposition": `inline; filename="${path.basename(strResolvedPath)}"`,
        "Cache-Control": "no-store",
      },
    });
  } catch (error: unknown) {
    if (isErrorWithCode(error) && error.code === "ENOENT") {
      return json(
        {
          success: false,
          error: `Requested song not found at ${strResolvedPath}`,
        },
        { status: 404 }
      );
    }

    console.error("[api.song-file] Failed to stream song file:", error);
    return json(
      { success: false, error: "Failed to stream requested song file." },
      { status: 500 }
    );
  }
}
