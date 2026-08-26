import csv,json,re,sys
from urllib.parse import urlparse
rows=list(csv.DictReader(open(sys.argv[1],encoding="utf-8-sig",newline="")))
def nk(v):return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]","",(v or "").lower())
def dk(v):
 h=urlparse(v or "").netloc.lower().split(":")[0];return h[4:] if h.startswith("www.") else h
def pk(v):return re.sub(r"\D","",v or "")
def dups(vals):
 seen=set();dup=set()
 for v in vals:
  if not v:continue
  if v in seen:dup.add(v)
  seen.add(v)
 return sorted(dup)
report={"rows":len(rows),"blank_company_name":sum(not r.get("company_name","").strip() for r in rows),"blank_url":sum(not r.get("url","").strip() for r in rows),"blank_why_fit":sum(not r.get("why_fit","").strip() for r in rows),"blank_evidence_urls":sum(not r.get("evidence_urls","").strip() for r in rows),"not_verified":sum(r.get("review_status")!="VERIFIED" for r in rows),"duplicate_names":dups([nk(r.get("company_name")) for r in rows]),"duplicate_domains":dups([dk(r.get("url")) for r in rows]),"duplicate_phones":dups([pk(r.get("phone")) if len(pk(r.get("phone")))>=9 else "" for r in rows])}
open(sys.argv[2],"w",encoding="utf-8").write(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:(len(v) if isinstance(v,list) else v) for k,v in report.items()},ensure_ascii=False))
