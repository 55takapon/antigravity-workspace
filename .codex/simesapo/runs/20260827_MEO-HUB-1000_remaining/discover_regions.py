import sys,json,time,hashlib
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE=Path(__file__).parent
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
from prepare_pool import nk
CACHE=BASE/'regional_cache';CACHE.mkdir(exist_ok=True)
e=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8'));names={nk(r.get('company_name')) for r in e};known=set()
for p in (BASE/'advertising_cache').glob('*.json'):
 known.update(r['source_url'] for r in json.loads(p.read_text(encoding='utf-8')))
u='https://houjin.goo.to/corporations/categories/advertising';s=BeautifulSoup(requests.get(u,timeout=25).text,'html.parser')
roots=sorted({urljoin(u,a['href']) for a in s.select('a[href]') if '/prefs/' in a['href'] and 'category-advertising' in a['href']})
out={}
for root in roots:
 last=set()
 for page in range(100):
  u=root+('' if page==0 else '/page'+str(page));p=CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.json')
  if p.exists():rows=json.loads(p.read_text(encoding='utf-8'))
  else:
   time.sleep(1)
   try:
    r=requests.get(u,timeout=25,headers={'User-Agent':'Mozilla/5.0'})
    if r.status_code in (403,429):raise RuntimeError('Source access restricted')
    if r.status_code!=200:break
    r.encoding='utf-8';s=BeautifulSoup(r.text,'html.parser');rows=[]
    for card in s.select('article.company-list-card'):
     a=card.select_one('a.cl-name');address=card.select_one('.cl-location')
     if a:rows.append({'company_name':a.get_text(' ',strip=True),'source_url':urljoin(u,a['href']),'url':'','phone':'','address':address.get_text(' ',strip=True) if address else ''})
    p.write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
   except requests.RequestException:break
  current={r['source_url'] for r in rows}
  if not current or current==last:break
  last=current
  for row in rows:
   if row['source_url'] not in known and nk(row['company_name']) not in names:out.setdefault(row['source_url'],row)
  tmp=BASE/'regional_pending.tmp';tmp.write_text(json.dumps(list(out.values()),ensure_ascii=False),encoding='utf-8');tmp.replace(BASE/'regional_pending.json')
  print(root.split('/')[-2],page,'new_pending',len(out),flush=True)
(BASE/'regional_lists_complete.flag').touch()
print('done',len(out),flush=True)
