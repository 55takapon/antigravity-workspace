from __future__ import annotations

import argparse, csv, re, sys, unicodedata
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'.agent/skills/simesapo-sales-skills-dist/shared'))
import sheets_io

SHEET='https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing'
SEED=Path(__file__).parent/'batch1_strict_v6_seed.csv'
BLOCKED={'gamo.co.jp','gamo-w.jp','kikuya-bisyodo.co.jp','senbi-beauty.com'}

def domain(v):
    h=(urlparse(v if '://' in v else 'https://'+v).hostname or '').lower()
    return re.sub(r'^www\.','',h)
def norm(v):
    v=unicodedata.normalize('NFKC',v or '').lower()
    v=re.sub(r'株式会社|有限会社|合同会社|\(株\)|\(有\)','',v)
    return re.sub(r'[\s\u3000・･.,，．_\-–—/()（）]+','',v)

rows=list(csv.DictReader(SEED.open(encoding='utf-8-sig')))
targets=[]
for r in rows:
    d=domain(r['url'])
    if not r.get('区分','').startswith('A｜美容室・サロン向け経営・販促支援'):
        continue
    if d in BLOCKED:
        reason='enterprise_or_large_group:大手美容ディーラーとして除外確定 | checked:2026-08-07 | source:次期高親和性監査'
        category='除外確定（大手・規模不適合）'
    else:
        reason='partnership_mismatch:研修・商材供給・経営支援が中心で、当方へのGBP案件紹介・外注導線を確認できない | checked:2026-08-07 | source:次期高親和性監査'
        category='除外確定（提携導線なし）'
    targets.append([r['company_name'],r['url'],'','', '',r.get('contact_url',''),'','', 'excluded',reason,'','',category])

ap=argparse.ArgumentParser(); ap.add_argument('--apply',action='store_true'); args=ap.parse_args()
ws=sheets_io.open_worksheet(SHEET,'除外リスト')
values=ws.get_all_values(); header=values[0]
expected=['company_name','url','address','phone','maps_url','contact_url','message','sent_at','status','error_reason','screenshot_path','provider_used','提案区分']
if header[:13]!=expected: raise RuntimeError('除外リストのヘッダー不一致')
existing_names={norm(r[0]) for r in values[1:] if r and r[0].strip()}
existing_domains={domain(r[1]) for r in values[1:] if len(r)>1 and r[1].strip()}
pending=[r for r in targets if norm(r[0]) not in existing_names and domain(r[1]) not in existing_domains]
print({'targets':len(targets),'existing_skipped':len(targets)-len(pending),'pending':len(pending),'apply':args.apply})
for r in pending: print(r[0],domain(r[1]),r[12])
if not args.apply: raise SystemExit(0)
if pending: ws.append_rows(pending,value_input_option='RAW')
after=ws.get_all_values(); after_names={norm(r[0]) for r in after[1:] if r and r[0].strip()}; after_domains={domain(r[1]) for r in after[1:] if len(r)>1 and r[1].strip()}
missing=[r[0] for r in pending if norm(r[0]) not in after_names and domain(r[1]) not in after_domains]
if missing: raise RuntimeError(f'除外リスト読み戻し不一致:{missing}')
print({'written':len(pending),'verified':len(pending)-len(missing),'final_data_rows':len(after)-1})
