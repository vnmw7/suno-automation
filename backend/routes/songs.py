from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import mimetypes
import os

router = APIRouter(prefix="/api/songs", tags=["songs"])

# Define the absolute path to the base 'songs' directory.
# This creates a security "sandbox," preventing any file access outside this directory.
SONGS_DIR = Path(__file__).resolve().parent.parent / 'songs'

@router.get("/{file_path:path}")
async def stream_song(file_path: str):
    """
    Securely streams an audio file from within the SONGS_DIR.
    Prevents directory traversal attacks by ensuring the resolved file path is
    strictly confined within the SONGS_DIR boundary.
    """
    try:
        # 1. Create a secure, absolute path to the base directory.
        secure_base_dir = SONGS_DIR.resolve()

        # 2. Safely join the requested file_path to the base directory.
        # The client-provided path is treated as relative to SONGS_DIR.
        full_path = (secure_base_dir / file_path).resolve()

        # 3. CRITICAL SECURITY CHECK: Verify the resolved path is a child of the base directory.
        # This is the canonical method to prevent directory traversal attacks.
        if not str(full_path).startswith(str(secure_base_dir)):
            raise HTTPException(status_code=403, detail="Forbidden: Access to the requested path is denied.")

        # 4. Check if the path points to an actual file.
        if not full_path.is_file():
            raise HTTPException(status_code=404, detail=f"Song not found: {file_path}")

        # 5. Determine the MIME type for the Content-Type header.
        mime_type, _ = mimetypes.guess_type(full_path)
        if not mime_type:
            mime_type = 'audio/mpeg'  # Default for .mp3 files if guess fails.

        # 6. FIX THE BUG: Use the actual filename from the resolved path.
        # This sets the 'Content-Disposition' header for downloads.
        return FileResponse(
            path=str(full_path),
            media_type=mime_type,
            filename=full_path.name,  # CORRECTED: Resolves the NameError
            headers={
                "Accept-Ranges": "bytes",  # Essential for allowing clients to seek within the audio stream.
                "Cache-Control": "no-cache",
            }
        )

    except HTTPException:
        # Re-raise FastAPI's own exceptions.
        raise
    except Exception as e:
        # Log unexpected internal errors for debugging.
        print(f"An unexpected error occurred while streaming song {file_path}: {e}")
        # Return a generic 500 error to the client.
        raise HTTPException(status_code=500, detail="Internal server error while streaming the song.")