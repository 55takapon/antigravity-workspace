import csv
from pathlib import Path
from urllib.parse import urlparse


def domain(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


paths = sorted(Path("data").glob("sns_*candidates_wave*.csv"))
paths += [Path("data/sns_existing_maps_unseen_all.csv")]
rows, seen = [], set()
for path in paths:
    if not path.exists():
        continue
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            url = (row.get("url") or row.get("website") or "").strip()
            key = domain(url)
            if not key or key in seen:
                continue
            seen.add(key)
            rows.append({
                "company_name": row.get("company_name") or row.get("title") or "",
                "url": url,
                "address": row.get("address", ""),
                "phone": row.get("phone", ""),
                "maps_url": row.get("maps_url", ""),
                "area_hint": row.get("area_hint") or row.get("area") or "",
                "query": row.get("query", ""),
            })
fields = ["company_name", "url", "address", "phone", "maps_url", "area_hint", "query"]
with Path("data/sns_candidate_archive_merged.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader(); writer.writerows(rows)
print(f"files={len(paths)} domains={len(rows)}")
