import csv
import re
from pathlib import Path
from urllib.parse import urlparse


def name_key(value):
    value = (value or "").lower()
    value = value.replace("株式会社", "").replace("有限会社", "").replace("合同会社", "")
    return re.sub(r"\W+", "", value)


def clean_name(value):
    value = re.sub(r"[\u200b-\u200d\ufeff]", "", value or "").strip()
    value = re.sub(r"^\d{4}\s+", "", value)
    value = re.sub(r"\s+(?:All Rights Reserved\.?|technology\.)\s*$", "", value, flags=re.I)
    return value.strip()


def domain(value):
    try:
        return urlparse(value).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


paths = [
    Path("data/sns_official_strict_v4.csv"),
    Path("data/sns_official_strict_wave7_v4.csv"),
    Path("data/sns_official_strict_wave8_v4.csv"),
    Path("data/sns_official_strict_wave9_v4.csv"),
]
rows, names, domains, phones = [], set(), set(), set()
for path in paths:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            row["company_name"] = clean_name(row.get("company_name", ""))
            if re.match(r"^by\s+", row["company_name"], re.I):
                continue
            nk, dk = name_key(row.get("company_name")), domain(row.get("url", ""))
            pk = re.sub(r"\D", "", row.get("phone", ""))
            if not nk or not dk or nk in names or dk in domains or (len(pk) >= 9 and pk in phones):
                continue
            names.add(nk); domains.add(dk)
            if len(pk) >= 9:
                phones.add(pk)
            rows.append(row)
fields = ["company_name", "url", "address", "phone", "maps_url", "contact_url"]
with Path("data/sns_strict_merged.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader(); writer.writerows({key: row.get(key, "") for key in fields} for row in rows)
print(f"merged={len(rows)}")
