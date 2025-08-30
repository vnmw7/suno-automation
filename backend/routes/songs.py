from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
from pathlib import Path
import mimetypes
from typing import List, Dict, Any

router = APIRouter(prefix="/api/songs", tags=["songs"])

# Get the songs directory path
SONGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'songs')

@router.get("/{filename:path}")
async def stream_song(filename: str):
    """Stream audio file from songs directory or subdirectories"""
    try:
        # Remove leading slash if present
        if filename.startswith('/'):
            filename = filename[1:]
        
        # Check for absolute paths or directory traversal attempts
        if os.path.isabs(filename) or '..' in filename:
            raise HTTPException(status_code=403, detail="Invalid file path")
        
        # Try multiple locations
        possible_paths = [
            os.path.join(SONGS_DIR, filename),  # Direct path
            os.path.join(SONGS_DIR, 'final_review', os.path.basename(filename)),  # In final_review
            os.path.join(SONGS_DIR, 'pending_review', os.path.basename(filename)),  # In pending_review
        ]
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path) and os.path.isfile(path):
                file_path = path
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"Song not found: {filename}")
        
        # Verify the file is actually in the songs directory (security check)
        real_path = os.path.realpath(file_path)
        real_songs_dir = os.path.realpath(SONGS_DIR)
        if not real_path.startswith(real_songs_dir):
            raise HTTPException(status_code=403, detail="Invalid file path")
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'audio/mpeg'  # Default to MP3
        
        # Send file with appropriate headers for streaming
        return FileResponse(
            path=file_path,
            media_type=mime_type,
            filename=safe_filename,
            headers={
                "Accept-Ranges": "bytes",  # Enable seeking
                "Cache-Control": "no-cache",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error streaming song {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stream song")

@router.get("")
async def list_songs() -> Dict[str, List[Dict[str, Any]]]:
    """List all available songs"""
    try:
        if not os.path.exists(SONGS_DIR):
            os.makedirs(SONGS_DIR, exist_ok=True)
            return {"songs": []}
        
        songs = []
        for filename in os.listdir(SONGS_DIR):
            if filename.endswith(('.mp3', '.wav', '.m4a', '.ogg')):
                file_path = os.path.join(SONGS_DIR, filename)
                songs.append({
                    "filename": filename,
                    "size": os.path.getsize(file_path),
                    "url": f"/api/songs/{filename}"
                })
        
        return {"songs": songs}
        
    except Exception as e:
        print(f"Error listing songs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list songs")