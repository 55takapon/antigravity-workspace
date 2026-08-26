import argparse,csv,re,sys
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist")
sys.path.insert(0,str(ROOT/"shared"));import sheets_io
ap=argparse.ArgumentParser();ap.add_argument("sheet");ap.add_argument("registry");ap.add_argument("--apply",action="store_true");a=ap.parse_args()
def nk(v):return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]","",(v or "").lower())
def dk(v):
 h=urlparse(v or "").netloc.lower().split(":")[0];return h[4:] if h.startswith("www.") else h
def pk(v):return re.sub(r"\D","",v or "")
ws=sheets_io.open_worksheet(a.sheet,"除外リスト");header=ws.row_values(1)[:12]
if len(header)!=12:raise SystemExit(f"unexpected header columns={len(header)}")
col_a=ws.col_values(1);last=max((i for i,v in enumerate(col_a,1) if v.strip()),default=1)
values=ws.get(f"A2:L{last}");existing=[dict(zip(header,row+[""]*(12-len(row)))) for row in values]
names={nk(r.get("company_name")) for r in existing if r.get("company_name")};domains={dk(r.get("url")) for r in existing if dk(r.get("url"))};phones={pk(r.get("phone")) for r in existing if len(pk(r.get("phone")))>=9}
source=list(csv.DictReader(open(a.registry,encoding="utf-8-sig",newline="")));new=[]
for r in source:
 n,d,p=nk(r.get("company_name")),dk(r.get("url")),pk(r.get("phone"))
 if n in names or d in domains or (len(p)>=9 and p in phones):continue
 names.add(n);domains.add(d)
 if len(p)>=9:phones.add(p)
 item={k:"" for k in header};item.update({"company_name":r.get("company_name"),"url":r.get("url"),"phone":r.get("phone"),"status":"恒久除外" if r.get("exclusion_scope")=="PERMANENT" else "要再確認","error_reason":r.get("reject_reason"),"provider_used":"MEOハブ再審査2 2026-08-26"});new.append(item)
start=last+1;end=start+len(new)-1
print(f"registry={len(source)} write={len(new)} skip_existing={len(source)-len(new)} exact_range=A{start}:L{end} apply={a.apply}")
if not a.apply or not new:raise SystemExit(0)
if ws.row_count < end:ws.add_rows(end-ws.row_count)
probe=ws.get(f"A{start}:L{end}")
if any(any(str(c).strip() for c in row) for row in probe):raise SystemExit("target range is not blank")
matrix=[[r.get(h,"") for h in header] for r in new]
for i in range(0,len(matrix),200):
 r1=start+i;r2=r1+len(matrix[i:i+200])-1;ws.update(range_name=f"A{r1}:L{r2}",values=matrix[i:i+200],value_input_option="RAW")
back=ws.get(f"A{start}:L{end}")
for i,(got,want) in enumerate(zip(back,matrix),start):
 got=got+[""]*(12-len(got))
 if got!=want:raise SystemExit(f"readback mismatch row={i}")
print(f"written={len(new)} readback_verified={len(new)}")
