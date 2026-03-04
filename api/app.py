from dotenv import load_dotenv
load_dotenv()

import os
from typing import Any, Dict, List

import logging
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from requests_oauthlib import OAuth1

log = logging.getLogger("smugmug")

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

def smugmug_get(path: str, *, params: Dict[str, Any] | None = None) -> requests.Response:
    auth = get_oauth()
    headers = {"Accept": "application/json"}

    url = f"{SMUGMUG_BASE}{path}"
    resp = requests.get(url, auth=auth, headers=headers, params=params, timeout=30)  # verify=True by default
    return resp

def raise_upstream(resp: requests.Response, url: str) -> None:
    content_type = resp.headers.get("content-type", "")
    try:
        body = resp.json() if "json" in content_type else resp.text
    except Exception:
        body = resp.text

    log.warning(
        "SmugMug non-200: status=%s url=%s server=%s via=%s retry_after=%s body=%s",
        resp.status_code,
        url,
        resp.headers.get("server"),
        resp.headers.get("via"),
        resp.headers.get("retry-after"),
        str(body)[:2000],
    )

    raise HTTPException(
        status_code=resp.status_code,
        detail={
            "upstream": "api.smugmug.com",
            "status_code": resp.status_code,
            "url": url,
            "retry_after": resp.headers.get("retry-after"),
            "server": resp.headers.get("server"),
            "via": resp.headers.get("via"),
            "body": body if isinstance(body, (dict, list)) else str(body)[:2000],
        },
    )

app = FastAPI(title="RaceBibIndexer API")

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

@app.get("/me")
def whoami() -> Dict[str, Any]:
    """
    Returns info about the authenticated SmugMug user for the OAuth token.
    """
    resp = smugmug_get("/authuser")
    if resp.status_code != 200:
        raise_upstream(resp, resp.url)

    data = resp.json()
    user = data.get("Response", {}).get("User", {})

    # Return both raw + convenient fields
    return {
        "raw": user,
        "nickname": user.get("NickName"),
        "name": user.get("Name"),
        "uri": user.get("Uri"),
        "webUri": user.get("WebUri"),
        "userKey": user.get("UserKey"),
    }

@app.get("/albums/{username}")
def list_albums(username: str, count: int = 50) -> Dict[str, Any]:
    auth = get_oauth()
    headers = {"Accept": "application/json"}
    url = f"{SMUGMUG_BASE}/user/{username}!albums?start=1&count={count}"

    # IMPORTANT: don't disable TLS verification in production
    resp = requests.get(url, auth=auth, headers=headers, timeout=30)

    if resp.status_code != 200:
        raise_upstream(resp, url)

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

    return {"username": username, "count": len(simplified), "albums": simplified}