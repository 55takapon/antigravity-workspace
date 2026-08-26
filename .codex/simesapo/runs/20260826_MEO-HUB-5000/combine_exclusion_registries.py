import csv,re,sys
from pathlib import Path
from urllib.parse import urlparse

base,extra,out=map(Path,sys.argv[1:4])
def nk(v):return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]","",(v or "").lower())
def dk(v):
 h=urlparse(v or "").netloc.lower().split(":")[0];return h[4:] if h.startswith("www.") else h
def pk(v):return re.sub(r"\D","",v or "")
rows=[];seen=set();fields=[]
for path in (base,extra):
 reader=csv.DictReader(open(path,encoding="utf-8-sig",newline=""))
 for field in reader.fieldnames or []:
  if field not in fields:fields.append(field)
 for r in reader:
  keys={x for x in ("n:"+nk(r.get("company_name")),"d:"+dk(r.get("url")),"p:"+pk(r.get("phone"))) if x not in ("n:","d:","p:")}
  if keys & seen:continue
  seen|=keys;rows.append(r)
with open(out,"w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
print(f"combined={len(rows)}")
