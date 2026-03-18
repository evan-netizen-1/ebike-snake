import modal
import json
from datetime import datetime

image = modal.Image.debian_slim().pip_install("fastapi")
app = modal.App("ebike-snake-leaderboard", image=image)

# Modal Dict persists key-value data between invocations
scores_dict = modal.Dict.from_name("ebike-snake-scores", create_if_missing=True)

MODES = ["chill", "classic", "turbo", "impossible", "walls"]
MAX_SCORES = 10


@app.function()
@modal.fastapi_endpoint(method="GET")
def get_scores(mode: str = ""):
    """Get leaderboard scores. If mode specified, return that mode only."""
    all_scores = {}
    for m in MODES:
        try:
            all_scores[m] = scores_dict[m]
        except KeyError:
            all_scores[m] = []

    if mode and mode in MODES:
        return {"scores": all_scores[mode], "mode": mode}
    return all_scores


@app.function()
@modal.fastapi_endpoint(method="POST")
def add_score(data: dict):
    """Add a score to the leaderboard."""
    mode = data.get("mode", "")
    name = data.get("name", "")
    score = data.get("score", 0)

    if mode not in MODES:
        return {"error": "Invalid mode", "valid_modes": MODES}
    if not name or not isinstance(name, str):
        return {"error": "Name is required"}
    if not isinstance(score, (int, float)) or score <= 0:
        return {"error": "Score must be a positive number"}

    # Sanitize name
    name = name.strip()[:12].upper()

    # Get current scores for this mode
    try:
        current = scores_dict[mode]
    except KeyError:
        current = []

    # Add new score
    current.append({
        "name": name,
        "score": int(score),
        "date": datetime.utcnow().isoformat() + "Z",
    })

    # Sort and keep top N
    current.sort(key=lambda x: x["score"], reverse=True)
    current = current[:MAX_SCORES]

    # Save back
    scores_dict[mode] = current

    return {"success": True, "scores": current, "mode": mode}
