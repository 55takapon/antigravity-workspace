import csv,json,re,sys,unicodedata
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(r'C:\Users\hangy\.gemini\antigravity');RUN=Path(__file__).parent;DIST=ROOT/'.agent/skills/simesapo-sales-skills-dist';EF=DIST/'custmize/enterprise_filter'
sys.path[:0]=[str(DIST/'.codex_pydeps'),str(DIST/'shared')]
from sheets_io import get_client
def nn(s):
 s=unicodedata.normalize('NFKC',s or '').lower();s=re.sub(r'^(株式会社|有限会社|合同会社|合資会社)','',s);s=re.sub(r'(株式会社|有限会社|合同会社|合資会社)$','',s);return re.sub(r'[^0-9a-z\u3040-\u30ff\u3400-\u9fff]+','',s)
def dom(u):
 if '://' not in (u or ''):u='https://'+(u or '')
 h=(urlparse(u).hostname or '').lower().strip('.');return h[4:] if h.startswith('www.') else h
rows=list(csv.DictReader((RUN/'job_signal_30.data').open(encoding='utf-8-sig')))
book=get_client(str(DIST/'shared/gcp_service_account.json')).open_by_key('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ');targets={'シート1','Webマーケ','SNS運用','送信済み251127','送信済み251222','Web幹事済み','シート2','除外リスト'};names=set();domains=set()
for ws in [w for w in book.worksheets() if w.title in targets]:
 vals=ws.get_all_values()
 if not vals:continue
 heads=[unicodedata.normalize('NFKC',x).strip().lower() for x in vals[0]];ci=heads.index('company_name') if 'company_name' in heads else None;ui=heads.index('url') if 'url' in heads else None
 if ci is None:continue
 for x in vals[1:]:
  if ci<len(x) and x[ci]:names.add(nn(x[ci]))
  if ui is not None and ui<len(x) and dom(x[ui]):domains.add(dom(x[ui]))
jpx={r['normalized_company_name'] for r in csv.DictReader((EF/'jpx_listed_companies_20260630.csv').open(encoding='utf-8-sig'))};rules=[r for r in csv.DictReader((EF/'major_group_rules.csv').open(encoding='utf-8-sig')) if r['match_type']=='company_contains']
competitors={'株式会社PARLAY','株式会社クオンタム','株式会社トリニアス'}
for r in rows:
 k=nn(r['company_name']);d=dom(r['url']);reasons=[]
 if k in names or d in domains:reasons.append('既存または除外リスト一致')
 if k in jpx:reasons.append('JPX会社名完全一致')
 if any(q['normalized_value'] and q['normalized_value'].lower() in k for q in rules):reasons.append('大手管理語')
 if r['company_name'] in competitors:reasons.append('GBP・MEOを主力提供する直接競合')
 r.update(normalized_name=k,normalized_domain=d,prefilter='exclude' if reasons else 'pass',prefilter_reason=' / '.join(reasons))
with (RUN/'job30_prefiltered.data').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
rep={'total':len(rows),'pass':sum(r['prefilter']=='pass' for r in rows),'exclude':sum(r['prefilter']=='exclude' for r in rows)};print(json.dumps(rep,ensure_ascii=False));[print(r['prefilter'],r['company_name'],r['prefilter_reason']) for r in rows]
