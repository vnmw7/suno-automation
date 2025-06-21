const API_BASE_URL = 'http://127.0.0.1:8000';

export interface SongRequest {
  strBookName: string;
  intBookChapter: number;
  strVerseRange: string;
  strStyle: string;
  strTitle: string;
}

export interface SongResponse {
  success: boolean;
  message: string;
  result?: any;
  error?: string;
}

export const generateSong = async (request: SongRequest): Promise<SongResponse> => {
  try {
    console.log('API request payload:', request);
    
    const response = await fetch(`${API_BASE_URL}/generate-song`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    console.log('Response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Error response:', errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }    const data = await response.json();
    console.log('API response data:', data);
    return data;
  } catch (error) {
    console.error('Error generating song:', error);
    return {
      success: false,
      message: 'Failed to generate song',
      error: error instanceof Error ? error.message : 'Unknown error',
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
  result?: any;
  error?: string;
}

export const generateSongStructure = async (request: SongStructureRequest): Promise<SongStructureResponse> => {
  try {
    console.log('Song structure API request payload:', request);
    
    const response = await fetch(`${API_BASE_URL}/generate-song-structure`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    console.log('Song structure response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Song structure error response:', errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Song structure API response data:', data);
    return data;
  } catch (error) {
    console.error('Error generating song structure:', error);
    return {
      success: false,
      message: 'Failed to generate song structure',
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
};
