import csv,json,re,sys,unicodedata
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(r'C:\Users\hangy\.gemini\antigravity');RUN=Path(__file__).parent;DIST=ROOT/'.agent/skills/simesapo-sales-skills-dist';EF=DIST/'custmize/enterprise_filter';sys.path[:0]=[str(DIST/'.codex_pydeps'),str(DIST/'shared')]
from sheets_io import get_client
def nn(s):
 s=unicodedata.normalize('NFKC',s or '').lower().replace('(株)','株式会社');s=re.sub(r'^(株式会社|有限会社|合同会社|合資会社|一般社団法人|公益社団法人)','',s);s=re.sub(r'(株式会社|有限会社|合同会社|合資会社)$','',s);return re.sub(r'[^0-9a-z\u3040-\u30ff\u3400-\u9fff]+','',s)
def dom(u):
 if not u:return ''
 if '://' not in u:u='https://'+u
 h=(urlparse(u).hostname or '').lower().strip('.');return h[4:] if h.startswith('www.') else h
rows=list(csv.DictReader((RUN/'prsj_companies_all.data').open(encoding='utf-8-sig')))
sh=get_client(str(DIST/'shared/gcp_service_account.json')).open_by_key('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ');names=set();domains=set()
for ws in sh.worksheets():
 vals=ws.get_all_values()
 if not vals:continue
 head=[unicodedata.normalize('NFKC',x).strip().lower() for x in vals[0]]
 if 'company_name' not in head:continue
 ci=head.index('company_name');ui=head.index('url') if 'url' in head else None
 for x in vals[1:]:
  if ci<len(x):names.add(nn(x[ci]))
  if ui is not None and ui<len(x) and dom(x[ui]):domains.add(dom(x[ui]))
jpx={r['normalized_company_name'] for r in csv.DictReader((EF/'jpx_listed_companies_20260630.csv').open(encoding='utf-8-sig'))};rules=[r for r in csv.DictReader((EF/'major_group_rules.csv').open(encoding='utf-8-sig')) if r['match_type']=='company_contains']
weak={'モニタリング会社','リリース配信会社','調査会社',''}
for r in rows:
 key=nn(r['company_name']);d=dom(r['url']);rs=[]
 if key in names or (d and d in domains):rs.append('既存または除外リスト一致')
 if key in jpx:rs.append('JPX会社名完全一致')
 for q in rules:
  if q['normalized_value'] and q['normalized_value'].lower() in key:rs.append('大手管理語='+q['match_value'])
 if r['source_category'] in weak:rs.append('対象外業態='+('分類なし' if not r['source_category'] else r['source_category']))
 if not r['url']:rs.append('公式URLなし')
 r['normalized_name']=key;r['normalized_domain']=d;r['prefilter']='exclude' if rs else 'pass';r['prefilter_reason']=' / '.join(dict.fromkeys(rs))
out=RUN/'prsj_prefiltered.data';fields=list(rows[0])
with out.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
rep={'total':len(rows),'pass':sum(r['prefilter']=='pass' for r in rows),'exclude':sum(r['prefilter']=='exclude' for r in rows),'new_exclusions':sum(r['prefilter']=='exclude' and '既存または除外リスト一致' not in r['prefilter_reason'] for r in rows),'existing':sum('既存または除外リスト一致' in r['prefilter_reason'] for r in rows)}
(RUN/'prefilter_summary.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(rep,ensure_ascii=False,indent=2))
