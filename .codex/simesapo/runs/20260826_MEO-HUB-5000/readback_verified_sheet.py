import json,re,sys
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist");sys.path.insert(0,str(ROOT/"shared"));import sheets_io
sheet,worksheet,output,baseline=sys.argv[1:5]
ws=sheets_io.open_worksheet(sheet,worksheet); values=ws.get("A1:L6001"); header=values[0]; rows=[]
for vals in values[1:]:
 vals=vals+[""]*(len(header)-len(vals));rows.append(dict(zip(header,vals)))
Path(output).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
def nk(v):return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]","",(v or "").lower())
def dk(v):
 h=urlparse(v or "").netloc.lower().split(":")[0];return h[4:] if h.startswith("www.") else h
def pk(v):return re.sub(r"\D","",v or "")
def dup(vals):
 seen=set();d=set()
 for v in vals:
  if not v:continue
  if v in seen:d.add(v)
  seen.add(v)
 return d
base=json.loads(Path(baseline).read_text(encoding="utf-8-sig"))
first_unchanged=len(base)==5000 and all(nk(a.get("company_name"))==nk(b.get("company_name")) and dk(a.get("url"))==dk(b.get("url")) for a,b in zip(rows[:5000],base))
last=rows[5000:]
report={"rows":len(rows),"first_5000_unchanged":first_unchanged,"blank_company_name":sum(not r.get("company_name") for r in rows),"blank_url":sum(not r.get("url") for r in rows),"duplicate_names":len(dup([nk(r.get("company_name")) for r in rows])),"duplicate_domains":len(dup([dk(r.get("url")) for r in rows])),"duplicate_phones":len(dup([pk(r.get("phone")) if len(pk(r.get("phone")))>=9 else "" for r in rows])),"last_1000":len(last),"last_blank_why_fit":sum(not r.get("why_fit") for r in last),"last_blank_evidence_urls":sum(not r.get("evidence_urls") for r in last),"last_not_verified":sum(r.get("review_status")!="VERIFIED" for r in last)}
print(json.dumps(report,ensure_ascii=False))
