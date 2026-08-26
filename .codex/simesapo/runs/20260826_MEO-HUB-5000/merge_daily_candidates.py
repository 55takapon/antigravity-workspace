import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


def name_key(value):
    return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]", "", (value or "").lower())


def domain_key(value):
    host = urlparse(value or "").netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def phone_key(value):
    return re.sub(r"\D", "", value or "")


def load(path):
    if path.lower().endswith(".json"):
        text = Path(path).read_text(encoding="utf-8-sig")
        if text.lstrip().startswith(("[", "{")):
            return json.loads(text)
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


output, existing_path, *inputs = sys.argv[1:]
existing = load(existing_path)
names = {name_key(x.get("company_name")) for x in existing if x.get("company_name")}
domains = {domain_key(x.get("url")) for x in existing if domain_key(x.get("url"))}
phones = {phone_key(x.get("phone")) for x in existing if len(phone_key(x.get("phone"))) >= 9}
kept = []
for path in inputs:
    if not Path(path).exists():
        continue
    for row in load(path):
        n, d, p = name_key(row.get("company_name")), domain_key(row.get("url")), phone_key(row.get("phone"))
        if not n or not d or n in names or d in domains or (len(p) >= 9 and p in phones):
            continue
        names.add(n); domains.add(d)
        if len(p) >= 9: phones.add(p)
        kept.append(row)
fields = ["company_name", "url", "address", "phone", "maps_url", "status", "source_url", "business_description", "hub_evidence", "recurring_evidence"]
with open(output, "w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
    writer.writeheader(); writer.writerows(kept)
print(f"merged={len(kept)}")
