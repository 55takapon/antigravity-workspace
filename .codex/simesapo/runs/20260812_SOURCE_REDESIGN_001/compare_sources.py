import csv,json,re,sys,unicodedata
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
ROOT=Path(r'C:\Users\hangy\.gemini\antigravity');RUN=Path(__file__).parent;DIST=ROOT/'.agent/skills/simesapo-sales-skills-dist';EF=DIST/'custmize/enterprise_filter'
sys.path[:0]=[str(DIST/'.codex_pydeps'),str(DIST/'shared')]
from sheets_io import get_client
def nn(s):
 s=unicodedata.normalize('NFKC',s or '').lower();s=re.sub(r'^(株式会社|有限会社|合同会社|合資会社|一般社団法人|公益社団法人)','',s);s=re.sub(r'(株式会社|有限会社|合同会社|合資会社)$','',s);return re.sub(r'[^0-9a-z\u3040-\u30ff\u3400-\u9fff]+','',s)
def dom(u):
 if not u:return ''
 if '://' not in u:u='https://'+u
 h=(urlparse(u).hostname or '').lower().strip('.');return h[4:] if h.startswith('www.') else h
s=BeautifulSoup((RUN/'jiaa_members.html').read_text(encoding='utf-8'),'html.parser')
rows=[]
for typ,sel in [('正会員','#regular_member li a'),('賛助会員','#support_member li a'),('準会員A','#associate-a_member li a'),('準会員B','#associate-b_member li a')]:
 for a in s.select(sel):
  name=' '.join(a.get_text(' ',strip=True).split());url=a.get('href','').strip()
  if name:rows.append({'source':'JIAA','member_type':typ,'company_name':name,'url':url})
seen=set();rows=[r for r in rows if not ((nn(r['company_name']),dom(r['url'])) in seen or seen.add((nn(r['company_name']),dom(r['url']))))]
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
for r in rows:
 key=nn(r['company_name']);d=dom(r['url']);reasons=[]
 if key in names or (d and d in domains):reasons.append('existing')
 if key in jpx:reasons.append('jpx')
 if any(q['normalized_value'] and q['normalized_value'].lower() in key for q in rules):reasons.append('major_keyword')
 r['normalized_name']=key;r['normalized_domain']=d;r['prefilter_reason']=' / '.join(reasons);r['pass']=not reasons
with (RUN/'jiaa_prefiltered.data').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
rep={'JIAA_total':len(rows),'existing':sum('existing' in r['prefilter_reason'] for r in rows),'jpx_or_major':sum(('jpx' in r['prefilter_reason'] or 'major_keyword' in r['prefilter_reason']) for r in rows),'raw_pass':sum(r['pass'] for r in rows),'raw_pass_rate':round(100*sum(r['pass'] for r in rows)/len(rows),1),'member_types':{t:sum(r['member_type']==t for r in rows) for t in sorted(set(r['member_type'] for r in rows))}}
(RUN/'source_comparison.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(rep,ensure_ascii=False,indent=2));print('PASS SAMPLE');
for r in [x for x in rows if x['pass']][:80]:print(r['member_type'],r['company_name'],r['url'])
