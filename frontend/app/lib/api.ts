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

// New interfaces for download and review endpoints
export interface SongDownloadRequest {
  strTitle: string;
  intIndex: number;
  download_path?: string;
}

export interface SongDownloadResponse {
  success: boolean;
  file_path?: string;
  error?: string;
  song_title: string;
  song_index: number;
}

export interface SongReviewRequest {
  audio_file_path: string;
  song_structure_id: number;
}

export interface SongReviewResponse {
  success: boolean;
  verdict: string;  // "continue", "re-roll", or "error"
  first_response?: string;
  second_response?: string;
  error?: string;
  audio_file?: string;
}

export interface OrchestratorRequest {
  strBookName: string;
  intBookChapter: number;
  strVerseRange: string;
  strStyle: string;
  strTitle: string;
  song_structure_id?: number;
}

export interface OrchestratorResponse {
  success: boolean;
  message: string;
  total_attempts: number;
  final_songs_count: number;
  good_songs?: number;
  re_rolled_songs?: number;
  error?: string;
  workflow_details?: any;
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
  structureId?: string;  // Optional, for regeneration
  // TODO: Add documentation comment explaining when/how to use structureId
  // The structureId field is used when regenerating an existing song structure
  // Pass the ID of the structure you want to regenerate to create a new version
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

    const response = await fetch(`${API_BASE_URL}/ai-generation/song-structure`, {
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

// TODO: Create functions to use the new /ai-generation/verse-ranges endpoints
// Currently, verse range generation might still be using the old endpoints
// Need to add:
// - generateVerseRanges() - POST /ai-generation/verse-ranges
// - getVerseRanges() - GET /ai-generation/verse-ranges

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
  bookName?: string,
  chapter?: number,
  verseRange?: string
): Promise<FetchSongStructuresResponse> => {
  try {
    console.log(`Fetching song structures of ${bookName} ${chapter}:${verseRange} from Supabase...`);

    let query = supabase
      .from("song_structure_tbl")
      .select("*")
      .not("song_structure", "is", null)
      .not("song_structure", "eq", "")
      .order("id", { ascending: false });

    if (bookName) {
      query = query.eq("book_name", bookName);
    }
    if (chapter) {
      query = query.eq("chapter", chapter);
    }
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
  bookName?: string,
  chapter?: number,
  verseRange?: string
): Promise<FetchStylesResponse> => {
  try {
    console.log("Fetching styles from Supabase song_structure_tbl...");

    let query = supabase
      .from("song_structure_tbl")
      .select("styles")
      .not("styles", "is", null);

    if (bookName) {
      query = query.eq("book_name", bookName);
    }
    if (chapter) {
      query = query.eq("chapter", chapter);
    }
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

// TOFIX: This function calls /download-song endpoint which doesn't exist in the visible backend files
// Either the endpoint needs to be implemented in the backend or this should use a different endpoint
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

// New API functions for download and review endpoints
export const downloadSongAPI = async (
  request: SongDownloadRequest
): Promise<SongDownloadResponse> => {
  try {
    console.log("API request payload for /song/download:", request);

    const response = await fetch(`${API_BASE_URL}/song/download/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    console.log("Download-song response status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Error response from /song/download:", errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    console.log("Download-song API response data:", data);
    return data;
  } catch (error) {
    console.error("Error downloading song:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
      song_title: request.strTitle,
      song_index: request.intIndex,
    };
  }
};

export const reviewSongAPI = async (
  request: SongReviewRequest
): Promise<SongReviewResponse> => {
  try {
    console.log("API request payload for /ai_review/review:", request);

    const response = await fetch(`${API_BASE_URL}/ai_review/review/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    console.log("Review-song response status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Error response from /ai_review/review:", errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    console.log("Review-song API response data:", data);
    return data;
  } catch (error) {
    console.error("Error reviewing song:", error);
    return {
      success: false,
      verdict: "error",
      error: error instanceof Error ? error.message : "Unknown error",
      audio_file: request.audio_file_path,
    };
  }
};

export const orchestratorWorkflow = async (
  request: OrchestratorRequest
): Promise<OrchestratorResponse> => {
  try {
    console.log("🎼 [API] Orchestrator request payload:", request);

    const response = await fetch(`${API_BASE_URL}/orchestrator/workflow`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    console.log("🎼 [API] Orchestrator response status:", response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("🎼 [API] Orchestrator error response:", errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log("🎼 [API] Orchestrator response data:", data);
    return data;
  } catch (error) {
    console.error("🎼 [API] Orchestrator error:", error);
    return {
      success: false,
      message: "Failed to execute orchestrator workflow",
      error: error instanceof Error ? error.message : "Unknown error",
      total_attempts: 0,
      final_songs_count: 0,
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

// TODO: Consider implementing type safety enhancements
// Create a shared types package that both frontend and backend can use
// This would ensure perfect type alignment between TypeScript and Python models
