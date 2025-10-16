"""
System: Suno Automation Backend
Module: main
Purpose: Main FastAPI application setup, including routing, middleware, and API endpoints for song generation and related functionalities.
"""

import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.song.routes import router as song_router
from api.ai_review.routes import router as ai_review_router
from api.ai_generation.routes import router as ai_generation_router
from api.orchestrator.routes import router as orchestrator_router
from routes.songs import router as songs_router

app = FastAPI()

# Define a specific list of allowed origins.
# This should be managed via environment variables for different deployments.
allowed_origins = [
    "http://localhost:3000",  # Remix production server
    "http://localhost:5173",  # Remix dev server
    # Add production URLs here when deploying
    # e.g., "https://your-production-app.com"
]

# Configure CORS BEFORE adding routers
# Try without credentials to debug CORS issue
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily for debugging
    allow_credentials=False,  # Disable credentials temporarily
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose headers to the client
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Include routers AFTER CORS middleware
app.include_router(song_router)
app.include_router(ai_review_router)
app.include_router(ai_generation_router)
app.include_router(orchestrator_router)
app.include_router(songs_router)

REQUIRED_ENVIRONMENT_KEYS: List[str] = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "USER",
    "PASSWORD",
    "HOST",
    "PORT",
    "DBNAME",
]


@app.get("/health")
def read_health():
    """
    Report application readiness with lightweight configuration checks.

    Returns:
        JSONResponse: Health status with missing environment keys (if any).
    """
    missing_env = [key for key in REQUIRED_ENVIRONMENT_KEYS if not os.getenv(key)]
    is_healthy = not missing_env

    return JSONResponse(
        status_code=200 if is_healthy else 503,
        content={
            "status": "healthy" if is_healthy else "degraded",
            "missingEnv": missing_env,
        },
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


@app.options("/api/v1/auth/manual-login")
async def manual_login_options():
    """Handle OPTIONS preflight request for manual login endpoint"""
    return {"status": "ok"}

@app.post("/api/v1/auth/manual-login")
async def manual_login_endpoint():
    """
    System: Suno Automation
    Module: Manual Login Endpoint
    Purpose: Triggers manual login flow - opens browser for user to login

    This endpoint opens the Suno website and allows users to manually
    authenticate with any provider of their choice.

    Returns:
        dict: A dictionary indicating the success status of the manual login.
    """
    from lib.login import manual_login_suno

    is_successful = await manual_login_suno()
    return {"success": is_successful, "method": "manual"}


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
