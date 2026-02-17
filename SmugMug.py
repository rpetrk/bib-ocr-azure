import requests
from requests_oauthlib import OAuth1

# SmugMug API credentials
api_key = 'zPgGc7tRXxZHs7PgmkSKcTfcwzpRfD23'
api_secret = 'kTstmwxFJ7Ms6nkBvF5cDPv4RcGJZw6q8JJnP3NMd665Tbwf7gH4Vztb6W8GqBWz'
access_token = 'J9BX5DFCjrcGvJLXbcTgX74nxHfDWLcT'
access_token_secret = 'FWPFmGxkKMS4n8kQsPXPCCZp8dtvcCbnrhLJbrNFGfh84ZFXm3tqMTd4tgKNJrj2'

# OAuth authentication setup
auth = OAuth1(api_key, api_secret, access_token, access_token_secret)

# SmugMug API endpoint to retrieve albums for a user
url = 'https://api.smugmug.com/api/v2/user/mcrrcphotos!albums'

headers = {
    'Accept': 'application/json'
}

albums = []  # To store all albums
has_more = True  # To keep track of pagination
start = 1  # Starting index for pagination
count = 50  # Number of albums to fetch per page (adjust as needed)

while has_more:
    # Add pagination parameters to URL
    paginated_url = f"{url}?start={start}&count={count}"

    # Make a GET request to the API to fetch albums
    response = requests.get(paginated_url, auth=auth, headers=headers)

    print("STATUS:", response.status_code)
    print("CONTENT-TYPE:", response.headers.get("Content-Type"))
    print("FIRST 500 CHARS:", response.text[:500])


    if 'json' in response.headers.get('Content-Type', ''):
        try:
            data = response.json()

            # Access the albums data
            current_albums = data.get('Response', {}).get('Album', [])
            albums.extend(current_albums)  # Append current page albums to the full list

            # Check if there's more data (pagination)
            has_more = data.get('Response', {}).get('Pages', {}).get('NextPage') is not None

            if has_more:
                # Move to the next page
                start += count  # Increment start for the next page

        except ValueError as e:
            print(f"Error parsing JSON: {e}")
            has_more = False
    else:
        print("Expected JSON but got something else.")
        print(f"Response Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response Content: {response.text}")
        has_more = False

# Now you can get the total number of albums
album_count = len(albums)
print(f"Total number of albums: {album_count}")

# Write album details to a file
with open('albums.txt', 'w') as file:
    for album in albums:
        title = album.get('Title', 'N/A')
        album_key = album.get('AlbumKey', 'N/A')
        url_path = album.get('Uri', 'N/A')
        DateCreated = album.get('DateCreated', 'N/A')
        ImageCount = album.get('ImageCount', 'N/A')
        LastUpdated = album.get('LastUpdated', 'N/A')

        file.write(f"Album Title: {title}\n")
        file.write(f"Album Key: {album_key}\n")
        file.write(f"Album URL: {url_path}\n")
        file.write(f"DateCreated: {DateCreated}\n")
        file.write(f"ImageCount: {ImageCount}\n")
        file.write(f"LastUpdated: {LastUpdated}\n")
        file.write("\n")  # Add a blank line between albums

print("Album details written to albums.txt.")
