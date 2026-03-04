from dotenv import load_dotenv
from fastapi.params import Query
load_dotenv()

import os
from typing import Any, Dict, List

import logging
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from requests_oauthlib import OAuth1
from urllib.parse import urlparse

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

@app.get("/smugmug/user/apidemo")
def smugmug_user_apidemo() -> Dict[str, Any]:
    """
    Proxies the SmugMug API demo endpoint using the API key from env:

      GET https://api.smugmug.com/api/v2/user/apidemo?APIKey=<SMUGMUG_API_KEY>

    Notes:
    - This is the SmugMug "apidemo" user endpoint; it does not use OAuth.
    - Env var required: SMUGMUG_API_KEY
    """
    api_key = os.environ.get("SMUGMUG_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing env var: SMUGMUG_API_KEY")

    upstream_url = f"{SMUGMUG_BASE}/user/apidemo"
    resp = requests.get(
        upstream_url,
        headers={"Accept": "application/json"},
        params={"APIKey": api_key},
        timeout=30,
        allow_redirects=False,
    )

    if resp.status_code != 200:
        raise_upstream(resp, resp.url)

    return resp.json()

@app.get("/smugmug/root")
def smugmug_root() -> Dict[str, Any]:
    """
    Returns SmugMug API v2 root response (authenticated).
    Useful to discover the correct 'who am I' / auth-user link for this token.
    """
    auth = get_oauth()
    headers = {"Accept": "application/json"}

    resp = requests.get(f"{SMUGMUG_BASE}/", auth=auth, headers=headers, timeout=30)

    if resp.status_code != 200:
        content_type = resp.headers.get("content-type", "")
        try:
            body = resp.json() if "json" in content_type else resp.text
        except Exception:
            body = resp.text
        raise HTTPException(
            status_code=resp.status_code,
            detail={
                "upstream": "api.smugmug.com",
                "status_code": resp.status_code,
                "url": resp.url,
                "body": body,
                "server": resp.headers.get("server"),
                "via": resp.headers.get("via"),
            },
        )

    return resp.json()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/me")
def me() -> Dict[str, Any]:
    """
    Returns the SmugMug user record for the configured account.

    Requires:
      - SMUGMUG_USERNAME (your SmugMug nickname)
      - OAuth env vars used by get_oauth()

    This avoids relying on the SmugMug API root for discovery.
    """
    username = os.environ.get("SMUGMUG_USERNAME")
    if not username:
        raise HTTPException(status_code=500, detail="Missing env var: SMUGMUG_USERNAME")

    auth = get_oauth()
    headers = {"Accept": "application/json"}

    url = f"{SMUGMUG_BASE}/user/{username}"
    resp = requests.get(
        url,
        auth=auth,
        headers=headers,
        timeout=30,
        allow_redirects=False,
    )

    if resp.status_code != 200:
        raise_upstream(resp, url)

    data = resp.json()
    user = data.get("Response", {}).get("User", {})

    return {
        "username": username,
        "nickname": user.get("NickName"),
        "name": user.get("Name"),
        "uri": user.get("Uri"),
        "webUri": user.get("WebUri"),
        "uris": user.get("Uris"),
        "raw": user,
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

from urllib.parse import urlparse

from urllib.parse import urlparse

@app.get("/smugmug/resolve-nickname")
def smugmug_resolve_nickname(
    url: str = Query(..., description="Public SmugMug URL (custom domain or *.smugmug.com)"),
) -> Dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Invalid URL")

    # Fast-path for *.smugmug.com
    if parsed.netloc.endswith(".smugmug.com"):
        nickname = parsed.netloc.split(".")[0]
        return {"input": {"url": url}, "nickname": nickname, "source": "parsed-subdomain"}

    username = os.environ.get("SMUGMUG_USERNAME")
    if not username:
        raise HTTPException(status_code=500, detail="Missing env var: SMUGMUG_USERNAME")

    auth = get_oauth()
    headers = {"Accept": "application/json"}

    lookup_url = f"{SMUGMUG_BASE}/user/{username}!urlpathlookup"

    # Ask SmugMug to include the resolved object (Folder/Album/Page) in the response.
    # These param names are API-dependent; `_expand` is a common SmugMug pattern.
    params = {
        "urlpath": url,
        "_expand": "Folder,Album,Page",
        "ResponseLevel": "Full",
    }

    resp = requests.get(
        lookup_url,
        auth=auth,
        headers=headers,
        params=params,
        timeout=30,
        allow_redirects=False,
    )
    if resp.status_code != 200:
        raise_upstream(resp, resp.url)

    data = resp.json()
    r = data.get("Response", {})

    # Try to resolve via embedded object -> Uris.User.Uri
    for obj_key in ("Folder", "Album", "Page"):
        obj = r.get(obj_key)
        if isinstance(obj, dict):
            uris = obj.get("Uris") or {}
            u = uris.get("User")
            if isinstance(u, dict) and isinstance(u.get("Uri"), str):
                user_uri = u["Uri"].rstrip("/")
                nickname = user_uri.split("/")[-1]
                return {"input": {"url": url}, "nickname": nickname, "source": f"urlpathlookup:{obj_key}", "raw": data}

            # Fallback: sometimes the object itself might carry user-ish fields
            for k in ("NickName", "UserKey", "OwnerNickName"):
                if isinstance(obj.get(k), str) and obj.get(k):
                    return {"input": {"url": url}, "nickname": obj.get(k), "source": f"urlpathlookup:{obj_key}:field:{k}", "raw": data}

    # If not expanded, SmugMug will often still tell you what it resolved via Locator/LocatorType,
    # but won't include the object. In that case, you must do a second request to the returned Uri.
    uri = r.get("Uri")
    if isinstance(uri, str) and uri.startswith("/api/"):
        follow_url = f"https://api.smugmug.com{uri}"
        follow = requests.get(follow_url, auth=auth, headers=headers, timeout=30, allow_redirects=False)
        if follow.status_code != 200:
            raise_upstream(follow, follow_url)
        follow_data = follow.json()

        rr = follow_data.get("Response", {})
        for obj_key in ("Folder", "Album", "Page"):
            obj = rr.get(obj_key)
            if isinstance(obj, dict):
                uris = obj.get("Uris") or {}
                u = uris.get("User")
                if isinstance(u, dict) and isinstance(u.get("Uri"), str):
                    user_uri = u["Uri"].rstrip("/")
                    nickname = user_uri.split("/")[-1]
                    return {"input": {"url": url}, "nickname": nickname, "source": f"urlpathlookup-follow:{obj_key}", "raw": follow_data}

        return {"input": {"url": url}, "nickname": None, "source": "urlpathlookup-follow", "raw": follow_data}

    # Nothing resolved
    return {"input": {"url": url}, "nickname": None, "source": "urlpathlookup", "raw": data}