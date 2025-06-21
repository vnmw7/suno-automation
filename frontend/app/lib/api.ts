const API_BASE_URL = "http://127.0.0.1:8000";
import { supabase } from "./supabase";

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

    const response = await fetch(`${API_BASE_URL}/generate-song`, {
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

export const fetchSongStructures =
  async (): Promise<FetchSongStructuresResponse> => {
    try {
      console.log("Fetching song structures from Supabase...");

      const { data, error } = await supabase
        .from("song_structure_tbl")
        .select("*")
        .not("song_structure", "is", null)
        .not("song_structure", "eq", "")
        .order("id", { ascending: false });

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

export const fetchStyles = async (): Promise<FetchStylesResponse> => {
  try {
    console.log("Fetching styles from Supabase song_structure_tbl...");

    // Fetch all unique styles from the song_structure_tbl
    const { data, error } = await supabase
      .from("song_structure_tbl")
      .select("*") // Use select('*') to avoid the malformed array literal error
      .not("styles", "is", null);

    if (error) {
      console.error("Supabase error fetching styles:", error);
      return {
        success: false,
        message: "Failed to fetch styles from database",
        error: error.message,
      };
    } // Extract unique styles from the results
    const uniqueStyles = new Set<string>();
    data?.forEach((row) => {
      if (row.styles && Array.isArray(row.styles)) {
        row.styles.forEach((style: string) => {
          if (style && typeof style === "string") {
            uniqueStyles.add(style.trim());
          }
        });
      }
    });

    // Convert to the expected format
    const styleResults: Style[] = Array.from(uniqueStyles).map(
      (styleName, index) => ({
        id: index + 1,
        name: styleName,
      })
    );

    console.log("Extracted unique styles:", styleResults);

    return {
      success: true,
      message: "Styles fetched successfully",
      result: styleResults,
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
