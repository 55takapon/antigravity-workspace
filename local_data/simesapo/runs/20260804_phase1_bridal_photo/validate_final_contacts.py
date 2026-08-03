import argparse, csv, json, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests
from bs4 import BeautifulSoup

HERE=Path(__file__).parent
parser=argparse.ArgumentParser()
parser.add_argument('--csv',default=str(HERE/'bridal_final_verified_50.csv'))
parser.add_argument('--output',default=str(HERE/'bridal_contact_validation.json'))
args=parser.parse_args()
rows=list(csv.DictReader(Path(args.csv).open(encoding='utf-8-sig',newline='')))

def check(idx,row):
    try:
        r=requests.get(row['contact_url'],headers={'User-Agent':'Mozilla/5.0'},timeout=20,allow_redirects=True)
        s=BeautifulSoup(r.text,'html.parser')
        text=re.sub(r'\s+',' ',s.get_text(' ',strip=True))
        forms=s.find_all('form')
        sendable=False
        for form in forms:
            blob=(form.get_text(' ',strip=True)+' '+str(form)).lower()
            if any(x in blob for x in ('textarea','メールアドレス','email','お問い合わせ内容','ご相談内容','message','送信','確認画面')) and not ('ログイン' in blob and 'お問い合わせ' not in blob):
                sendable=True
        mailto=bool(s.select('a[href^="mailto:"]'))
        inquiry=bool(re.search(r'お問い合わせ|お問合せ|問い合わせ|ご相談',text))
        return {'idx':idx,'company_name':row['company_name'],'contact_url':row['contact_url'],'status':r.status_code,'final_url':r.url,'forms':len(forms),'sendable_form':sendable,'mailto':mailto,'inquiry_text':inquiry,'decision':'pass' if r.status_code<400 and (sendable or mailto) else 'review'}
    except Exception as e:
        return {'idx':idx,'company_name':row['company_name'],'contact_url':row['contact_url'],'status':'','final_url':'','forms':0,'sendable_form':False,'mailto':False,'inquiry_text':False,'decision':'review','error':type(e).__name__}

out=[]
with ThreadPoolExecutor(max_workers=10) as p:
    fs=[p.submit(check,i,r) for i,r in enumerate(rows)]
    for f in as_completed(fs):out.append(f.result())
out.sort(key=lambda r:r['idx'])
Path(args.output).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'rows':len(out),'pass':sum(r['decision']=='pass' for r in out),'review':sum(r['decision']=='review' for r in out)},ensure_ascii=False))
for r in out:
    if r['decision']=='review': print(r)
