import csv,json,hashlib,re,sys
from pathlib import Path
from urllib.parse import urlsplit
BASE=Path(__file__).parent
CACHE=BASE.parent/'20260827_MEO-HUB-1000'/'official_cache'
rows=list(csv.DictReader((BASE/'verification_audit.csv').open(encoding='utf-8-sig')))
kind=sys.argv[1] if len(sys.argv)>1 else '根拠なし'
limit=int(sys.argv[2]) if len(sys.argv)>2 else 50
count=0
for r in rows:
 if kind not in r.get('reject_reason',''):continue
 u=urlsplit(r['url']);root=u.scheme+'://'+u.netloc+'/'
 p=CACHE/(hashlib.sha256(root.encode()).hexdigest()+'.json')
 if not p.exists():continue
 d=json.loads(p.read_text(encoding='utf-8'));t=d.get('text','')
 if not t:continue
 print('\n',r['company_name'],r['url'],d.get('title',''))
 for m in list(re.finditer('広告|販促|看板|デザイン|Web|WEB|ホームページ|TEL|電話',t))[:3]:print(t[max(0,m.start()-25):m.end()+130].replace('\n',' '))
 count+=1
 if count>=limit:break
