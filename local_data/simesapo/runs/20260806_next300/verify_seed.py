from __future__ import annotations
import argparse,csv,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
HELPERS=Path(__file__).resolve().parents[1]/"20260805_next300"
sys.path.insert(0,str(HELPERS))
from collect_aca import discover
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args()
with Path(a.input).open(encoding='utf-8-sig',newline='') as h: source=list(csv.DictReader(h))
rows=[]
with ThreadPoolExecutor(max_workers=8) as pool:
    futures=[pool.submit(discover,row) for row in source]
    for future in as_completed(futures): rows.append(future.result())
rows.sort(key=lambda r:r['company_name'])
with Path(a.output).open('w',encoding='utf-8-sig',newline='') as h:
    w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print({'input':len(source),'contact_found':sum(bool(r['contact_url'].strip()) for r in rows),'company_confirmed':sum(r['company_confirmed']=='yes' for r in rows),'output':a.output})
