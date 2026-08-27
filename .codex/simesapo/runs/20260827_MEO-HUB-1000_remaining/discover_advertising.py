import sys,json,csv,re,time,argparse,hashlib
from pathlib import Path
from urllib.parse import urlsplit,urljoin
import requests
from bs4 import BeautifulSoup
BASE=Path(__file__).parent
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
from prepare_pool import nk,dk
def save(path,rows):
 fields=sorted({k for r in rows for k in r})
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--end',type=int,default=411);a=ap.parse_args()
 existing=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8'))
 names={nk(x.get('company_name')) for x in existing};domains={dk(x.get('url')) for x in existing}
 cache=BASE/'advertising_cache';cache.mkdir(exist_ok=True)
 out={};audit=[]
 for page in range(a.end+1):
  u='https://houjin.goo.to/corporations/categories/advertising'+('' if page==0 else '/page'+str(page))
  p=cache/(str(page)+'.json')
  if p.exists():items=json.loads(p.read_text(encoding='utf-8'))
  else:
   time.sleep(1)
   try:
    r=requests.get(u,timeout=25,headers={'User-Agent':'Mozilla/5.0'})
    if r.status_code!=200:
     print('status',page,r.status_code,flush=True)
     if r.status_code in (403,404,429):break
     continue
    r.encoding='utf-8';soup=BeautifulSoup(r.text,'html.parser');items=[]
    for card in soup.select('article.company-list-card'):
     n=card.select_one('a.cl-name');img=card.select_one('img.cl-logo');addr=card.select_one('.cl-location')
     if not n:continue
     src=img.get('src','') if img else '';parts=urlsplit(src)
     candidate=parts.scheme+'://'+parts.netloc+'/' if parts.scheme in ('http','https') else ''
     items.append({'company_name':n.get_text(' ',strip=True),'url':candidate,'phone':'','address':addr.get_text(' ',strip=True) if addr else '', 'source_url':urljoin(u,n.get('href','')),'discovery_note':'名簿ロゴ画像の配信元。公式性は別途確認必須'})
    p.write_text(json.dumps(items,ensure_ascii=False),encoding='utf-8')
   except requests.RequestException as e:
    print('error',page,type(e).__name__,flush=True);continue
  for row in items:
   d=dk(row['url']);n=nk(row['company_name'])
   if not d or d in domains or n in names or d in out:continue
   if any(x in d for x in ['goo.to','amazonaws.com','cloudfront.net','google.','gstatic.','wp.com','wixstatic.','website-files.','jimdo','shopify','sakura.ne.jp']):continue
   out[d]=row
  save(BASE/'advertising_raw.csv',list(out.values()))
  print(json.dumps({'page':page,'new_raw':len(out)}),flush=True)
 print('done',len(out))
