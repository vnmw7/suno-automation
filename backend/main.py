"""
main.py
This file sets up the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SongRequest(BaseModel):
    strBookName: str
    intBookChapter: int
    strVerseRange: str
    strStyle: str
    strTitle: str


class SongStructureRequest(BaseModel):
    strBookName: str
    intBookChapter: int
    strVerseRange: str


@app.get("/")
def read_root():
    return {"message": "server working"}


@app.get("/login")
async def login_endpoint():
    from utils.suno_functions import login_suno

    is_successful = await login_suno()
    return {"success": is_successful}


@app.post("/generate-verse-ranges")
def generate_verse_ranges_endpoint(book_name: str, book_chapter: int):
    from utils.ai_functions import generate_verse_ranges

    try:
        verse_ranges = generate_verse_ranges(book_name, book_chapter)
        return {
            "success": True,
            "message": "Verse ranges generated successfully.",
            "verse_ranges": verse_ranges,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/get-verse-ranges")
def get_verse_ranges_endpoint(book_name: str, book_chapter: int):
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


@app.post("/generate-song")
async def generate_song_endpoint(SongRequest: SongRequest):
    from utils.suno_functions import generate_song

    try:
        result = await generate_song(
            strBookName=SongRequest.strBookName,
            intBookChapter=SongRequest.intBookChapter,
            strVerseRange=SongRequest.strVerseRange,
            strStyle=SongRequest.strStyle,
            strTitle=SongRequest.strTitle,
        )
        return {
            "success": True,
            "message": "Song generated successfully.",
            "result": result,
        }
    except ValueError as ve:
        print(f"ValueError in generate_song_endpoint: {ve}")
        return {
            "error": str(ve),
            "message": "Missing or invalid song structure data.",
            "success": False,
        }
    except Exception as e:
        print(f"A critical error occurred in generate_song_endpoint: {e}")
        print(traceback.format_exc())
        return {
            "error": str(e),
            "message": "A critical error occurred during the song generation.",
            "success": False,
        }


@app.post("/download-song")
async def download_song_endpoint(request: SongRequest):

    try:
        from utils.suno_functions import download_song_with_page, AsyncCamoufox, config

        async with AsyncCamoufox(
            headless=False,
            persistent_context=True,
            user_data_dir="user-data-dir",
            os=("windows"),
            config=config,
            humanize=False,
            i_know_what_im_doing=True,
        ) as browser:
            page = await browser.new_page()

            SONG_INDEX = 1
            SONG_COUNT = 2

            download_results = []

            for i in range(SONG_INDEX, SONG_COUNT + 1):
                print(
                    f"Attempting to download song {i} of {SONG_COUNT} with title: {request.strTitle}"
                )
                success = await download_song_with_page(
                    page, strTitle=request.strTitle, intIndex=-i
                )
                download_results.append(
                    {
                        "index": i,
                        "title": request.strTitle,
                        "download_successful": success,
                    }
                )
                if not success:
                    print(f"Failed to download song {i} with title: {request.strTitle}")

            successful_downloads_count = sum(
                1 for res in download_results if res["download_successful"]
            )

            if successful_downloads_count == (SONG_COUNT - SONG_INDEX + 1):
                return {
                    "success": True,
                    "message": f"All {successful_downloads_count} songs downloaded successfully.",
                    "details": download_results,
                }
            elif successful_downloads_count > 0:
                return {
                    "success": False,  # Indicate partial success
                    "message": f"Downloaded {successful_downloads_count} out of {SONG_COUNT - SONG_INDEX + 1} songs.",
                    "details": download_results,
                }
            else:
                return {
                    "error": "Failed to download any songs.",
                    "message": "All song downloads failed.",
                    "details": download_results,
                }

    except Exception as e:
        print(f"A critical error occurred in generate_song_endpoint: {e}")
        print(traceback.format_exc())
        return {
            "error": str(e),
            "message": "A critical error occurred during the song operation.",
        }


@app.get("/debug/song-structures")
def debug_song_structures_endpoint():
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
