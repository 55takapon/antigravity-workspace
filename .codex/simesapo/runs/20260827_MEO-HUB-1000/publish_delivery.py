import argparse,csv,json,sys
from pathlib import Path
from prepare_pool import nk,dk,pk
ROOT=Path(r'C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist');sys.path.insert(0,str(ROOT/'shared'));import sheets_io
BASE=Path(__file__).parent;SHEET='1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
FIELDS=['company_name','url','address','phone','maps_url','status','hub_type','why_fit','evidence_urls','confidence','review_status','last_verified_at','contact_url','generic_email','risk_notes']
def pad(r,n):return r+['']*(n-len(r))
def load(name):return list(csv.DictReader((BASE/name).open(encoding='utf-8-sig',newline='')))
ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');a=ap.parse_args()
rows=load('delivery.csv');ex=load('recheck_registry.csv')
if not 0<len(rows)<=1000:raise SystemExit('candidate count outside requested upper limit')
ws=sheets_io.open_worksheet(SHEET,'MEOハブ候補');before=ws.get_all_values();base=json.loads((BASE/'target_before.json').read_text(encoding='utf-8'))
if before!=base:raise SystemExit('target changed since snapshot; refresh before applying')
if len(before)!=6001:raise SystemExit('expected 6000 existing companies')
if before[0]!=FIELDS[:12]:raise SystemExit('unexpected target header')
matrix=[[r.get(f,'') for f in FIELDS] for r in rows]
if any(not r.get('company_name') or not r.get('url') or not r.get('why_fit') or not r.get('evidence_urls') or r.get('review_status')!='EVIDENCE_CHECKED' for r in rows):raise SystemExit('candidate completeness failed')
live=[]
for tab in ('シート1','Webマーケ','MEO業者','SNS運用','除外リスト','251127作成','251222作成','Web幹事','シート2','MEOハブ候補'):
 tw=sheets_io.open_worksheet(SHEET,tab);live.extend(sheets_io.read_rows(tw,want=['company_name','url','phone'],aliases={'phone':['連絡先','電話番号']}))
names={nk(r.get('company_name')) for r in live};domains={dk(r.get('url')) for r in live};phones={pk(r.get('phone')) for r in live if len(pk(r.get('phone')))>=9}
for r in rows:
 n,d,p=nk(r.get('company_name')),dk(r.get('url')),pk(r.get('phone'))
 if n in names or d in domains or (len(p)>=9 and p in phones):raise SystemExit('existing or duplicate candidate: '+r['company_name'])
 names.add(n);domains.add(d)
 if len(p)>=9:phones.add(p)
ew=sheets_io.open_worksheet(SHEET,'除外リスト');ebefore=ew.get_all_values();eh=ebefore[0][:12];erows=[dict(zip(eh,pad(r[:12],12))) for r in ebefore[1:]]
if ebefore!=json.loads((BASE/'exclusions_before.json').read_text(encoding='utf-8')):raise SystemExit('exclusion sheet changed since snapshot')
if not {'company_name','url','phone','status','error_reason','provider_used'}.issubset(eh):raise SystemExit('exclusion headers missing')
ens={nk(r.get('company_name')) for r in erows};eds={dk(r.get('url')) for r in erows};eps={pk(r.get('phone')) for r in erows if len(pk(r.get('phone')))>=9};em=[]
for r in ex:
 n,d,p=nk(r.get('company_name')),dk(r.get('url')),pk(r.get('phone'))
 if not n or not d or n in ens or d in eds or (len(p)>=9 and p in eps):continue
 if n in {nk(x['company_name']) for x in rows} or d in {dk(x['url']) for x in rows} or (len(p)>=9 and p in {pk(x.get('phone')) for x in rows}):raise SystemExit('exclusion overlaps candidate')
 ens.add(n);eds.add(d)
 if len(p)>=9:eps.add(p)
 item={'company_name':r['company_name'],'url':r['url'],'phone':r.get('phone',''),'status':'要再確認','error_reason':r.get('reject_reason') or '公式根拠確認不足','provider_used':'MEOハブ収集 2026-08-27'}
 em.append([item.get(h,'') for h in eh])
print(json.dumps({'append_candidates':len(rows),'requested':1000,'target_met':len(rows)==1000,'current_candidates':len(before)-1,'append_recheck':len(em),'apply':a.apply}),flush=True)
if not a.apply:raise SystemExit(0)
start=len(before)+1;end=start+len(rows)-1
es=max(i for i,r in enumerate(ebefore,1) if r and r[0].strip())+1;ee=es+len(em)-1
journal={'candidate_range':f'A{start}:O{end}','exclusion_range':f'A{es}:L{ee}','candidate_rows':matrix,'exclusion_rows':em,'phase':'preflight','target_met':len(rows)==1000}
def checkpoint(phase):
 journal['phase']=phase;(BASE/'publication_journal.json').write_text(json.dumps(journal,ensure_ascii=False),encoding='utf-8')
checkpoint('preflight')
if ws.col_count<len(FIELDS):ws.add_cols(len(FIELDS)-ws.col_count)
if ws.row_count<len(before)+len(rows):ws.add_rows(len(before)+len(rows)-ws.row_count)
if em and ew.row_count<ee:ew.add_rows(ee-ew.row_count)
if any(any(str(c).strip() for c in r) for r in ws.get(f'A{start}:O{end}')):raise SystemExit('append range not blank')
if em and any(any(str(c).strip() for c in r) for r in ew.get(f'A{es}:L{ee}')):raise SystemExit('exclusion range not blank')
checkpoint('both_ranges_checked')
ws.update(range_name='M1:O1',values=[FIELDS[12:]],value_input_option='RAW')
for i in range(0,len(matrix),100):ws.update(range_name=f'A{start+i}:O{start+i+len(matrix[i:i+100])-1}',values=matrix[i:i+100],value_input_option='RAW')
back=ws.get_all_values()
if len(back)!=len(before)+len(rows):raise SystemExit('target row count mismatch')
if any(pad(g[:12],12)!=pad(w[:12],12) for g,w in zip(back[1:len(before)],before[1:])):raise SystemExit('old rows changed')
if [pad(r,15) for r in back[len(before):]]!=matrix:raise SystemExit('candidate readback mismatch')
(BASE/'target_after.json').write_text(json.dumps(back,ensure_ascii=False),encoding='utf-8')
checkpoint('candidate_readback_complete')
if em:
 if ew.row_count<ee:ew.add_rows(ee-ew.row_count)
 if any(any(str(c).strip() for c in r) for r in ew.get(f'A{es}:L{ee}')):raise SystemExit('exclusion range not blank')
 for i in range(0,len(em),100):ew.update(range_name=f'A{es+i}:L{es+i+len(em[i:i+100])-1}',values=em[i:i+100],value_input_option='RAW')
 if [pad(r,12) for r in ew.get(f'A{es}:L{ee}')]!=em:raise SystemExit('exclusion readback mismatch')
checkpoint('all_readbacks_complete')
report={'added':len(rows),'requested':1000,'target_met':len(rows)==1000,'status':'TARGET_MET' if len(rows)==1000 else 'PARTIAL_TARGET_NOT_MET','total':len(back)-1,'existing_rows_unchanged':True,'candidate_readback_exact':True,'recheck_added':len(em),'exclusion_readback_exact':True,'start_row':start,'end_row':end,'exclusion_start':es,'exclusion_end':ee}
(BASE/'publication_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
