import argparse,csv,json,re,time,hashlib,unicodedata,threading
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from concurrent.futures import ThreadPoolExecutor,as_completed
import requests
from bs4 import BeautifulSoup
from prepare_pool import nk,dk,pk
BASE=Path(__file__).parent.parent/'20260827_MEO-HUB-1000'
CACHE=BASE/'official_cache';CACHE.mkdir(exist_ok=True)
SERVICE=re.compile(r'(?:ホームページ|[Ww][Ee][Bb](?:サイト)?|ウェブサイト|[Ee][Cc]サイト|ランディングページ)[の・/／企画制作開発設計保守運用管理、及びやとを\s]{0,12}(?:制作|作成|構築|開発|運用|保守|管理)|(?:SNS|Instagram|インスタグラム|リスティング広告|Web広告|WEB広告|MEO|Googleビジネスプロフィール)[アカウントの・/／広告企画\s]{0,10}(?:運用|代行|支援|対策)')
RECUR=re.compile(r'保守|更新代行|運用代行|運用支援|月額|伴走|継続支援|定期.*レポート')
VERT=re.compile(r'飲食店|美容室|美容院|サロン|クリニック|歯科|整骨院|整体院|ホテル|旅館|学習塾|店舗|地域企業|中小企業')
LOCK=threading.Lock();LAST={}
HOLDS={'matt-g.jp':'スタッフ経歴とサービスを混同のため要再確認','believe.co.jp':'沿革のシステム実績のみで今回の営業適合根拠不足','pilotton.jp':'役員略歴と現行サービスを混同のため要再確認','qgm-inc.com':'別法人の事業を本体事業と混同のため要再確認','adsfactory.ne.jp':'公式ページに社名変更あり。現商号の再照合が必要','ocs.olc.co.jp':'公式ページに統合後の別商号あり。現商号の再照合が必要','www2.adovonext.com':'資格説明と提供サービスを混同のため要再確認'}
def fetch(u):
 key=hashlib.sha256(u.encode()).hexdigest();path=CACHE/(key+'.json')
 if path.exists():return json.loads(path.read_text(encoding='utf-8'))
 host=dk(u)
 with LOCK:
  wait=max(0,LAST.get(host,0)+1-time.monotonic());LAST[host]=time.monotonic()+wait
 if wait:time.sleep(wait)
 result={'requested_url':u,'retrieved_at':datetime.now().isoformat(timespec='seconds')}
 try:
  r=requests.get(u,timeout=(8,16),headers={'User-Agent':'Mozilla/5.0','Accept-Language':'ja'},allow_redirects=True)
  result.update(status=r.status_code,url=r.url)
  if r.status_code==200 and 'text/html' in r.headers.get('Content-Type',''):
   if not r.encoding or r.encoding.lower() in ('iso-8859-1','ascii'):r.encoding=r.apparent_encoding
   soup=BeautifulSoup(r.text,'html.parser');title=soup.title.get_text(' ',strip=True) if soup.title else ''
   links=[{'url':urljoin(r.url,a.get('href','')),'label':a.get_text(' ',strip=True)} for a in soup.select('a[href]')]
   for x in soup(['script','style','noscript','svg']):x.decompose()
   identity=soup.get_text(' ',strip=True)
   for x in soup.select('footer, .footer, #footer'):x.decompose()
   text=soup.get_text('\n',strip=True)
   result.update(title=title,text=text,identity_text=identity,links=links,hash=hashlib.sha256(text.encode()).hexdigest())
 except requests.RequestException as e:result.update(status=0,error=type(e).__name__)
 path.write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8');return result
def examine(row):
 r=dict(row);u=r['url'];root=urlsplit(u).scheme+'://'+urlsplit(u).netloc+'/'
 if dk(u) in HOLDS:return dict(r,review_status='RECHECK',reject_reason=HOLDS[dk(u)])
 pages=[fetch(root)];first=pages[0]
 if first.get('status')!=200 and u!=root:pages.append(fetch(u))
 valid=[p for p in pages if p.get('status')==200 and p.get('text') and dk(p.get('url'))==dk(u)]
 if not valid:return dict(r,review_status='RECHECK',reject_reason='公式サイト取得不能または別ドメインへ移動')
 links=valid[0].get('links',[]);queue=[]
 for kind in ('会社概要|会社情報|企業情報|about|company','サービス|事業内容|service|business'):
  added=0
  for l in links:
   if dk(l['url'])==dk(u) and re.search(kind,l['label']+' '+l['url'],re.I) and l['url'] not in [p.get('url') for p in pages] and not re.search(r'blog|news|column|recruit|\.pdf',l['url'],re.I):
    if l['url'] not in queue:
     queue.append(l['url']);added+=1
    if added>=4:break
 for link in list(dict.fromkeys(queue))[:8]:
  p=fetch(link);pages.append(p)
  if p.get('status')==200 and p.get('text') and dk(p.get('url'))==dk(u):valid.append(p)
 identity=any(nk(r['company_name']) in nk(p.get('identity_text','')) for p in valid)
 evidence=[];recurring=[];vertical=[];contacts=[];official_phones=[]
 for p in valid:
  text=unicodedata.normalize('NFKC',p['text'])
  for m in re.finditer(r'(?:TEL|Tel|tel|電話(?:番号)?)[\s:：.]{0,8}(0[0-9]{1,4}[\s()（）-]{1,4}[0-9]{1,4}[\s()（）-]{1,4}[0-9]{3,4})',text):
   number=pk(m.group(1))
   if 9<=len(number)<=11:official_phones.append(number)
  for m in SERVICE.finditer(text):
   snippet=text[max(0,m.start()-55):m.end()+85].replace('\n',' ')
   if not re.search('SNS運用方針|ソーシャルメディアポリシー|学ぶ|学び|学習|略歴|経歴|退職|入社|経験を積|閉鎖|終了しま|事業譲渡|統合しま',snippet):evidence.append({'url':p['url'],'text':snippet})
  if RECUR.search(text):recurring.append(p['url'])
  if VERT.search(text):vertical.append(p['url'])
  for l in p.get('links',[]):
   if l['url'].startswith('tel:') and 9<=len(pk(l['url']))<=11:official_phones.append(pk(l['url']))
   if dk(l['url'])==dk(u) and re.search(r'/(?:contact|inquiry|inquiries|toiawase|otoiawase)(?:[/.?#_-]|$)',urlsplit(l['url']).path,re.I) and not re.search(r'/news/|/blog/|/column/|/\d{4}/',l['url']):contacts.append(l['url'])
   elif dk(l['url'])==dk(u) and re.search('お問い合わせ|お問合せ|問い合わせ',l['label']) and not re.search(r'/news/|/blog/|/column/|\.pdf',l['url']):contacts.append(l['url'])
   elif l['url'].startswith('mailto:'):contacts.append(l['url'])
 if not identity:return dict(r,review_status='RECHECK',reject_reason='公式ページ本文と社名の一致を確認できない',evidence_detail=json.dumps(evidence[:3],ensure_ascii=False))
 if not evidence:return dict(r,review_status='RECHECK',reject_reason='公式ページに顧客向けWeb制作・集客運用サービスの明確な根拠なし')
 for p in valid:
  candidate_phone=pk(r.get('phone'))
  if 9<=len(candidate_phone)<=11 and candidate_phone in pk(p.get('identity_text','')):official_phones.append(candidate_phone)
 r['phone']=next(iter(official_phones),'')
 verified_contact=''
 for c in dict.fromkeys(contacts):
  if not c.startswith('http'):continue
  cp=fetch(c)
  if cp.get('status')==200 and dk(cp.get('url'))==dk(u) and re.search('お問い合わせ|お問合せ|問い合わせ|contact|inquiry',cp.get('title','')+' '+cp.get('text','')[:3000],re.I):verified_contact=cp['url'];break
 if not verified_contact and not any(c.startswith('mailto:') for c in contacts) and not r['phone']:return dict(r,review_status='RECHECK',reject_reason='公式サイトで到達できる問い合わせ先を確認できない')
 meo=any(re.search('MEO|Googleビジネスプロフィール',e['text'],re.I) for e in evidence)
 # Business fit is provisional: explicit evidence is kept separately from sales hypotheses.
 r.update(url=valid[0]['url'],review_status='EVIDENCE_CHECKED',last_verified_at=datetime.now().isoformat(timespec='seconds'),hub_type='OVERFLOW_HUB' if meo else 'ADD_ON_HUB',confidence='B',why_fit='公式ページで「'+evidence[0]['text'][:135]+'」を確認。MEOの追加提案候補（外注意向・採算は未確認）。',evidence_urls=' | '.join(dict.fromkeys(e['url'] for e in evidence[:5])),evidence_detail=json.dumps(evidence[:5],ensure_ascii=False),contact_url=verified_contact,generic_email=next((c[7:].split('?')[0] for c in contacts if c.startswith('mailto:')),''),recurring_relationship='signal_only' if recurring else 'unknown',store_client_access='signal_only' if vertical else 'unknown',margin_fit='unknown',status='MEOハブ候補')
 return r
def write(path,rows):
 fields=sorted({k for r in rows for k in r})
 with path.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('prefix');ap.add_argument('--workers',type=int,default=8);a=ap.parse_args()
 rows=list(csv.DictReader(open(a.source,encoding='utf-8-sig',newline='')));out=[]
 with ThreadPoolExecutor(max_workers=a.workers) as pool:
  for i,f in enumerate(as_completed([pool.submit(examine,r) for r in rows]),1):
   try:out.append(f.result())
   except Exception as e:raise RuntimeError('verification worker failed') from e
   if i%50==0:
    write(BASE/(a.prefix+'_audit.csv'),out);print(json.dumps({'examined':i,'evidence_checked':sum(r['review_status']=='EVIDENCE_CHECKED' for r in out)}),flush=True)
 write(BASE/(a.prefix+'_audit.csv'),out);write(BASE/(a.prefix+'_checked.csv'),[r for r in out if r['review_status']=='EVIDENCE_CHECKED'])
 print(json.dumps({'done':True,'examined':len(out),'evidence_checked':sum(r['review_status']=='EVIDENCE_CHECKED' for r in out)}),flush=True)
