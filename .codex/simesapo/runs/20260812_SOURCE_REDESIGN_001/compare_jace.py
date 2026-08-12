import csv,json,re,sys,unicodedata
from pathlib import Path
ROOT=Path(r'C:\Users\hangy\.gemini\antigravity');RUN=Path(__file__).parent;DIST=ROOT/'.agent/skills/simesapo-sales-skills-dist';EF=DIST/'custmize/enterprise_filter'
sys.path.insert(0,r'C:\Users\hangy\.cache\codex-runtimes\codex-primary-runtime\dependencies\python')
import pdfplumber
def nn(s):
 s=unicodedata.normalize('NFKC',s or '').lower();s=re.sub(r'^(株式会社|有限会社|合同会社|合資会社|一般社団法人|公益社団法人)','',s);s=re.sub(r'(株式会社|有限会社|合同会社|合資会社)$','',s);return re.sub(r'[^0-9a-z\u3040-\u30ff\u3400-\u9fff]+','',s)
page=pdfplumber.open(RUN/'jace_members.pdf').pages[0]
text='\n'.join([(page.crop((0,0,page.width/2,page.height)).extract_text() or ''),(page.crop((page.width/2,0,page.width,page.height)).extract_text() or '')])
names=[]
for line in text.splitlines():
 if line.startswith('正会員 '):
  p=re.sub(r'^正会員\s+','',line);p=re.sub(r'\s+(?:正|準|賛助)$','',p).strip()
  if p and p not in names:names.append(p)
# Known PDF layout may leave the second column attached to a trailing marker; retain only corporate-looking names.
names=[re.sub(r'\s+$','',n) for n in names if ('株式会社' in n or '合同会社' in n or n.endswith('inc.'))]
seen=set();names=[n for n in names if not (nn(n) in seen or seen.add(nn(n)))]
sys.path[:0]=[str(DIST/'.codex_pydeps'),str(DIST/'shared')]
from sheets_io import get_client
book=get_client(str(DIST/'shared/gcp_service_account.json')).open_by_key('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ');targets={'シート1','Webマーケ','SNS運用','送信済み251127','送信済み251222','Web幹事済み','シート2','除外リスト'};existing=set()
for ws in [w for w in book.worksheets() if w.title in targets]:
 vals=ws.get_all_values()
 if not vals:continue
 heads=[unicodedata.normalize('NFKC',x).strip().lower() for x in vals[0]];ci=heads.index('company_name') if 'company_name' in heads else None
 if ci is not None:
  existing.update(nn(x[ci]) for x in vals[1:] if ci<len(x) and x[ci])
jpx={r['normalized_company_name'] for r in csv.DictReader((EF/'jpx_listed_companies_20260630.csv').open(encoding='utf-8-sig'))};rules=[r for r in csv.DictReader((EF/'major_group_rules.csv').open(encoding='utf-8-sig')) if r['match_type']=='company_contains']
rows=[]
for n in names:
 k=nn(n);reasons=[]
 if k in existing:reasons.append('existing')
 if k in jpx:reasons.append('jpx')
 if any(q['normalized_value'] and q['normalized_value'].lower() in k for q in rules):reasons.append('major_keyword')
 rows.append({'company_name':n,'normalized_name':k,'reason':' / '.join(reasons),'pass':not reasons})
with (RUN/'jace_prefiltered.data').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
rep={'JACE_extracted_corporate':len(rows),'existing':sum('existing' in r['reason'] for r in rows),'jpx_or_major':sum(('jpx' in r['reason'] or 'major_keyword' in r['reason']) for r in rows),'raw_pass':sum(r['pass'] for r in rows)};print(json.dumps(rep,ensure_ascii=False,indent=2));print('PASS');[print(r['company_name']) for r in rows if r['pass']]
