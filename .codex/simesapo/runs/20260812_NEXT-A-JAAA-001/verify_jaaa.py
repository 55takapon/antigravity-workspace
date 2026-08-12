import json,sys
from pathlib import Path
ROOT=Path(r'C:\Users\hangy\.gemini\antigravity');DIST=ROOT/'.agent/skills/simesapo-sales-skills-dist'
sys.path[:0]=[str(DIST/'.codex_pydeps'),str(DIST/'shared')]
from sheets_io import get_client
sh=get_client(str(DIST/'shared/gcp_service_account.json')).open_by_key('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ')
ws=sh.worksheet('シート2');ex=sh.worksheet('除外リスト');pw=sh.worksheet('収集進捗管理')
sv=ws.get('A1:P',value_render_option='FORMULA');ev=ex.get('A1:P',value_render_option='FORMULA')
def v(r,i):return r[i] if i<len(r) else ''
jaaa_send=[r for r in sv[1:] if v(r,14).startswith('送付対象') and 'JAAA' in v(r,14)]
jaaa_ex=[r for r in ev[1:] if 'JAAA本監査' in v(r,14)]
first=next(i for i,r in enumerate(sv[1:],2) if v(r,14).startswith('除外'))
domains=[]
from urllib.parse import urlparse
for r in sv[1:]:
 u=v(r,1)
 if u:
  if '://' not in u:u='https://'+u
  h=(urlparse(u).hostname or '').lower();domains.append(h[4:] if h.startswith('www.') else h)
rep={'sheet2_rows':len(sv),'exclusion_rows':len(ev),'jaaa_send':len(jaaa_send),'jaaa_send_names':[v(r,0) for r in jaaa_send],'jaaa_exclusions':len(jaaa_ex),'first_exclusion_row':first,'exclusions_contiguous_bottom':all(v(r,14).startswith('除外') for r in sv[first-1:]),'send_count':sum(v(r,14).startswith('送付対象') for r in sv[1:]),'duplicate_domains_sheet2':len(domains)-len(set(domains)),'progress':pw.get('A87:F87')+pw.get('A89:F89')}
print(json.dumps(rep,ensure_ascii=False,indent=2))
