from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Add this import
from pydantic import BaseModel

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
async def login():
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
    from utils.suno_functions import generate_song, download_song

    try:
        # result = await generate_song(
        #     strLyrics=request.strLyrics,
        #     strStyle=request.strStyle,
        #     strTitle=request.strTitle,
        # )

        SONG_INDEX = 1
        SONG_COUNT = 2
        for i in range(SONG_INDEX, SONG_COUNT + 1):
            print(f"Downloading song {i} with title: {request.strTitle}")
            await download_song(strTitle=request.strTitle, intIndex=i)

        return {"success": "result", "message": "Song generation completed"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1")
