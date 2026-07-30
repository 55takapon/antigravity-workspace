import csv
import json
import re
from urllib.parse import urlparse


def compact(value):
    return re.sub(r"\s+", "", value or "").lower()


def norm_name(value):
    value = compact(value)
    for token in ("株式会社", "有限会社", "合同会社", "一般社団法人", "一般財団法人"):
        value = value.replace(token, "")
    return re.sub(r"[・･.,，。()（）\-ー_／/|｜]", "", value)


def domain(value):
    host = urlparse(value if "://" in value else "https://" + value).hostname or ""
    return host.lower().removeprefix("www.")


with open("data/_exclude_plus_existing_webmarketing_live.json", encoding="utf-8-sig") as handle:
    existing = json.load(handle)
names = {norm_name(row.get("company_name")) for row in existing if row.get("company_name")}
domains = {domain(row.get("url")) for row in existing if row.get("url")}

with open("data/round4_public_award_seeds.csv", encoding="utf-8-sig") as handle:
    seeds = list(csv.DictReader(handle))

seen = set()
kept = []
for row in seeds:
    host = domain(row["url"])
    if host in seen:
        continue
    seen.add(host)
    reasons = []
    if norm_name(row["company_name"]) in names:
        reasons.append("name")
    if host in domains:
        reasons.append("domain")
    print(("DROP " + ",".join(reasons)) if reasons else "KEEP", row["company_name"], host)
    if not reasons:
        kept.append(row)

with open("data/round4_public_award_new_seeds.csv", "w", newline="", encoding="utf-8-sig") as handle:
    writer = csv.DictWriter(handle, fieldnames=["company_name", "url", "public_source"])
    writer.writeheader()
    writer.writerows(kept)
print(f"seed_unique={len(seen)} candidate_new={len(kept)}")
