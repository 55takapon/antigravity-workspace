import json
from pathlib import Path
BASE=Path(__file__).parent
batch=json.loads((BASE/'full_batch.json').read_text(encoding='utf-8'))
results=[];last=1
for row in batch:
    path=BASE/'contact_checks'/(str(row['_row'])+'.json')
    if not path.exists():break
    check=json.loads(path.read_text(encoding='utf-8'))
    if check.get('qa_version')!='contact-purpose-v5':break
    assert check['idx']==row['idx']
    results.append({'idx':row['idx'],'method':'link' if check['contact_url'] else 'none','contact_url':check['contact_url']})
    last=row['_row']
(BASE/'top_prefix_results.json').write_text(json.dumps({'results':results},ensure_ascii=False),encoding='utf-8')
print(json.dumps({'checked_prefix_rows':len(results),'last_sheet_row':last,'found':sum(bool(r['contact_url']) for r in results)}))
