import os
import requests
import time
import re
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
subscription_key = os.getenv("AZURE_VISION_KEY")
endpoint = os.getenv("AZURE_VISION_ENDPOINT")

if not subscription_key or not endpoint:
    raise Exception("Missing AZURE_VISION_KEY or AZURE_VISION_ENDPOINT in .env")

read_url = endpoint.rstrip("/") + "/vision/v3.2/read/analyze"
image_folder = "r4PXN6"
supported_extensions = (".jpg", ".jpeg", ".png")
image_bib_map = {}

# Get list of all image files
image_files = [
    f for f in os.listdir(image_folder)
    if f.lower().endswith(supported_extensions)
]
total_images = len(image_files)

print(f"📁 Found {total_images} image(s) to process...")

# Loop with progress display
for idx, filename in enumerate(image_files, start=1):
    image_path = os.path.join(image_folder, filename)
    percent_done = int((idx / total_images) * 100)

    print(f"\n📤 [{idx}/{total_images}] ({percent_done}%) Processing: {filename}")

    with open(image_path, "rb") as image_data:
        headers = {
            "Ocp-Apim-Subscription-Key": subscription_key,
            "Content-Type": "application/octet-stream"
        }
        response = requests.post(read_url, headers=headers, data=image_data)

    if response.status_code != 202:
        print(f"❌ Failed on {filename}: {response.text}")
        continue

    operation_url = response.headers["Operation-Location"]

    while True:
        result_response = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": subscription_key})
        result = result_response.json()
        if result["status"] in ["succeeded", "failed"]:
            break
        time.sleep(1)

    bibs = set()
    if result["status"] == "succeeded":
        for page in result["analyzeResult"]["readResults"]:
            for line in page["lines"]:
                text = line["text"]
                if re.match(r"^\d{2,5}$", text):
                    bibs.add(text)

    image_bib_map[filename] = sorted(bibs)
    print(f"✅ Bibs: {sorted(bibs)}")

# Save results
with open("bib_tags.json", "w") as f:
    json.dump(image_bib_map, f, indent=2)

print("\n🏁 OCR complete! Results saved to bib_tags.json")
