import csv
import json

# Load bib tags from JSON
with open("bib_tags.json") as f:
    bib_map = json.load(f)  # image -> [bib1, bib2]

# Load runner data
runners = {}
with open("runners.csv", newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        bib = row["Num"].strip()
        name = row["Name"].strip().lower()
        runners[bib] = name

# Reverse lookup: name → bib
name_to_bib = {v: k for k, v in runners.items()}

# ---- Search Interface ----
print("\n🎽 Search by bib number or runner name (type 'exit' to quit):")

while True:
    query = input("🔍 Search: ").strip().lower()
    if query == "exit":
        break

    matched_bibs = set()

    if query.isdigit():
        matched_bibs.add(query)
    else:
        # Search by partial name match
        for name, bib in name_to_bib.items():
            if query in name:
                matched_bibs.add(bib)

    if not matched_bibs:
        print("❌ No matches found.")
        continue

    # Find all matching images
    matching_images = []
    for image, bibs in bib_map.items():
        if any(bib in bibs for bib in matched_bibs):
            matching_images.append(image)

    if matching_images:
        print(f"📸 Found {len(matching_images)} image(s):")
        for img in matching_images:
            print("   ", img)
    else:
        print("❌ No images found with that bib.")
