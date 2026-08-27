import sys,json,csv,re,hashlib,unicodedata
from pathlib import Path
BASE=Path(__file__).parent
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
from prepare_pool import nk,dk,pk
from verify_official import write
def read(name):return list(csv.DictReader((BASE/name).open(encoding='utf-8-sig')))
def verified_address(r):
 address=r.get('address','')
 if not address:return ''
 def norm(s):return re.sub(r'[\s\-‐−ー〒]','',unicodedata.normalize('NFKC',s))
 urls=[r['url'],*r.get('evidence_urls','').split(' | ')]
 texts=[];cache=BASE.parent/'20260827_MEO-HUB-1000'/'official_cache'
 for u in list(dict.fromkeys(urls)):
  p=cache/(hashlib.sha256(u.encode()).hexdigest()+'.json')
  if not p.exists():continue
  page=json.loads(p.read_text(encoding='utf-8'));texts.append(page.get('identity_text',page.get('text','')))
  for l in page.get('links',[]):
   if dk(l['url'])==dk(r['url']) and re.search('会社概要|会社情報|company|about',l['label']+' '+l['url'],re.I):
    child=cache/(hashlib.sha256(l['url'].encode()).hexdigest()+'.json')
    if child.exists():
     data=json.loads(child.read_text(encoding='utf-8'));texts.append(data.get('identity_text',data.get('text','')))
 return address if any(norm(address) in norm(t) for t in texts) else ''
reviews={}
for p in [BASE/'semantic_review.json',*sorted(BASE.glob('semantic_review_batch*.json'))]:
 if p.exists():reviews.update(json.loads(p.read_text(encoding='utf-8')))
manual=json.loads((BASE/'manual_reviews.json').read_text(encoding='utf-8'))
policy=json.loads((BASE/'contact_policy_flags.json').read_text(encoding='utf-8')) if (BASE/'contact_policy_flags.json').exists() else {}
existing=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8'))
names={nk(r.get('company_name')) for r in existing};domains={dk(r.get('url')) for r in existing};phones={pk(r.get('phone')) for r in existing if len(pk(r.get('phone')))>=9}
accepted=[];excluded=[];pending=[];duplicates=[]
gate_path=BASE/'final_core_result.json'
gate=json.loads(gate_path.read_text(encoding='utf-8')) if gate_path.exists() else None
gate_kept={dk(r.get('url')):r for r in gate['kept']} if gate else {}
for r in read('verification_audit.csv'):
 d=dk(r['url']);review=reviews.get(d,{})
 if d in policy:
  excluded.append(dict(r,reject_reason=policy[d]['reason']+' '+policy[d]['evidence_url'],exclusion_scope='RECHECK'));continue
 if d in manual['holds'] or review.get('verdict')=='HOLD':
  excluded.append(dict(r,reject_reason=manual['holds'].get(d) or review.get('reason'),exclusion_scope='RECHECK'));continue
 if r.get('review_status')!='EVIDENCE_CHECKED':
  excluded.append(dict(r,exclusion_scope='RECHECK'));continue
 if review.get('verdict') not in ('ACCEPT','CORRECT_THEN_ACCEPT'):
  pending.append(r);continue
 correction=manual['corrections'].get(d,{})
 if review.get('verdict')=='CORRECT_THEN_ACCEPT':
  if review.get('company_name'):r['company_name']=review['company_name']
  r['hub_type']=review.get('hub_type','ADD_ON_HUB')
 if 'evidence_index' in correction:
  e=json.loads(r['evidence_detail'])[correction['evidence_index']]
  r['why_fit']='公式ページで「'+e['text']+'」を確認。既存支援にMEOを追加する提案候補。外注意向・採算は未確認。';r['evidence_urls']=e['url']
 for key in ['why_fit','evidence_urls']:
  if correction.get(key):r[key]=correction[key]
  elif review.get(key):r[key]=review[key]
 for key in ['contact_url','generic_email','phone']:
  if key in review:r[key]=review[key]
 if review.get('status')=='手動送信要':r['status']='手動送信要'
 if isinstance(r.get('evidence_urls'),list):r['evidence_urls']=' | '.join(r['evidence_urls'])
 if 'MEO' not in r['why_fit']:r['why_fit']+=' 既存支援へのMEO追加提案候補。外注意向・採算は未確認。'
 if review.get('verdict')=='CORRECT_THEN_ACCEPT' and not correction and not review.get('why_fit'):raise RuntimeError('Missing correction '+d)
 n,t=nk(r['company_name']),pk(r.get('phone'))
 if n in names or d in domains or (len(t)>=9 and t in phones):duplicates.append(r);continue
 if not (r.get('contact_url') or r.get('phone') or r.get('generic_email')):raise RuntimeError('Missing contact '+d)
 if gate is not None and d not in gate_kept:
  excluded.append(dict(r,reject_reason='最終照合で営業候補への追加を見送り。連絡条件・適合の再確認が必要。',exclusion_scope='RECHECK'));continue
 if gate is not None and gate_kept[d].get('status')=='手動送信要':r['status']='手動送信要'
 names.add(n);domains.add(d)
 if len(t)>=9:phones.add(t)
 r['risk_notes']='公開情報に基づく営業仮説。外注意向・再販可否・月額15,000円での採算・受注可能性は未確認。'+review.get('risk_notes','')
 r['address']=verified_address(r)
 accepted.append(r)
raw={}
for p in BASE.glob('*_raw.csv'):
 for r in csv.DictReader(p.open(encoding='utf-8-sig')):raw.setdefault(dk(r.get('url')),r)
for p in BASE.glob('*_core_*.json'):
 for r in json.loads(p.read_text(encoding='utf-8')).get('dropped',[]):
  d=dk(r.get('url'));source=raw.get(d,{})
  if r.get('reason') in ('dup','duplicate','partner'):continue
  if source.get('company_name'):excluded.append(dict(source,reject_reason='営業候補として追加不可。再利用前に連絡条件・対象適合を再確認（2026-08-27確認）',exclusion_scope='RECHECK'))
ad={dk(r['url']) for r in accepted};an={nk(r['company_name']) for r in accepted};ap={pk(r.get('phone')) for r in accepted if len(pk(r.get('phone')))>=9}
ex={}
for r in excluded:
 d=dk(r.get('url'));n=nk(r.get('company_name'));t=pk(r.get('phone'))
 if d in ad or n in an or (len(t)>=9 and t in ap):continue
 if not d or not n or not r.get('reject_reason'):continue
 if d not in ex or r.get('exclusion_scope')=='PERMANENT':ex[d]=r
accepted.sort(key=lambda r:(r.get('hub_type')!='OVERFLOW_HUB',r.get('recurring_relationship')!='signal_only',r.get('store_client_access')!='signal_only',not bool(re.search('Web|WEB|ホームページ|SNS',r.get('why_fit',''))),r['company_name']))
write(BASE/'qualified_candidates.csv',accepted);write(BASE/'delivery.csv',accepted[:832]);write(BASE/'review_pending.csv',pending);write(BASE/'recheck_registry.csv',list(ex.values()))
report={'qualified_new':len(accepted),'delivery_rows':min(len(accepted),832),'semantic_review_pending':len(pending),'duplicate_after_official_check':len(duplicates),'excluded_or_recheck':len(ex),'today_already_published':168,'goal_ready':len(accepted)>=832,'published_this_run':False}
(BASE/'pre_delivery_stats.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
