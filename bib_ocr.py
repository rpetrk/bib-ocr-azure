# bib_ocr.py
import requests
import time

endpoint = "https://rkaiservices.cognitiveservices.azure.com/"
subscription_key = "ELAU37g5LqlprENL5F447z1RPhpZyKSg9uNvgF9WRycXiPXFqd3BJQQJ99BFACYeBjFXJ3w3AAAEACOGEFVW"  # <-- replace this

read_url = endpoint + "vision/v3.2/read/analyze"
image_files = ["bib_left.jpg", "bib_right.jpg"]

for image_file in image_files:
    print(f"\n📤 Sending image: {image_file}")
    
    with open(image_file, "rb") as image_data:
        headers = {
            "Ocp-Apim-Subscription-Key": subscription_key,
            "Content-Type": "application/octet-stream"
        }
        response = requests.post(read_url, headers=headers, data=image_data)

    if response.status_code != 202:
        raise Exception(f"API call failed: {response.text}")

    operation_url = response.headers["Operation-Location"]

    while True:
        result_response = requests.get(operation_url, headers={"Ocp-Apim-Subscription-Key": subscription_key})
        result = result_response.json()
        if result["status"] in ["succeeded", "failed"]:
            break
        time.sleep(1)

    if result["status"] == "succeeded":
        print("✅ Text found:")
        for page in result["analyzeResult"]["readResults"]:
            for line in page["lines"]:
                print("   ", line["text"])
    else:
        print("❌ OCR failed.")
