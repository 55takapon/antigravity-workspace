import csv
import glob
import json
import re
import sys
from urllib.parse import urlparse


def norm_domain(value):
    host = urlparse(value or "").netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def norm_name(value):
    return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]", "", (value or "").lower())


source, output, url_glob, name_glob = sys.argv[1:5]
domains, names = set(), set()
for path in glob.glob(url_glob):
    domains.update(norm_domain(value) for value in json.load(open(path, encoding="utf-8")))
for path in glob.glob(name_glob):
    names.update(norm_name(value) for value in json.load(open(path, encoding="utf-8")))
with open(source, encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
kept = [row for row in rows if norm_name(row.get("company_name")) in names or norm_domain(row.get("url")) in domains]
with open(output, "w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(kept)
print(f"kept={len(kept)} names={len(names)} domains={len(domains)}")
