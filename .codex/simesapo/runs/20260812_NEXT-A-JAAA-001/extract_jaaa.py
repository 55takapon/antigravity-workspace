import csv
from pathlib import Path
from bs4 import BeautifulSoup

RUN=Path(__file__).parent
s=BeautifulSoup((RUN/'jaaa_members.html').read_text(encoding='utf-8'),'html.parser')
rows=[]
for a in s.select('main p > a[href]'):
 name=' '.join(a.get_text(' ',strip=True).split())
 url=a.get('href','').strip()
 if name and url and not url.startswith('https://www.jaaa.ne.jp'):
  rows.append({'company_name':name,'url':url})
seen=set(); rows=[r for r in rows if not (r['company_name'] in seen or seen.add(r['company_name']))]
with (RUN/'jaaa_members_all.data').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['company_name','url']);w.writeheader();w.writerows(rows)
print({'total':len(rows),'with_url':sum(bool(r['url']) for r in rows)})
