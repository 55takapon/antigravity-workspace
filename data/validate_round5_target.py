import csv
import glob
import json
import re
from pathlib import Path
from urllib.parse import urlparse

TARGET = Path("data/agent_round7_official_association_marketing.csv")


def norm_name(value):
    value = re.sub(r"\s+", "", value or "").lower()
    for token in ("株式会社", "有限会社", "合同会社", "一般社団法人", "一般財団法人"):
        value = value.replace(token, "")
    return re.sub(r"[・･.,，。()（）\-ー_／/|｜]", "", value)


def norm_domain(value):
    raw = value or ""
    host = urlparse(raw if "://" in raw else "https://" + raw).hostname or ""
    return host.lower().removeprefix("www.")


def norm_phone(value):
    return re.sub(r"\D", "", value or "")


with TARGET.open(encoding="utf-8-sig", newline="") as handle:
    target = list(csv.DictReader(handle))

with open("data/_exclude_plus_existing_webmarketing_live.json", encoding="utf-8-sig") as handle:
    existing = json.load(handle)

for path in glob.glob("data/agent_round*.csv"):
    if Path(path).resolve() == TARGET.resolve():
        continue
    try:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            existing.extend(csv.DictReader(handle))
    except (UnicodeDecodeError, csv.Error):
        pass

names = {norm_name(r.get("company_name")) for r in existing if r.get("company_name")}
domains = {norm_domain(r.get("url")) for r in existing if r.get("url")}
phones = {norm_phone(r.get("phone")) for r in existing if norm_phone(r.get("phone"))}

collisions = []
seen_domains = set()
for row in target:
    reasons = []
    company = norm_name(row.get("company_name"))
    host = norm_domain(row.get("url"))
    phone = norm_phone(row.get("phone"))
    if company in names:
        reasons.append("name")
    if host in domains:
        reasons.append("domain")
    if phone and phone in phones:
        reasons.append("phone")
    if host in seen_domains:
        reasons.append("duplicate_domain")
    seen_domains.add(host)
    if reasons:
        collisions.append((row.get("company_name"), host, reasons))

required_missing = [
    (index + 2, row.get("company_name"))
    for index, row in enumerate(target)
    if not row.get("company_name") or not row.get("url") or not row.get("address")
]

print(f"rows={len(target)}")
print(f"unique_domains={len(seen_domains)}")
print(f"required_missing={len(required_missing)}")
print(f"collisions={len(collisions)}")
for item in collisions:
    print(item)
