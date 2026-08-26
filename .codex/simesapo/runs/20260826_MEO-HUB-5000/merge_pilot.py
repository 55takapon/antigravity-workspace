import csv
import re
import sys
from urllib.parse import urlparse


def norm_name(value):
    return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]", "", (value or "").lower())


def norm_domain(value):
    host = urlparse(value or "").netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def main():
    out, *inputs = sys.argv[1:]
    rows = []
    for path in inputs:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            rows.extend(csv.DictReader(handle))
    seen_names, seen_domains, kept = set(), set(), []
    for row in rows:
        name, domain = norm_name(row.get("company_name")), norm_domain(row.get("url"))
        if not name or not domain or name in seen_names or domain in seen_domains:
            continue
        seen_names.add(name)
        seen_domains.add(domain)
        kept.append(row)
    fields = list(kept[0]) if kept else ["company_name", "url", "address", "phone", "maps_url", "status"]
    with open(out, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(kept)
    print(f"input={len(rows)} unique={len(kept)}")


if __name__ == "__main__":
    main()
