import csv,re,sys
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist");sys.path.insert(0,str(ROOT/"shared"));import sheets_io
sheet,registry=sys.argv[1:3]
def nk(v):return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]","",(v or "").lower())
def dk(v):
 h=urlparse(v or "").netloc.lower().split(":")[0];return h[4:] if h.startswith("www.") else h
ws=sheets_io.open_worksheet(sheet,"除外リスト");header=ws.row_values(1)[:12];last=max(i for i,v in enumerate(ws.col_values(1),1) if v.strip());vals=ws.get(f"A2:L{last}");live=[dict(zip(header,r+[""]*(12-len(r)))) for r in vals]
mine=[r for r in live if (r.get("provider_used") or "").startswith("MEOハブ再審査")]
reg=list(csv.DictReader(open(registry,encoding="utf-8-sig",newline="")))
live_names={nk(r.get("company_name")) for r in mine};live_domains={dk(r.get("url")) for r in mine}
missing=[r.get("company_name") for r in reg if nk(r.get("company_name")) not in live_names and dk(r.get("url")) not in live_domains]
outside=[]
for c in range(13,ws.col_count+1):
 for i,v in enumerate(ws.col_values(c)[1:],2):
  if str(v).strip().startswith("MEOハブ再審査"):outside.append((i,c))
print({"last_row":last,"registry":len(reg),"live_meo_exclusions":len(mine),"missing":len(missing),"blank_company":sum(not r.get("company_name") for r in mine),"blank_reason":sum(not r.get("error_reason") for r in mine),"permanent":sum(r.get("status")=="恒久除外" for r in mine),"recheck":sum(r.get("status")=="要再確認" for r in mine),"markers_outside_A_L":len(outside)})
if missing or outside:raise SystemExit(1)
