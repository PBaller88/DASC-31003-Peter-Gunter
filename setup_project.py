import os
import subprocess
import sys

# Define file contents
FILES = {
    "requirements.txt": """fastapi==0.110.0
uvicorn==0.28.0
requests==2.31.0
""",

    ".gitignore": """venv/
__pycache__/
.env
.DS_Store
""",

    "Dockerfile": """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
""",

    "generator.py": """import random
import requests

REST_COUNTRIES_URL = "https://restcountries.com/v3.1/all?fields=name,region,subregion,borders,landlocked"

def fetch_country_data():
    response = requests.get(REST_COUNTRIES_URL)
    response.raise_for_status()
    return response.json()

def build_category_pools(countries):
    pools = {
        "Countries in South America": [],
        "Countries in Southeast Asia": [],
        "Countries in Western Europe": [],
        "Countries in the Caribbean": [],
        "Landlocked Countries": [],
        "Island / Non-Bordering Nations": [],
        "Countries Bordering 5+ Neighbors": [],
        "Countries with 'Land' in Name": [],
    }

    for country in countries:
        name = country.get("name", {}).get("common", "")
        subregion = country.get("subregion", "")
        borders = country.get("borders", [])
        landlocked = country.get("landlocked", False)

        if subregion == "South America": pools["Countries in South America"].append(name)
        if subregion == "South-Eastern Asia": pools["Countries in Southeast Asia"].append(name)
        if subregion == "Western Europe": pools["Countries in Western Europe"].append(name)
        if subregion == "Caribbean": pools["Countries in the Caribbean"].append(name)
        if landlocked: pools["Landlocked Countries"].append(name)
        if len(borders) == 0: pools["Island / Non-Bordering Nations"].append(name)
        if len(borders) >= 5: pools["Countries Bordering 5+ Neighbors"].append(name)
        if "land" in name.lower() and name != "Finland": pools["Countries with 'Land' in Name"].append(name)

    return {cat: items for cat, items in pools.items() if len(items) >= 4}

def generate_puzzle_round():
    raw_data = fetch_country_data()
    pools = build_category_pools(raw_data)

    if len(pools) < 4:
        raise ValueError("Not enough valid categories.")

    difficulties = ["yellow", "green", "blue", "purple"]
    selected_categories = random.sample(list(pools.keys()), 4)

    puzzle_groups = []
    used_countries = set()
    all_tiles = []

    for idx, cat_name in enumerate(selected_categories):
        available = [c for c in pools[cat_name] if c not in used_countries]
        if len(available) < 4:
            return generate_puzzle_round()

        chosen_4 = random.sample(available, 4)
        used_countries.update(chosen_4)

        puzzle_groups.append({
            "category": cat_name,
            "difficulty": difficulties[idx],
            "items": chosen_4
        })
        all_tiles.extend(chosen_4)

    random.shuffle(all_tiles)
    return {"tiles": all_tiles, "solution": puzzle_groups}
""",

    "main.py": """import uuid
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
""",

    "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GeoConnections</title>
    <style>
        body { font-family: sans-serif; background: #121212; color: #fff; text-align: center; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; max-width: 500px; margin: 0 auto; }
        .tile { background: #2a2a2a; border-radius: 8px; padding: 20px 10px; font-weight: bold; cursor: pointer; user-select: none; transition: 0.2s; display: flex; align-items: center; justify-content: center; min-height: 50px; font-size: 0.9rem; }
        .tile.selected { background: #5a5a5a; border: 2px solid #fff; }
        .controls { margin-top: 20px; }
        button { background: #bb86fc; color: #000; border: none; padding: 12px 24px; font-size: 1rem; border-radius: 20px; font-weight: bold; cursor: pointer; margin: 5px; }
        button.secondary { background: #333; color: #fff; }
        .solved-group { grid-column: span 4; border-radius: 8px; padding: 15px; margin-bottom: 5px; color: #000; font-weight: bold; }
        .yellow { background: #f6d155; } .green { background: #b5e7a0; }
        .blue { background: #87ceeb; } .purple { background: #d0bdf4; }
    </style>
</head>
<body>
    <h1>GeoConnections</h1>
    <p>Group 16 items into 4 categories of 4!</p>
    <div id="solved-container" style="max-width:500px; margin:0 auto;"></div>
    <div class="grid" id="grid"></div>
    <div class="controls">
        <button onclick="submitGuess()">Submit Guess</button>
        <button class="secondary" onclick="startNewRound()">Next Round 🔄</button>
    </div>
    <script>
        let currentGameId = null, selectedTiles = [];
        async function startNewRound() {
            document.getElementById('solved-container').innerHTML = '';
            document.getElementById('grid').innerHTML = '';
            selectedTiles = [];
            const res = await fetch('/api/puzzle/new');
            const data = await res.json();
            currentGameId = data.game_id;
            data.tiles.forEach(tileText => {
                const tile = document.createElement('div');
                tile.className = 'tile';
                tile.innerText = tileText;
                tile.onclick = () => {
                    if (tile.classList.contains('selected')) {
                        tile.classList.remove('selected');
                        selectedTiles = selectedTiles.filter(t => t !== tileText);
                    } else if (selectedTiles.length < 4) {
                        tile.classList.add('selected');
                        selectedTiles.push(tileText);
                    }
                };
                document.getElementById('grid').appendChild(tile);
            });
        }
        async function submitGuess() {
            if (selectedTiles.length !== 4) return alert("Select exactly 4 tiles!");
            const res = await fetch('/api/puzzle/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ game_id: currentGameId, selected_items: selectedTiles })
            });
            const data = await res.json();
            if (data.correct) {
                const banner = document.createElement('div');
                banner.className = `solved-group ${data.difficulty}`;
                banner.innerHTML = `<div>${data.category.toUpperCase()}</div><div style="font-weight:normal; font-size:0.85rem">${data.items.join(', ')}</div>`;
                document.getElementById('solved-container').appendChild(banner);
                Array.from(document.querySelectorAll('.tile')).forEach(t => {
                    if (selectedTiles.includes(t.innerText)) t.remove();
                });
                selectedTiles = [];
            } else { alert(data.message); }
        }
        startNewRound();
    </script>
</body>
</html>
"""
}

def setup():
    print("📁 Creating project files...")
    for filename, content in FILES.items():
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ Created {filename}")

    print("\n⚙️ Setting up virtual environment (venv)...")
    subprocess.run([sys.executable, "-m", "venv", "venv"])

    pip_cmd = os.path.join("venv", "Scripts", "pip") if os.name == "nt" else os.path.join("venv", "bin", "pip")
    print("📦 Installing dependencies (FastAPI, Uvicorn, Requests)...")
    subprocess.run([pip_cmd, "install", "-r", "requirements.txt"])

    print("\n🐙 Initializing Git local repository...")
    subprocess.run(["git", "init"])
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "Initial commit: GeoConnections App"])

    print("\n🎉 Setup complete!")
    print("\n--- NEXT STEPS ---")
    print("1. Run locally:")
    print("   On Windows:      .\\venv\\Scripts\\python main.py")
    print("   On Mac/Linux:    ./venv/bin/python main.py")
    print("   Then open: http://127.0.0.1:8080 in your browser.")
    print("\n2. Deploy to GCP Cloud Run (via VS Code Terminal):")
    print("   gcloud run deploy geoconnections --source . --region us-central1 --allow-unauthenticated")

if __name__ == "__main__":
    setup()