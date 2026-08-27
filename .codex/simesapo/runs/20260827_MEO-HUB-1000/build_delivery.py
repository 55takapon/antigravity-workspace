import csv,json
from prepare_pool import dk
from verify_official import BASE,write
def read(n):return list(csv.DictReader((BASE/n).open(encoding='utf-8-sig',newline='')))
pre=read('candidate_pre_core.csv');lookup={dk(r['url']):r for r in pre};core=json.loads((BASE/'core_filter_result.json').read_text(encoding='utf-8'));rows=[]
for kept in core['kept']:
 if dk(kept['url']) not in lookup:continue
 r=dict(lookup[dk(kept['url'])]);r.update(company_name=kept['company_name'],url=kept['url'],status=kept.get('status') or 'MEOハブ候補');rows.append(r)
write(BASE/'delivery.csv',rows)
ex=read('recheck_registry.csv');seen={dk(r.get('url')) for r in ex}
for d in core['dropped']:
 domain=dk(d.get('url'))
 if domain in seen:continue
 r=dict(lookup[domain]);r.update(exclusion_scope='PERMANENT',reject_reason='001の営業不可判定により除外（2026-08-27確認）',review_status='EXCLUDED');ex.append(r);seen.add(domain)
write(BASE/'recheck_registry.csv',ex)
print(json.dumps({'delivery':len(rows),'manual':sum(r['status']=='手動送信要' for r in rows),'registry':len(ex),'permanent':sum(r.get('exclusion_scope')=='PERMANENT' for r in ex),'recheck':sum(r.get('exclusion_scope')=='RECHECK' for r in ex)}))
