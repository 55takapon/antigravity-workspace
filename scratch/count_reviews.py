
import os

def count_reviews(file_path):
    if not os.path.exists(file_path):
        return 0
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Separator is a long line of dashes. Let's split by it.
    # The separator seems to be at least 10 dashes based on my grep attempt.
    # Looking at view_file, it's 50 dashes.
    sep = "-" * 10
    reviews = [r for r in content.split(sep) if r.strip()]
    return len(reviews)

base_path = r'c:\Users\hangy\.gemini\antigravity\scratch\google_maps_data'
files = ['extracted_reviews.txt', 'izakaya_iami_reviews.txt']

for f in files:
    path = os.path.join(base_path, f)
    count = count_reviews(path)
    print(f"{f}: {count} reviews")
