import argparse,csv,re,sys
from pathlib import Path

ROOT=Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist")
sys.path.insert(0,str(ROOT/"shared"));import sheets_io

ap=argparse.ArgumentParser();ap.add_argument("sheet");ap.add_argument("csv");ap.add_argument("--worksheet",default="MEOハブ候補");ap.add_argument("--expected-current",default="");ap.add_argument("--apply",action="store_true");a=ap.parse_args()
rows=list(csv.DictReader(open(a.csv,encoding="utf-8-sig",newline="")))
if len(rows)!=1000:raise SystemExit(f"expected 1000 rows, got {len(rows)}")
ws=sheets_io.open_worksheet(a.sheet,a.worksheet)
current=ws.get("A5002:F6001")
expected_path=Path(a.expected_current) if a.expected_current else Path(a.csv).parent/"daily_append_1000_ready.csv"
expected_old=list(csv.DictReader(open(expected_path,encoding="utf-8-sig",newline="")))
if len(expected_old)!=1000:raise SystemExit(f"expected-current rows={len(expected_old)}")
def norm(v):return re.sub(r"\s+","",(v or "").strip().lower()).rstrip("/")
if len(current)!=1000:raise SystemExit(f"current block rows={len(current)}")
for i,(cur,old) in enumerate(zip(current,expected_old),5002):
    cur=cur+[""]*(6-len(cur))
    if norm(cur[0])!=norm(old.get("company_name")) or norm(cur[1])!=norm(old.get("url")):raise SystemExit(f"current block mismatch row={i}")
fields=["company_name","url","address","phone","maps_url","status","hub_type","why_fit","evidence_urls","confidence","review_status","last_verified_at"]
print(f"verified_current_block=1000 replacement_block=1000 apply={a.apply}")
if not a.apply:raise SystemExit(0)
if ws.col_count < 12: ws.add_cols(12-ws.col_count)
ws.update(range_name="G1:L1",values=[fields[6:]],value_input_option="RAW")
matrix=[[r.get(f,"") for f in fields] for r in rows]
for start in range(0,1000,200):
    r1=5002+start;r2=r1+len(matrix[start:start+200])-1
    ws.update(range_name=f"A{r1}:L{r2}",values=matrix[start:start+200],value_input_option="RAW")
back=ws.get("A5002:L6001")
if len(back)!=1000:raise SystemExit(f"readback rows={len(back)}")
for i,(got,want) in enumerate(zip(back,matrix),5002):
    got=got+[""]*(12-len(got))
    if got!=want:raise SystemExit(f"readback mismatch row={i}")
print("written=1000 readback_verified=1000")
