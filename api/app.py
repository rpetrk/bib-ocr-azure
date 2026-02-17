from dotenv import load_dotenv
load_dotenv()

import os
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from requests_oauthlib import OAuth1

SMUGMUG_BASE = "https://api.smugmug.com/api/v2"

def get_oauth() -> OAuth1:
    api_key = os.environ.get("SMUGMUG_API_KEY")
    api_secret = os.environ.get("SMUGMUG_API_SECRET")
    access_token = os.environ.get("SMUGMUG_ACCESS_TOKEN")
    access_token_secret = os.environ.get("SMUGMUG_ACCESS_TOKEN_SECRET")

    missing = [k for k, v in {
        "SMUGMUG_API_KEY": api_key,
        "SMUGMUG_API_SECRET": api_secret,
        "SMUGMUG_ACCESS_TOKEN": access_token,
        "SMUGMUG_ACCESS_TOKEN_SECRET": access_token_secret,
    }.items() if not v]

    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    return OAuth1(api_key, api_secret, access_token, access_token_secret)

app = FastAPI(title="RaceBibIndexer API")

# Allow your local webpage to call the API during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000", "http://localhost:5500", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/albums/{username}")
def list_albums(username: str, count: int = 50) -> Dict[str, Any]:
    """
    Returns a simplified list of albums for the given SmugMug username.
    """
    auth = get_oauth()
    headers = {"Accept": "application/json"}

    url = f"{SMUGMUG_BASE}/user/{username}!albums?start=1&count={count}"

    resp = requests.get(url, auth=auth, headers=headers, timeout=30)

    if resp.status_code != 200:
        # SmugMug often returns JSON error bodies; pass them through for debugging
        try:
            detail = resp.json()
        except Exception:
            detail = {"status_code": resp.status_code, "body": resp.text[:1000]}
        raise HTTPException(status_code=resp.status_code, detail=detail)

    data = resp.json()
    albums = data.get("Response", {}).get("Album", [])

    simplified: List[Dict[str, Any]] = []
    for a in albums:
        simplified.append({
            "title": a.get("Title"),
            "albumKey": a.get("AlbumKey"),
            "uri": a.get("Uri"),
            "dateCreated": a.get("DateCreated"),
            "lastUpdated": a.get("LastUpdated"),
            "imageCount": a.get("ImageCount"),
        })

    return {
        "username": username,
        "count": len(simplified),
        "albums": simplified,
    }
