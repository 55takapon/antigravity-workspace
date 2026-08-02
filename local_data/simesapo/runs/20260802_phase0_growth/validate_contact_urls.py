import csv
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests

SOURCE = Path(__file__).resolve().parent / "construction_candidate_pool.csv"

def check(row):
    try:
        r = requests.get(row["contact_url"], timeout=8, allow_redirects=True, headers={"User-Agent":"Mozilla/5.0"})
        return row["company_name"], r.status_code, r.url
    except requests.RequestException as e:
        return row["company_name"], "error", type(e).__name__

with SOURCE.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
with ThreadPoolExecutor(max_workers=10) as pool:
    results = list(pool.map(check, rows))
for item in results:
    print(item)
