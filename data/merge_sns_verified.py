import csv
import re
from pathlib import Path
from urllib.parse import urlparse


def norm_name(value):
    value = (value or "").lower()
    value = value.replace("株式会社", "").replace("有限会社", "").replace("合同会社", "")
    return re.sub(r"[\s　・･.,，。\-―ー_｜|/()（）【】\[\]]+", "", value)


def host(value):
    try:
        return urlparse(value).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def phone(value):
    return re.sub(r"\D", "", value or "")


def contact_url(value):
    for candidate in (value or "").split(" | "):
        if re.search(r"(contact|inquiry|otoiawase|toiawase|お問い合わせ)", candidate, re.I):
            return candidate.strip()
    return ""


rows = []
seen_names, seen_hosts, seen_phones = set(), set(), set()
for path in sorted(Path("data").glob("sns_verified_wave*.csv")):
    if path.stem.endswith("_audit"):
        continue
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            name_key, host_key, phone_key = norm_name(row.get("company_name")), host(row.get("url", "")), phone(row.get("phone"))
            if not name_key or not host_key:
                continue
            if name_key in seen_names or host_key in seen_hosts or (len(phone_key) >= 9 and phone_key in seen_phones):
                continue
            seen_names.add(name_key); seen_hosts.add(host_key)
            if len(phone_key) >= 9:
                seen_phones.add(phone_key)
            rows.append({
                **{key: row.get(key, "") for key in ("company_name", "url", "address", "phone", "maps_url")},
                "contact_url": contact_url(row.get("pages_checked", "")),
            })

fields = ["company_name", "url", "address", "phone", "maps_url", "contact_url"]
with Path("data/sns_verified_merged.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader(); writer.writerows(rows)
print(f"merged={len(rows)}")
