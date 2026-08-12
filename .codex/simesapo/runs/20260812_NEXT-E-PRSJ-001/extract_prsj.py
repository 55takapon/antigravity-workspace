import csv
from pathlib import Path
from bs4 import BeautifulSoup
RUN=Path(__file__).parent
raw=(RUN/'pr_company_search.html').read_bytes()
text=raw.decode('cp932','replace')
s=BeautifulSoup(text,'html.parser')
rows=[]
for h in s.select('h2.company-name'):
 a=h.find('a');box=h.find_parent(class_='company-box') or h.parent
 full=box.get_text(' ',strip=True) if box else h.get_text(' ',strip=True)
 prev=h.find_previous('span')
 category=prev.get_text(' ',strip=True) if prev else ''
 rows.append({'company_name':h.get_text(' ',strip=True).replace('(株)','株式会社').replace('（株）','株式会社'),'url':a.get('href','').strip() if a else '','address':'','phone':'','maps_url':'','source_category':category,'profile':(box.select_one('.company-profile').get_text(' ',strip=True) if box and box.select_one('.company-profile') else ''),'source_url':'https://area18.smp.ne.jp/area/table/45023/eg5o7c/M?S=reqaq2mbldof'})
out=RUN/'prsj_companies_all.data'
with out.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
print({'total':len(rows),'with_url':sum(bool(r['url']) for r in rows),'categories':sorted(set(r['source_category'] for r in rows))})
