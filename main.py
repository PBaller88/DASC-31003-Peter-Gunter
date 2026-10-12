import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from generator import generate_puzzle_round

app = FastAPI(title="GeoConnections API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GAME_SESSIONS = {}

class GuessRequest(BaseModel):
    game_id: str
    selected_items: List[str]

@app.get("/")
def read_index():
    return FileResponse("index.html")

@app.get("/api/puzzle/new")
def get_new_round():
    try:
        puzzle = generate_puzzle_round()
        game_id = str(uuid.uuid4())
        GAME_SESSIONS[game_id] = puzzle["solution"]
        return {"game_id": game_id, "tiles": puzzle["tiles"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/puzzle/validate")
def validate_guess(payload: GuessRequest):
    game_id = payload.game_id
    guess = set(payload.selected_items)

    if len(guess) != 4:
        raise HTTPException(status_code=400, detail="Select exactly 4 items.")

    if game_id not in GAME_SESSIONS:
        raise HTTPException(status_code=404, detail="Session expired.")

    for group in GAME_SESSIONS[game_id]:
        if guess == set(group["items"]):
            return {
                "correct": True,
                "category": group["category"],
                "difficulty": group["difficulty"],
                "items": group["items"]
            }

    return {"correct": False, "message": "Not a match! Try again."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
