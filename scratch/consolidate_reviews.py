
import json
import os
import re

def parse_txt_to_list(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by the separator used in the files
    sep = "-" * 50
    raw_blocks = [b.strip() for b in content.split(sep) if b.strip()]
    
    parsed = []
    for block in raw_blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            name = lines[0].strip()
            rating_date = lines[1].strip() # e.g. "5 stars - 1 か月前"
            
            # Extract rating and date
            rating = "N/A"
            date = "Unknown"
            if " stars - " in rating_date:
                parts = rating_date.split(" stars - ")
                rating = parts[0] + " stars"
                date = parts[1]
            
            text = "\n".join(lines[2:]).strip()
            
            parsed.append({
                "name": name,
                "rating": rating,
                "date": date,
                "text": text
            })
    return parsed

base_dir = r'c:\Users\hangy\.gemini\antigravity\scratch\google_maps_data'
bomnal_file = os.path.join(base_dir, 'extracted_reviews.txt')
iami_file = os.path.join(base_dir, 'izakaya_iami_reviews.txt')

bomnal_reviews = parse_txt_to_list(bomnal_file)
iami_reviews = parse_txt_to_list(iami_file)

all_reviews = {
    "bomnal_chicken": bomnal_reviews,
    "izakaya_iami": iami_reviews,
    "total_count": len(bomnal_reviews) + len(iami_reviews)
}

output_path = r'c:\Users\hangy\.gemini\antigravity\scratch\consolidated_55_reviews.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(all_reviews, f, ensure_ascii=False, indent=2)

print(f"Consolidated {len(bomnal_reviews)} reviews from Bomnal and {len(iami_reviews)} from Iami.")
print(f"Saved to {output_path}")
