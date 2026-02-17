import os
import requests
from requests_oauthlib import OAuth1

# SmugMug API credentials
api_key = 'qCJ9693fSX42hmh4RRb7FQccP7mcsMcx'
api_secret = 'pBd6nNGDVG7ZF4B34wQxPhg4qjSbHkHwmh7FcpTgPv8GH2SBtsZqWvhmcPKHC3V2'
access_token = 'DBRJhtMkwLr6Gr2PTzTNKM3LJjf2JLg7'
access_token_secret = 'hgJg5Q6htVZ8BDsfNPqrpsQ3MPNjZXqCqjV5s6GnGgjNx9DCQRQVz8jS3jLckQFV'

# OAuth authentication setup
auth = OAuth1(api_key, api_secret, access_token, access_token_secret)

def download_images_from_album(album_key):
    # API endpoint to retrieve images from a specific album
    url = f'https://api.smugmug.com/api/v2/album/{album_key}!images'
    
    # Set headers to request JSON
    headers = {
        'Accept': 'application/json'
    }

    start = 1  # Starting index for pagination
    count = 100  # Number of images to fetch per request
    has_more = True  # To track if there are more images to fetch

    while has_more:
        # Add pagination parameters to the URL
        paginated_url = f"{url}?start={start}&count={count}"

        # Make a GET request to fetch images in the album
        response = requests.get(paginated_url, auth=auth, headers=headers)

        if 'json' in response.headers.get('Content-Type', ''):
            try:
                data = response.json()
                images = data.get('Response', {}).get('AlbumImage', [])

                if not images:
                    print("No more images found in this album.")
                    break  # Exit if no images are returned

                # Create a directory to save images if it doesn't exist
                os.makedirs(album_key, exist_ok=True)

                for image in images:
                    # Get the image URL using ArchivedUri
                    image_url = image.get('ArchivedUri', '')
                    if image_url:
                        # Download the image
                        image_response = requests.get(image_url)
                        if image_response.status_code == 200:
                            # Extract the image filename from the URL
                            filename = os.path.join(album_key, os.path.basename(image_url))
                            with open(filename, 'wb') as img_file:
                                img_file.write(image_response.content)
                            print(f"Downloaded: {filename}")
                        else:
                            print(f"Failed to download image: {image_url}")
                    else:
                        print("Image URL not found.")
                
                # Increment start for the next batch of images
                start += count
                has_more = len(images) == count  # Check if we got the full count of images

            except ValueError as e:
                print(f"Error parsing JSON: {e}")
                break
        else:
            print("Expected JSON but got something else.")
            print(f"Response Content-Type: {response.headers.get('Content-Type')}")
            print(f"Response Content: {response.text}")
            break
        
# Example usage
album_key = 'r4PXN6'  # Replace with your actual album key
download_images_from_album(album_key)
