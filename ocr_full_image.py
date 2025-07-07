import re
import requests
import time

# Azure Vision credentials
endpoint = "https://rkaiservices.cognitiveservices.azure.com/"
subscription_key = "ELAU37g5LqlprENL5F447z1RPhpZyKSg9uNvgF9WRycXiPXFqd3BJQQJ99BFACYeBjFXJ3w3AAAEACOGEFVW"  # <-- replace this

# Azure Read API URL
read_url = endpoint + "vision/v3.2/read/analyze"

# Load the full image
image_path = "IMG_6401-X2.jpg"
with open(image_path, "rb") as image_data:
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/octet-stream"
    }
    print("📤 Sending image to Azure Read API...")
    response = requests.post(read_url, headers=headers, data=image_data)

# Check initial response
if response.status_code != 202:
    raise Exception(f"API request failed: {response.text}")

# Extract operation URL
operation_url = response.headers["Operation-Location"]

# Poll for result
print("⏳ Waiting for OCR processing to complete...")
while True:
    result_response = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": subscription_key})
    result = result_response.json()
    if result["status"] in ["succeeded", "failed"]:
        break
    time.sleep(1)

# Display results
if result["status"] == "succeeded":
    print("✅ OCR results:")
    for page in result["analyzeResult"]["readResults"]:
        for line in page["lines"]:
            if re.match(r"^\d{2,5}$", line["text"]):  # 2–5 digit numbers
                print("🎽 Bib number detected:", line["text"])
else:
    print("❌ OCR failed.")
