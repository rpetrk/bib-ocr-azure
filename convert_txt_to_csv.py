# save as convert_txt_to_csv.py

input_file = "pikes_peek_2024_results.txt"   # ← your pasted text
output_file = "runners.csv"

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

with open(output_file, "w", encoding="utf-8") as out:
    for line in lines:
        line = line.strip()
        if line:
            parts = line.split("\t")
            out.write(",".join(parts) + "\n")

print("✅ Converted to runners.csv")
