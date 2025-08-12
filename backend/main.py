"""
System: Suno Automation Backend
Module: main
Purpose: Main FastAPI application setup, including routing, middleware, and API endpoints for song generation and related functionalities.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.song.routes import router as song_router
from api.ai_review.routes import router as ai_review_router
from api.ai_generation.routes import router as ai_generation_router

app = FastAPI()

# Include routers
app.include_router(song_router)
app.include_router(ai_review_router)
app.include_router(ai_generation_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """
    Root endpoint to check if the server is running.

    Returns:
        dict: A message indicating the server is working.
    """
    return {"message": "server working"}


@app.get("/login")
async def login_endpoint():
    """
    Initiates the Suno login process.

    This endpoint calls the `login_suno` function to authenticate with Suno.

    Returns:
        dict: A dictionary indicating the success status of the login attempt.
    """
    from utils.suno_functions import login_suno

    is_successful = await login_suno()
    return {"success": is_successful}


@app.get("/login/microsoft")
async def login_with_microsoft_endpoint():
    """
    Handles login using Microsoft credentials.

    This endpoint first calls `login_google` and then `suno_login_microsoft`
    to authenticate via Microsoft.

    Returns:
        dict: A dictionary indicating the success status of the Microsoft login.
    """
    from lib.login import login_google, suno_login_microsoft

    await login_google()
    is_successful = await suno_login_microsoft()
    return {"success": is_successful}


@app.get("/debug/song-structures")
def debug_song_structures_endpoint():
    """
    Debug endpoint to retrieve and display song structures from the database.

    This endpoint queries the 'song_structure_tbl' table in the Supabase database
    and returns the found records. It includes error handling for database
    retrieval issues.

    Returns:
        dict: A JSON response with the success status, a message indicating the
              number of song structures found, and the data itself, or an error
              message if retrieval fails.
    """
    """Debug endpoint to see what song structures are available in the database"""
    try:
        from lib.supabase import supabase

        result = supabase.table("song_structure_tbl").select("*").execute()
        return {
            "success": True,
            "message": f"Found {len(result.data)} song structures",
            "data": result.data,
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve song structures"}


# TOFIX: Missing /download-song endpoint that frontend's calldownloadSongAPI is calling
# Either implement this endpoint or update the frontend to use the correct endpoint

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
