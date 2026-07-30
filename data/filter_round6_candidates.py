import csv
import glob
import json
import re
from pathlib import Path
from urllib.parse import urlparse

SOURCE = Path("data/round9_verified_for_001.csv")
OUTPUT = Path("data/round9_verified_new_for_001.csv")


def name(value):
    value = re.sub(r"\s+", "", value or "").lower()
    for token in ("株式会社", "有限会社", "合同会社", "一般社団法人", "一般財団法人"):
        value = value.replace(token, "")
    return re.sub(r"[・･.,，。()（）\-ー_／/|｜]", "", value)


def domain(value):
    raw = value or ""
    host = urlparse(raw if "://" in raw else "https://" + raw).hostname or ""
    return host.lower().removeprefix("www.")


def phone(value):
    return re.sub(r"\D", "", value or "")


with open("data/_exclude_plus_existing_webmarketing_live.json", encoding="utf-8-sig") as handle:
    existing = json.load(handle)

for path in glob.glob("data/agent_round*.csv"):
    try:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            existing.extend(csv.DictReader(handle))
    except (UnicodeDecodeError, csv.Error):
        pass

names = {name(r.get("company_name")) for r in existing if r.get("company_name")}
domains = {domain(r.get("url")) for r in existing if r.get("url")}
phones = {phone(r.get("phone")) for r in existing if phone(r.get("phone"))}

with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
    candidates = list(csv.DictReader(handle))

kept = []
for row in candidates:
    reasons = []
    if name(row["company_name"]) in names:
        reasons.append("name")
    if domain(row["url"]) in domains:
        reasons.append("domain")
    if phone(row["phone"]) and phone(row["phone"]) in phones:
        reasons.append("phone")
    print(("DROP " + ",".join(reasons)) if reasons else "KEEP", row["company_name"])
    if not reasons:
        kept.append(row)

with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=candidates[0].keys())
    writer.writeheader()
    writer.writerows(kept)

print(f"candidate={len(candidates)} kept={len(kept)}")
