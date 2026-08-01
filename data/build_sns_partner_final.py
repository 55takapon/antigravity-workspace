import csv
import re
from pathlib import Path
from urllib.parse import urlparse


FILES = [Path("data/sns_partner_archive_affinity_v5.csv")]
FILES.extend(Path(f"data/sns_partner_affinity_wave{i}_v5.csv") for i in range(2, 19))
FILES.extend(Path(f"data/sns_secondary_affinity_{i}.csv") for i in range(10))
FILES.append(Path("data/sns_secondary_affinity_10_13.csv"))
FILES.append(Path("data/sns_partner_recovered_noncompetitors_v5.csv"))
FILES.append(Path("data/sns_partner_recovered_noncompetitors_v6.csv"))
FILES.append(Path("data/sns_partner_recovered_noncompetitors_v7.csv"))
FILES.append(Path("data/sns_partner_recovered_noncompetitors_v8.csv"))
FILES.append(Path("data/sns_partner_recovered_noncompetitors_v9.csv"))
FILES.append(Path("data/sns_partner_recovered_noncompetitors_v10.csv"))
FILES.append(Path("data/sns_partner_recovered_noncompetitors_v11.csv"))
FILES.append(Path("data/sns_partner_recovered_noncompetitors_v12.csv"))
FILES.append(Path("data/sns_partner_recovered_noncompetitors_v13.csv"))
FILES.append(Path("data/sns_partner_recovered_noncompetitors_v14.csv"))
GRADE = {"A": 0, "B": 1, "C": 2}


def norm_name(value):
    return re.sub(r"[^0-9a-z一-龠ぁ-んァ-ヶ]", "", (value or "").lower())


def norm_phone(value):
    return re.sub(r"\D", "", value or "")


rows = []
for path in FILES:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows.extend(csv.DictReader(handle))
rows.sort(key=lambda row: (GRADE.get(row.get("affinity_grade", "C"), 9), -int(row.get("affinity_score") or 0)))

kept = []
domains, names, phones = set(), set(), set()
for row in rows:
    domain = urlparse(row.get("url", "")).netloc.lower().removeprefix("www.")
    name = norm_name(row.get("company_name", ""))
    phone = norm_phone(row.get("phone", ""))
    if not domain or domain in domains or (name and name in names) or (phone and phone in phones):
        continue
    domains.add(domain)
    if name:
        names.add(name)
    if phone:
        phones.add(phone)
    kept.append({key: row.get(key, "") for key in ["company_name", "url", "address", "phone", "maps_url"]})

output = Path("data/sns_partner_final_precore.csv")
with output.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["company_name", "url", "address", "phone", "maps_url"])
    writer.writeheader()
    writer.writerows(kept)
print(f"input={len(rows)} kept={len(kept)} output={output}")
