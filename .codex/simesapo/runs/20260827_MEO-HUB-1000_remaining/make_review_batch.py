import sys,json,csv,argparse
from pathlib import Path
BASE=Path(__file__).parent
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
from prepare_pool import dk
from verify_official import write
ap=argparse.ArgumentParser();ap.add_argument('batch');a=ap.parse_args()
seen=set()
for p in [BASE/'semantic_review.json',*BASE.glob('semantic_review_batch*.json')]:
 if p.exists():seen.update(json.loads(p.read_text(encoding='utf-8')))
for p in BASE.glob('review_batch_*.csv'):
 seen.update(dk(r['url']) for r in csv.DictReader(p.open(encoding='utf-8-sig')))
rows=[r for r in csv.DictReader((BASE/'verification_audit.csv').open(encoding='utf-8-sig')) if r.get('review_status')=='EVIDENCE_CHECKED' and r.get('evidence_detail') and r.get('last_verified_at') and dk(r['url']) not in seen]
out=BASE/f'review_batch_{a.batch}.csv'
if out.exists():raise SystemExit('do not overwrite a review snapshot')
write(out,rows[:200]);print('review_batch',a.batch,'rows',len(rows[:200]))
