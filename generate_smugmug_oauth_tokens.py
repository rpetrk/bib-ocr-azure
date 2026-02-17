from requests_oauthlib import OAuth1Session

CONSUMER_KEY = "zPgGc7tRXxZHs7PgmkSKcTfcwzpRfD23"
CONSUMER_SECRET = "kTstmwxFJ7Ms6nkBvF5cDPv4RcGJZw6q8JJnP3NMd665Tbwf7gH4Vztb6W8GqBWz"

REQUEST_TOKEN_URL = "https://api.smugmug.com/services/oauth/1.0a/getRequestToken"
AUTHORIZE_URL     = "https://api.smugmug.com/services/oauth/1.0a/authorize"
ACCESS_TOKEN_URL  = "https://api.smugmug.com/services/oauth/1.0a/getAccessToken"

# 1) Get a request token
oauth = OAuth1Session(CONSUMER_KEY, client_secret=CONSUMER_SECRET, callback_uri="oob")
rt = oauth.fetch_request_token(REQUEST_TOKEN_URL)

request_token = rt["oauth_token"]
request_secret = rt["oauth_token_secret"]

print("\nOpen this URL in your browser and approve:")
print(f"{AUTHORIZE_URL}?oauth_token={request_token}")

# 2) User approves, then SmugMug provides a verifier
verifier = input("\nPaste oauth_verifier here: ").strip()

# 3) Exchange for access token
oauth = OAuth1Session(
    CONSUMER_KEY,
    client_secret=CONSUMER_SECRET,
    resource_owner_key=request_token,
    resource_owner_secret=request_secret,
    verifier=verifier,
)

at = oauth.fetch_access_token(ACCESS_TOKEN_URL)

print("\n=== SAVE THESE (this is what your app uses) ===")
print("ACCESS_TOKEN        =", at["oauth_token"])
print("ACCESS_TOKEN_SECRET =", at["oauth_token_secret"])
