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
    strLyrics: str
    strStyle: str
    strTitle: str


@app.get("/")
def read_root():
    return {"message": "server working"}


@app.get("/login")
async def login_endpoint():
    from utils.suno_functions import login_suno

    is_successful = await login_suno()
    return {"success": is_successful}


@app.post("/generate-verse-ranges")
def generate_verse_ranges(book_name: str, book_chapter: int):
    from utils.ai_functions import generate_verse_ranges

    try:
        generate_verse_ranges(book_name, book_chapter)
        return {"message": "Verse ranges generated successfully."}
    except Exception as e:
        return {"error": str(e)}


@app.post("/generate-song")
async def generate_song_endpoint(request: SongRequest):
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
                    page, strTitle=request.strTitle, intIndex=i + 2
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
