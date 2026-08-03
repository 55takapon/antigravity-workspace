from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).parent

def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

main_seed = read_csv(HERE / "education_candidate_seed.csv")
main_contacts = read_csv(HERE / "education_with_contacts.csv")
supp = read_csv(HERE / "education_supplement_seed.csv")
payload = json.loads((HERE / "education_supplement_contacts.json").read_text(encoding="utf-8"))
results = {int(row["idx"]): row for row in payload["results"]}

accepted = []
for idx, row in enumerate(supp):
    result = results.get(idx, {})
    contact = result.get("contact_url", "")
    if result.get("confidence") != "high" or not contact or "email-protection" in contact:
        continue
    row["contact_url"] = contact
    accepted.append(row)

existing = {row["company_name"] for row in main_seed}
accepted = [row for row in accepted if row["company_name"] not in existing]
fields = ["company_name", "url", "contact_url", "区分", "検出ワード", "source_url"]
for path, rows in (
    (HERE / "education_candidate_seed.csv", main_seed + accepted),
    (HERE / "education_with_contacts.csv", main_contacts + accepted),
):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)

print(json.dumps({"supplement_accepted": len(accepted), "total": len(main_contacts) + len(accepted)}, ensure_ascii=False))
