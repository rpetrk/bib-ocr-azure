import requests
from requests_oauthlib import OAuth1

# SmugMug API credentials
api_key = 'qCJ9693fSX42hmh4RRb7FQccP7mcsMcx'
api_secret = 'pBd6nNGDVG7ZF4B34wQxPhg4qjSbHkHwmh7FcpTgPv8GH2SBtsZqWvhmcPKHC3V2'
access_token = 'DBRJhtMkwLr6Gr2PTzTNKM3LJjf2JLg7'
access_token_secret = 'hgJg5Q6htVZ8BDsfNPqrpsQ3MPNjZXqCqjV5s6GnGgjNx9DCQRQVz8jS3jLckQFV'

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
