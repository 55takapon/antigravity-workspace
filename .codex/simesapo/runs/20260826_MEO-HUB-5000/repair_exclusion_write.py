import csv,sys
from pathlib import Path
ROOT=Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist");sys.path.insert(0,str(ROOT/"shared"));import sheets_io
sheet,registry=sys.argv[1:3];ws=sheets_io.open_worksheet(sheet,"除外リスト");header=ws.row_values(1)[:12];source=list(csv.DictReader(open(registry,encoding="utf-8-sig",newline="")))
matrix=[]
for r in source:
 item={k:"" for k in header};item.update({"company_name":r.get("company_name"),"url":r.get("url"),"phone":r.get("phone"),"status":"恒久除外" if r.get("exclusion_scope")=="PERMANENT" else "要再確認","error_reason":r.get("reject_reason"),"provider_used":"MEOハブ再審査 2026-08-26"});matrix.append([item.get(h,"") for h in header])
if len(matrix)!=595:raise SystemExit(f"registry={len(matrix)}")
dest=ws.get("A3431:L4025")
if any(any(str(x).strip() for x in row) for row in dest):raise SystemExit("destination not blank")
ws.update(range_name="A3431:L4025",values=matrix,value_input_option="RAW")
ws.batch_clear(["AC3431:AN3630","AN3631:AY3830","AY3831:BJ4025"])
correct=ws.get("A3431:L4025");allv=ws.get_all_values();wrong=sum(1 for row in allv for val in row[12:] if val=="MEOハブ再審査 2026-08-26")
if len(correct)!=595 or wrong:raise SystemExit(f"readback correct={len(correct)} wrong_markers={wrong}")
print("moved=595 cleared_wrong_cells=7140 readback_verified=595 wrong_markers=0")
