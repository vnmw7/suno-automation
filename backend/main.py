"""
System: Suno Automation Backend
Module: main
Purpose: Main FastAPI application setup, including routing, middleware, and API endpoints for song generation and related functionalities.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback
from api.song.routes import router as song_router
from api.ai_review.routes import router as ai_review_router

app = FastAPI()

# Include routers
app.include_router(song_router)
app.include_router(ai_review_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SongRequest(BaseModel):
    """
    Represents a request to generate or download a song.

    Attributes:
        strBookName (str): The name of the book.
        intBookChapter (int): The chapter number within the book.
        strVerseRange (str): The range of verses to consider.
        strStyle (str): The desired style for the song.
        strTitle (str): The title of the song.
    """

    strBookName: str
    intBookChapter: int
    strVerseRange: str
    strStyle: str
    strTitle: str


class SongStructureRequest(BaseModel):
    """
    Represents a request to generate a song structure.

    Attributes:
        strBookName (str): The name of the book.
        intBookChapter (int): The chapter number within the book.
        strVerseRange (str): The range of verses to consider.
    """

    strBookName: str
    intBookChapter: int
    strVerseRange: str


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


@app.post("/generate-verse-ranges")
def generate_verse_ranges_endpoint(book_name: str, book_chapter: int):
    """
    Generates verse ranges for a given book and chapter.

    This endpoint takes a book name and chapter number, then uses an AI function
    to generate corresponding verse ranges. It includes error handling for
    unexpected issues during the generation process.

    Args:
        book_name (str): The name of the book (e.g., "Genesis").
        book_chapter (int): The chapter number (e.g., 1).

    Returns:
        dict: A JSON response containing the success status, a message, and the
              generated verse ranges, or an error message if an exception occurs.
    """
    from utils.ai_functions import generate_verse_ranges

    try:
        print(
            f"[generate_verse_ranges_endpoint({book_name}, {book_chapter})] Generating verse ranges for {book_name} chapter {book_chapter}"
        )
        verse_ranges = generate_verse_ranges(book_name, book_chapter)
        return {
            "success": True,
            "message": "Verse ranges generated successfully.",
            "verse_ranges": verse_ranges,
        }
    except Exception as e:
        print(f"A critical error occurred in generate_verse_ranges_endpoint: {e}")
        print(traceback.format_exc())
        return {
            "error": str(e),
            "message": "A critical error occurred during the verse ranges generation.",
        }


@app.get("/get-verse-ranges")
def get_verse_ranges_endpoint(book_name: str, book_chapter: int):
    """
    Retrieves pre-generated verse ranges for a given book and chapter.

    This endpoint fetches verse ranges from a data source using the provided
    book name and chapter number. It handles potential errors during retrieval.

    Args:
        book_name (str): The name of the book (e.g., "Genesis").
        book_chapter (int): The chapter number (e.g., 1).

    Returns:
        dict: A JSON response containing the success status, a message, and the
              retrieved verse ranges, or an error message if an exception occurs.
    """
    from utils.ai_functions import get_verse_ranges

    try:
        verse_ranges = get_verse_ranges(book_name, book_chapter)
        return {
            "success": True,
            "message": "Verse ranges retrieved successfully.",
            "verse_ranges": verse_ranges,
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/generate-song-structure")
async def generate_song_structure_endpoint(request: SongStructureRequest):
    """
    Generates a song structure based on book, chapter, and verse range.

    This endpoint takes a `SongStructureRequest` object and uses an AI function
    to generate a song structure. It logs the process and handles potential errors.

    Args:
        request (SongStructureRequest): The request object containing book details.

    Returns:
        dict: A JSON response with the success status, a message, and the generated
              song structure, or an error message if an exception occurs.
    """
    print(
        f"[generate_song_structure_endpoint()] Generating song structure for {request.strBookName} chapter {request.intBookChapter}"
    )
    from utils.ai_functions import generate_song_structure

    try:
        result = generate_song_structure(
            strBookName=request.strBookName,
            intBookChapter=request.intBookChapter,
            strVerseRange=request.strVerseRange,
        )
        return {
            "success": True,
            "message": "Song structure generated successfully.",
            "result": result,
        }
    except Exception as e:
        print(f"A critical error occurred in generate_song_structure_endpoint: {e}")
        print(traceback.format_exc())
        return {
            "error": str(e),
            "message": "A critical error occurred during the song structure generation.",
        }


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
