from __future__ import annotations
import base64,csv,json,re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import parse_qs,urljoin,urlparse
import requests
from bs4 import BeautifulSoup

HERE=Path(__file__).parent; OUT=HERE/'direct_agency_scale.csv'; AUDIT=HERE/'direct_agency_scale_audit.csv'
HEAD={'User-Agent':'Mozilla/5.0 (compatible; SimesapoResearch/1.0)'}
TARGETS=['歯科医院','クリニック','美容クリニック','整骨院 整体院','動物病院','美容室 サロン','飲食店','旅館 ホテル','学習塾 スクール','士業','不動産会社','工務店 リフォーム','葬儀社','ブライダル 結婚式場','介護施設','フィットネス ジム','自動車販売 整備','写真館 フォトスタジオ','観光施設 レジャー','フランチャイズ 多店舗']
REGIONS=['北海道 東北','関東','東京','北陸 甲信越','東海 名古屋','関西 大阪','中国 四国','九州 福岡']
TEMPLATES=[
'{target} 専門 Web集客 広告運用 SNS運用 株式会社 {region}',
'{target} 向け ホームページ制作 集客支援 お問い合わせ {region}',
'{target} 特化 Webマーケティング 運用代行 会社 {region}',
]
BLOCK={'youtube.com','facebook.com','instagram.com','x.com','wikipedia.org','prtimes.jp','wantedly.com','indeed.com','en-gage.net','note.com','ameblo.jp','amazon.co.jp','rakuten.co.jp','google.com','yahoo.co.jp','bing.com','itreview.jp','imitsu.jp','web-kanji.com','comparison.jp'}
LEGAL=re.compile(r'(?:株式会社|有限会社|合同会社)\s*[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶ・＆&ー]{1,35}|[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶ・＆&ー]{1,35}\s*(?:株式会社|有限会社|合同会社)')
BADNAME=re.compile(r'会社名|会社概要|お問い合わせ|確認画面|株式会社様|運営会社|弊社|当社|お客様|採用|Google|Yahoo',re.I)
PROFILE=re.compile(r'会社概要|会社情報|企業情報|運営会社|法人概要|about|company|corporate|profile',re.I)
CONTACT=re.compile(r'contact|inquiry|toiawase|otoiawase|form|お問い合わせ|お問合せ|問合せ|ご相談|見積',re.I)
SUPPORT=['Web集客','WEB集客','ホームページ制作','Web制作','WEB制作','広告運用','SNS運用','SEO','MEO','Googleビジネス','Googleマップ','集客支援','マーケティング支援']

def host(u):return (urlparse(u).hostname or '').lower().removeprefix('www.')
def unwrap(u):
 if host(u)=='bing.com':
  x=parse_qs(urlparse(u).query).get('u',[''])[0]
  if x.startswith('a1'):
   try:return base64.b64decode(x[2:]+'===').decode()
   except Exception:return ''
 return u
def search(q):
 try:r=requests.get('https://www.bing.com/search',params={'q':q,'count':'20'},headers=HEAD,timeout=25);r.raise_for_status()
 except Exception:return []
 s=BeautifulSoup(r.text,'html.parser');out=[]
 for a in s.select('li.b_algo h2 a[href]'):
  u=unwrap(a.get('href',''));d=host(u)
  if u.startswith('http') and d and not any(d==b or d.endswith('.'+b) for b in BLOCK):out.append((d,u,q))
 return out[:12]
def fetch(u):
 r=requests.get(u,headers=HEAD,timeout=22,allow_redirects=True);r.raise_for_status()
 if 'html' not in r.headers.get('content-type','').lower():raise ValueError('non_html')
 r.encoding=r.apparent_encoding;return r.url,BeautifulSoup(r.text,'html.parser')
def clean_name(v):
 v=''.join(v.split()).strip('｜|:：-–—・');m=LEGAL.search(v)
 if not m:return ''
 n=''.join(m.group(0).split())
 return n if 4<=len(n)<=40 and not BADNAME.search(n) else ''
def json_names(o):
 out=[]
 if isinstance(o,dict):
  typ=o.get('@type',[]);typ=[typ] if isinstance(typ,str) else typ
  if any(str(t) in {'Organization','Corporation','LocalBusiness','ProfessionalService'} for t in typ):
   for k in ('legalName','name'):
    if isinstance(o.get(k),str):out.append(o[k])
  for v in o.values():out.extend(json_names(v))
 elif isinstance(o,list):
  for v in o:out.extend(json_names(v))
 return out
def names_from(s):
 out=[]
 for n in s.select('script[type="application/ld+json"]'):
  try:out += [clean_name(x) for x in json_names(json.loads(n.get_text()))]
  except Exception:pass
 for tr in s.select('tr'):
  c=tr.find_all(['th','td'])
  if len(c)>=2 and re.fullmatch(r'会社名|社名|法人名|商号|運営会社',c[0].get_text(' ',strip=True)):out.append(clean_name(c[1].get_text(' ',strip=True)))
 for dt in s.select('dt'):
  if re.fullmatch(r'会社名|社名|法人名|商号|運営会社',dt.get_text(' ',strip=True)) and dt.find_next_sibling('dd'):out.append(clean_name(dt.find_next_sibling('dd').get_text(' ',strip=True)))
 for f in s.select('footer'):
  out += [clean_name(m.group(0)) for m in LEGAL.finditer(f.get_text(' ',strip=True))]
 text=' '.join(s.get_text(' ',strip=True).split())
 for m in re.finditer(r'(?:会社名|社名|法人名|商号|運営会社)\s*[：:]?\s*(.{0,100})',text):
  n=LEGAL.search(m.group(1))
  if n:out.append(clean_name(n.group(0)))
 for meta in s.select('meta[property="og:site_name"][content],meta[name="application-name"][content]'):
  out.append(clean_name(meta.get('content','')))
 title=s.title.get_text(' ',strip=True) if s.title else ''
 out += [clean_name(m.group(0)) for m in LEGAL.finditer(title)]
 return [x for x in out if x]
def validate(item):
 d,u,q=item; a={'domain':d,'url':u,'query':q,'result':'','company_name':'','contact_url':''}
 try:base,page=fetch(u)
 except Exception as e:a['result']='fetch_'+type(e).__name__;return None,a
 pages=[(base,page)];profiles=[];contacts=[]
 for link in page.select('a[href]'):
  href=urljoin(base,link.get('href','')).split('#',1)[0];sig=link.get_text(' ',strip=True)+' '+href
  if host(href)==host(base) and PROFILE.search(sig):profiles.append(href)
  if CONTACT.search(sig) and not re.search(r'採用|recruit|privacy|ログイン|login',sig,re.I):contacts.append(href)
 for href in list(dict.fromkeys(profiles))[:4]:
  try:pages.append(fetch(href))
  except Exception:pass
 names=[]
 for _,s in pages:names.extend(names_from(s))
 if not names:a['result']='name_unconfirmed';return None,a
 name=Counter(names).most_common(1)[0][0];a['company_name']=name
 text=' '.join(s.get_text(' ',strip=True) for _,s in pages);terms=[x for x in SUPPORT if x in text]
 if len(terms)<2:a['result']='support_short';return None,a
 contact=list(dict.fromkeys(contacts))[0] if contacts else ''
 if not contact:a['result']='contact_missing';return None,a
 a['contact_url']=contact;a['result']='accepted'
 label=next((t for t in TARGETS if all(x in text for x in t.split()[:1])),'地域事業者')
 row={'company_name':name,'url':base,'address':'','phone':'','contact_url':contact,'区分':f'S｜{label}向けWeb・集客受託','検出ワード':'公式サイト確認：顧客業種＋'+'・'.join(terms[:3]),'source_url':u}
 return row,a

queries=[t.format(target=x,region=r) for x in TARGETS for r in REGIONS for t in TEMPLATES]
if AUDIT.exists():
 with AUDIT.open(encoding='utf-8-sig',newline='') as f:
  cached=list(csv.DictReader(f))
 unique={r['domain']:(r['domain'],r['url'],r['query']) for r in cached if r.get('domain') and r.get('url')}
else:
 hits=[]
 with ThreadPoolExecutor(max_workers=12) as p:
  for g in p.map(search,queries):hits.extend(g)
 unique={d:(d,u,q) for d,u,q in hits}
results=[];aud=[]
with ThreadPoolExecutor(max_workers=20) as p:
 fs=[p.submit(validate,x) for x in unique.values()]
 for f in as_completed(fs):
  r,a=f.result();aud.append(a)
  if r:results.append(r)
results=list({host(r['url']):r for r in results}.values());results.sort(key=lambda x:x['company_name'])
fields=['company_name','url','address','phone','contact_url','区分','検出ワード','source_url']
with OUT.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(results)
with AUDIT.open('w',encoding='utf-8-sig',newline='') as f:
 af=['domain','url','query','result','company_name','contact_url'];w=csv.DictWriter(f,fieldnames=af);w.writeheader();w.writerows(aud)
print({'queries':len(queries),'domains':len(unique),'accepted':len(results),'reasons':dict(Counter(x['result'] for x in aud)),'output':str(OUT)})
