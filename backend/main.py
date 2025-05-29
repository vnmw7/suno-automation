from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Add this import

from utils.suno_functions import login_suno

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "server working"}


@app.get("/login")
def login():
    is_successful = login_suno()
    return {is_successful}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1")
