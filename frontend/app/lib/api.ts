const API_BASE_URL = "http://127.0.0.1:8000";
import { supabase } from "../lib/supabase";

export interface SongRequest {
  strBookName: string;
  intBookChapter: number;
  strVerseRange: string;
  strStyle: string;
  strTitle: string;
}

export interface SongResult {
  id?: number;
  title: string;
  lyrics?: string;
  audioUrl?: string;
  status?: string;
}

export interface SongStructureResult {
  id?: number;
  song_structure: string;
  book_name: string;
  chapter: number;
  verse_range: string;
  tone?: number;
  styles?: string[];
}

export interface SongResponse {
  success: boolean;
  message: string;
  result?: SongResult;
  error?: string;
}

export const generateSong = async (
  request: SongRequest
): Promise<SongResponse> => {
  try {
    console.log("API request payload:", request);

    const response = await fetch(`${API_BASE_URL}/song/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    console.log("Response status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Error response:", errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    console.log("API response data:", data);
    return data;
  } catch (error) {
    console.error("Error generating song:", error);
    return {
      success: false,
      message: "Failed to generate song",
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
};

export interface SongStructureRequest {
  strBookName: string;
  intBookChapter: number;
  strVerseRange: string;
}

export interface SongStructureResponse {
  success: boolean;
  message: string;
  result?: SongStructureResult;
  error?: string;
}

export const generateSongStructure = async (
  request: SongStructureRequest
): Promise<SongStructureResponse> => {
  try {
    console.log("Song structure API request payload:", request);

    const response = await fetch(`${API_BASE_URL}/generate-song-structure`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    console.log("Song structure response status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Song structure error response:", errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Song structure API response data:", data);
    return data;
  } catch (error) {
    console.error("Error generating song structure:", error);
    return {
      success: false,
      message: "Failed to generate song structure",
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
};

export interface SongStructure {
  id: number;
  book_name: string;
  chapter: number;
  verse_range: string;
  song_structure: string;
  tone: number;
  styles: string[];
}

export interface Style {
  id: number;
  name: string;
  description?: string;
}

export interface FetchSongStructuresResponse {
  success: boolean;
  message: string;
  result?: SongStructure[];
  error?: string;
}

export interface FetchStylesResponse {
  success: boolean;
  message: string;
  result?: Style[];
  error?: string;
}

export const fetchSongStructures = async (
  verseRange?: string
): Promise<FetchSongStructuresResponse> => {
  try {
    console.log("Fetching song structures from Supabase...");

    let query = supabase
      .from("song_structure_tbl")
      .select("*")
      .not("song_structure", "is", null)
      .not("song_structure", "eq", "")
      .order("id", { ascending: false });

    if (verseRange) {
      query = query.eq("verse_range", verseRange);
    }

    const { data, error } = await query;

    if (error) {
      console.error("Supabase error fetching song structures:", error);
      return {
        success: false,
        message: "Failed to fetch song structures from database",
        error: error.message,
      };
    }

    console.log("Supabase song structures data:", data);

    return {
      success: true,
      message: "Song structures fetched successfully",
      result: data || [],
    };
  } catch (error) {
    console.error("Error fetching song structures:", error);
    return {
      success: false,
      message: "Failed to fetch song structures",
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
};

export const fetchStyles = async (
  verseRange?: string
): Promise<FetchStylesResponse> => {
  try {
    console.log("Fetching styles from Supabase song_structure_tbl...");

    let query = supabase
      .from("song_structure_tbl")
      .select("styles")
      .not("styles", "is", null);

    if (verseRange) {
      query = query.eq("verse_range", verseRange);
    }

    const { data, error } = await query;

    if (error) {
      console.error("Supabase error fetching styles:", error);
      return {
        success: false,
        message: "Failed to fetch styles from database",
        error: error.message,
      };
    }

    // Extract unique styles from the results
    const uniqueStyles = new Set<string>();
    data?.forEach((row) => {
      if (row.styles && Array.isArray(row.styles)) {
        row.styles.forEach((style: string) => uniqueStyles.add(style));
      }
    });

    return {
      success: true,
      message: "Styles fetched successfully",
      result: Array.from(uniqueStyles).map((style, index) => ({
        id: index + 1, // Generate a unique ID for each style
        name: style,
      })),
    };
  } catch (error) {
    console.error("Error fetching styles:", error);
    return {
      success: false,
      message: "Failed to fetch styles",
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
};

export const calldownloadSongAPI = async (
  request: SongRequest
): Promise<SongResponse> => {
  try {
    console.log("API request payload for download-song:", request);

    const response = await fetch(`${API_BASE_URL}/download-song`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    console.log("Download-song response status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Error response from download-song:", errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    console.log("Download-song API response data:", data);
    return data;
  } catch (error) {
    console.error("Error downloading song:", error);
    return {
      success: false,
      message: "Failed to download song",
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
};

export const fetchSongFilesFromPublic = async (
  bookName: string,
  chapter: number,
  verseRange: string
): Promise<{ success: boolean; result?: string[]; error?: string }> => {
  try {
    const queryParams = new URLSearchParams({
      bookName,
      chapter: chapter.toString(),
      range: verseRange,
    });

    const response = await fetch(`/api/list-songs?${queryParams.toString()}`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: "Network response was not ok" }));
      return { success: false, error: errorData.error || `HTTP error! status: ${response.statusText} (${response.status})` };
    }
    const data = await response.json();
    return { success: true, result: data.files };
  } catch (error) {
    console.error("Failed to fetch song files from public:", error);
    return { success: false, error: error instanceof Error ? error.message : "An unknown error occurred" };
  }
};
