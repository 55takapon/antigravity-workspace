import csv,json
from pathlib import Path
from prepare_pool import nk,dk,pk
from verify_official import write,BASE,HOLDS
def read(name):return list(csv.DictReader((BASE/name).open(encoding='utf-8-sig',newline='')))
existing=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8-sig'))
names={nk(r.get('company_name')) for r in existing};domains={dk(r.get('url')) for r in existing};phones={pk(r.get('phone')) for r in existing if len(pk(r.get('phone')))>=9}
manual=json.loads((BASE/'manual_reviews.json').read_text(encoding='utf-8'));holds={**HOLDS,**manual['holds']}
rows=read('strict_pool_audit.csv')+read('stream_audit.csv');rows.sort(key=lambda r:(r.get('review_status')!='EVIDENCE_CHECKED',r.get('company_name','')))
accepted=[];recheck=[];seen_n=set();seen_d=set();seen_p=set();stats={'input_rows':len(rows),'existing_or_duplicate':0,'recheck':0,'accepted':0}
for r in rows:
 if dk(r.get('url')) in manual.get('company_names',{}):r['company_name']=manual['company_names'][dk(r.get('url'))]
 n,d,p=nk(r.get('company_name')),dk(r.get('url')),pk(r.get('phone'))
 if not n or not d:continue
 if n in names or d in domains or (len(p)>=9 and p in phones) or n in seen_n or d in seen_d or (len(p)>=9 and p in seen_p):stats['existing_or_duplicate']+=1;continue
 seen_n.add(n);seen_d.add(d)
 if len(p)>=9:seen_p.add(p)
 if d in holds:r.update(review_status='RECHECK',reject_reason=holds[d])
 if r['review_status']!='EVIDENCE_CHECKED':
  r['exclusion_scope']='RECHECK';r['reject_reason']=r.get('reject_reason') or '要再確認';recheck.append(r);continue
 if d in manual['evidence_index']:
  e=json.loads(r['evidence_detail'])[manual['evidence_index'][d]];r['why_fit']='公式会社概要で「'+e['text']+'」を確認。MEO追加提案候補（外注意向・採算は未確認）。';r['evidence_urls']=e['url']
 if d in manual.get('why_fit',{}):r['why_fit']=manual['why_fit'][d]
 r['risk_notes']='営業候補としての仮説。店舗顧客との商流、外注意向、1店舗月額15,000円での採算は商談確認が必要。'
 r.pop('contact_form_url',None)
 accepted.append(r)
stats.update(accepted=len(accepted),recheck=len(recheck));write(BASE/'candidate_pre_core.csv',accepted);write(BASE/'recheck_registry.csv',recheck)
(BASE/'pre_delivery_stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(stats,ensure_ascii=False))
