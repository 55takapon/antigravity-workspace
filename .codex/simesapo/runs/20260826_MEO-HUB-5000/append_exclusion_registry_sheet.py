import argparse,csv,re,sys
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist");sys.path.insert(0,str(ROOT/"shared"));import sheets_io
ap=argparse.ArgumentParser();ap.add_argument("sheet");ap.add_argument("registry");ap.add_argument("--apply",action="store_true");a=ap.parse_args()
def nk(v):return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]","",(v or "").lower())
def dk(v):
 h=urlparse(v or "").netloc.lower().split(":")[0];return h[4:] if h.startswith("www.") else h
def pk(v):return re.sub(r"\D","",v or "")
ws=sheets_io.open_worksheet(a.sheet,"除外リスト");header=ws.row_values(1)[:12];values=ws.get(f"A2:L{ws.row_count}");existing=[dict(zip(header,row+[""]*(len(header)-len(row)))) for row in values]
names={nk(r.get("company_name")) for r in existing if r.get("company_name")};domains={dk(r.get("url")) for r in existing if dk(r.get("url"))};phones={pk(r.get("phone")) for r in existing if len(pk(r.get("phone")))>=9}
source=list(csv.DictReader(open(a.registry,encoding="utf-8-sig",newline="")));new=[]
for r in source:
 n,d,p=nk(r.get("company_name")),dk(r.get("url")),pk(r.get("phone"))
 if n in names or d in domains or (len(p)>=9 and p in phones):continue
 names.add(n);domains.add(d)
 if len(p)>=9:phones.add(p)
 item={k:"" for k in header};item.update({"company_name":r.get("company_name"),"url":r.get("url"),"phone":r.get("phone"),"status":"恒久除外" if r.get("exclusion_scope")=="PERMANENT" else "要再確認","error_reason":r.get("reject_reason"),"provider_used":"MEOハブ再審査 2026-08-26"});new.append(item)
print(f"registry={len(source)} append={len(new)} skip_existing={len(source)-len(new)} apply={a.apply}")
if not a.apply:raise SystemExit(0)
matrix=[[r.get(h,"") for h in header] for r in new]
for i in range(0,len(matrix),200):ws.append_rows(matrix[i:i+200],value_input_option="RAW")
values=ws.get(f"A2:L{ws.row_count}");after=[dict(zip(header,row+[""]*(len(header)-len(row)))) for row in values];after_names={nk(r.get("company_name")) for r in after};missing=[r["company_name"] for r in new if nk(r["company_name"]) not in after_names]
if missing:raise SystemExit(f"readback missing={len(missing)}")
print(f"appended={len(new)} readback_verified={len(new)} total_exclusion_rows={len(after)}")
