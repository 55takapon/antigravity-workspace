import argparse, csv, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HELPERS = Path(__file__).resolve().parents[1] / "20260805_next300"
sys.path.insert(0, str(HELPERS))
from collect_aca import discover

p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--output",required=True); a=p.parse_args()
with open(a.input,encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
with ThreadPoolExecutor(max_workers=10) as pool: checked=list(pool.map(discover,rows))
accepted=[r for r in checked if r.get("company_confirmed")=="yes" and r.get("contact_url")]
fields=["company_name","url","address","phone","contact_url","区分","検出ワード","source_url"]
with open(a.output,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(accepted)
print({"input":len(rows),"company_confirmed":sum(r.get('company_confirmed')=='yes' for r in checked),"accepted":len(accepted),"output":a.output})
