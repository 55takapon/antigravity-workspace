import csv
import glob
import json
import re
from urllib.parse import urlparse


def norm_name(value):
    value = re.sub(r"\s+", "", value or "").lower()
    for token in ("株式会社", "有限会社", "合同会社", "一般社団法人", "一般財団法人"):
        value = value.replace(token, "")
    return re.sub(r"[・･.,，。()（）\-ー_／/|｜]", "", value)


def domain(value):
    host = urlparse(value if "://" in (value or "") else "https://" + (value or "")).hostname or ""
    return host.lower().removeprefix("www.")


with open("data/_exclude_plus_existing_webmarketing_live.json", encoding="utf-8-sig") as handle:
    existing = json.load(handle)

names = {norm_name(row.get("company_name")) for row in existing if row.get("company_name")}
domains = {domain(row.get("url")) for row in existing if row.get("url")}

for path in glob.glob("data/agent_round*.csv"):
    if path.endswith("agent_round5_public_award_marketing.csv"):
        continue
    try:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("company_name"):
                    names.add(norm_name(row["company_name"]))
                if row.get("url"):
                    domains.add(domain(row["url"]))
    except (UnicodeDecodeError, csv.Error):
        pass

with open("data/round5_public_award_seeds.csv", encoding="utf-8-sig", newline="") as handle:
    seeds = list(csv.DictReader(handle))

kept = []
seen = set()
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

with open("data/round5_public_award_new_seeds.csv", "w", newline="", encoding="utf-8-sig") as handle:
    writer = csv.DictWriter(handle, fieldnames=["company_name", "url", "public_source"])
    writer.writeheader()
    writer.writerows(kept)
print(f"seed_unique={len(seen)} candidate_new={len(kept)}")
