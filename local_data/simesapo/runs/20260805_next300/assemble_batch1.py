from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).parent
SOURCES = [HERE / "aca_crawled.csv", HERE / "oac_crawled.csv"]
OUTPUT = HERE / "batch1_seed.csv"


def domain(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


rows = []
seen = set()
for source in SOURCES:
    with source.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = domain(row.get("url", ""))
            if not key or key in seen:
                continue
            if row.get("company_confirmed") != "yes" or not row.get("contact_url"):
                continue
            seen.add(key)
            rows.append(row)

fields = list(rows[0])
with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)

print({"input_sources": len(SOURCES), "official_profile_and_contact": len(rows), "output": str(OUTPUT)})
