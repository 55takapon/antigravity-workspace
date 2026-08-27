import sys,json,csv,re,time,hashlib,argparse
from pathlib import Path
from urllib.parse import urljoin,urlsplit,urldefrag
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
BASE=Path(__file__).parent
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
from prepare_pool import nk,dk,pk
SEEDS=['https://www.paj-pid.jp/members/index.html','https://jlaa2003.com/company/','https://www.zakko.or.jp/about/member','https://www.jaaa.ne.jp/about/member-companies/','https://www.aca-j.or.jp/meibo/','https://www.oac.or.jp/member/','https://www.acc-cm.or.jp/about/members2.html','https://www.aj-pia.or.jp/map/','https://osaka-pia.or.jp/sitemaps/','https://www.tokyo-printing.or.jp/about/outline/']
CACHE=BASE/'source_cache';CACHE.mkdir(exist_ok=True)
robots={};last={}
def get(u):
 host=dk(u);root=urlsplit(u).scheme+'://'+urlsplit(u).netloc
 if host not in robots:
  rp=RobotFileParser();rp.set_url(root+'/robots.txt')
  try:
   rr=requests.get(root+'/robots.txt',timeout=15)
   if rr.status_code==200:rp.parse(rr.text.splitlines())
   elif rr.status_code in (401,403):rp.disallow_all=True
   else:rp.allow_all=True
  except requests.RequestException:rp.disallow_all=True
  robots[host]=rp
 if not robots[host].can_fetch('*',u):return None
 p=CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.json')
 if p.exists():return json.loads(p.read_text(encoding='utf-8'))
 wait=max(0,last.get(host,0)+1-time.monotonic())
 if wait:time.sleep(wait)
 last[host]=time.monotonic()
 try:
  r=requests.get(u,timeout=20,headers={'User-Agent':'Mozilla/5.0'})
  if r.status_code!=200 or 'text/html' not in r.headers.get('content-type',''):return None
  if not r.encoding or r.encoding.lower() in ('iso-8859-1','ascii'):r.encoding=r.apparent_encoding
  soup=BeautifulSoup(r.text,'html.parser')
  links=[]
  for a in soup.select('a[href]'):
   label=a.get_text(' ',strip=True) or ' '.join(x.get('alt','') for x in a.select('img'))
   links.append({'url':urljoin(r.url,a['href']),'label':label,'context':a.parent.get_text(' ',strip=True)[:400]})
  d={'url':r.url,'links':links};p.write_text(json.dumps(d,ensure_ascii=False),encoding='utf-8');return d
 except requests.RequestException:return None
def write(rows):
 with (BASE/'association_raw.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['company_name','url','phone','address','source_url']);w.writeheader();w.writerows(rows)
if __name__=='__main__':
 existing=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8'))
 names={nk(x.get('company_name')) for x in existing};domains={dk(x.get('url')) for x in existing}
 queue=[(u,0) for u in SEEDS];seen=set();out={}
 while queue and len(seen)<900:
  u,depth=queue.pop(0)
  if u in seen:continue
  seen.add(u);page=get(u)
  if not page:continue
  for l in page['links']:
   v,label=urldefrag(l['url'])[0],l['label'];domain=dk(v)
   if label.startswith(('http','www.')):
    candidate=re.split(r'https?://|www\.',l.get('context',''))[0].strip()
    if 2<len(candidate)<70 and re.search('株式会社|有限会社|合同会社|印刷|広告',candidate):label=candidate
   if re.search('login|members_only|ログイン',v+label,re.I):continue
   if not v.startswith(('http://','https://')) or re.search(r'\.(pdf|jpg|png|zip)(\?|$)',v,re.I):continue
   same=domain==dk(page['url'])
   directory=bool(re.search('組合|協会|支部|会員|名簿',label))
   if depth<3 and ((same and re.search('会員|名簿|支部|組合員|member|division|branch',label+' '+v,re.I)) or (u=='https://www.aj-pia.or.jp/map/' and (directory or label=='ホームページ'))):
    if v not in seen:queue.append((v,depth+1))
   if same or directory or not label or len(label)>80:continue
   if not re.search(r'株式会社|有限会社|合同会社|（株）|\(株\)|（有）|\(有\)|印刷|デザイン|広告|企画',label):continue
   if domain in domains or nk(label) in names or domain in out:continue
   if any(x in domain for x in ['google.','facebook.','twitter.','instagram.','youtube.','amazon.']):continue
   out[domain]={'company_name':label,'url':v,'phone':'','address':'','source_url':page['url']}
  write(list(out.values()))
  print(json.dumps({'pages':len(seen),'pending':len(queue),'new':len(out),'source':u},ensure_ascii=False),flush=True)
 print('done',len(out))
