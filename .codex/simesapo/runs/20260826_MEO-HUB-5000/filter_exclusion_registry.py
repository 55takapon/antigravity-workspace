import csv
import re
import sys
from urllib.parse import urlparse

source, registry, output = sys.argv[1:4]
def nk(v): return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]", "", (v or "").lower())
def dk(v):
    h=urlparse(v or "").netloc.lower().split(":")[0]
    return h[4:] if h.startswith("www.") else h
def pk(v): return re.sub(r"\D", "", v or "")

excluded=list(csv.DictReader(open(registry,encoding="utf-8-sig",newline="")))
names={nk(x.get("company_name")) for x in excluded if x.get("company_name")}
domains={x.get("normalized_domain") or dk(x.get("url")) for x in excluded if x.get("normalized_domain") or x.get("url")}
phones={pk(x.get("phone")) for x in excluded if len(pk(x.get("phone")))>=9}
rows=list(csv.DictReader(open(source,encoding="utf-8-sig",newline="")))
kept=[]; dropped=[]
for row in rows:
    if nk(row.get("company_name")) in names or dk(row.get("url")) in domains or (len(pk(row.get("phone")))>=9 and pk(row.get("phone")) in phones): dropped.append(row)
    else: kept.append(row)
fields=list(rows[0].keys()) if rows else []
with open(output,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(kept)
print(f"input={len(rows)} kept={len(kept)} excluded={len(dropped)}")
