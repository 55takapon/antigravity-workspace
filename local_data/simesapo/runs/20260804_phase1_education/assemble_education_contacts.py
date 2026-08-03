from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).parent
SEED = HERE / "education_candidate_seed.csv"
RESULTS = HERE / "education_contact_results.json"
OUTPUT = HERE / "education_with_contacts.csv"

with SEED.open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
payload = json.loads(RESULTS.read_text(encoding="utf-8"))
by_idx = {int(item["idx"]): item for item in payload["results"]}
for idx, row in enumerate(rows):
    result = by_idx.get(idx, {})
    if result.get("confidence") == "high" and result.get("contact_url"):
        row["contact_url"] = result["contact_url"]

with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["company_name", "url", "contact_url", "区分", "検出ワード", "source_url"])
    writer.writeheader()
    writer.writerows(rows)

print(json.dumps({"input": len(rows), "contact_url": sum(bool(row["contact_url"]) for row in rows)}, ensure_ascii=False))
