import concurrent.futures,hashlib,json,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE=Path(__file__).parent
sys.path.insert(0,r'C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\.claude\skills\002-contact-extract\scripts')
from write_contacts import probe
CACHE=BASE/'contact_checks';CACHE.mkdir(exist_ok=True)

def check(item):
    row,result=item; path=CACHE/(str(row['_row'])+'.json')
    if path.exists():return json.loads(path.read_text(encoding='utf-8'))
    url=result.get('contact_url','')
    if result.get('method')=='probe':url=probe(result.get('probe_candidates',[]))
    out={'idx':row['idx'],'_row':row['_row'],'company_name':row['company_name'],'official_url':row['base_url'],'detected_url':url,'contact_url':'','checked_at':datetime.now(timezone.utc).isoformat(),'check':'NOT_DETECTED'}
    if url:
        try:
            res=requests.get(url,timeout=18,headers={'User-Agent':'Mozilla/5.0','Accept-Language':'ja,en;q=0.8'})
            out.update(http_status=res.status_code,final_url=res.url)
            if res.status_code!=200:out['check']='HTTP_ERROR'
            else:
                if res.encoding in (None,'ISO-8859-1'):res.encoding=res.apparent_encoding
                soup=BeautifulSoup(res.text,'html.parser')
                for tag in soup(['script','style','noscript']):tag.decompose()
                text=' '.join(soup.stripped_strings)
                out.update(title=soup.title.get_text(' ',strip=True) if soup.title else '',text=text[:40000],content_hash=hashlib.sha256(res.content).hexdigest())
                stop=re.search(r'(?:営業|勧誘|セールス)[^。\n]{0,100}(?:お断り|ご遠慮|禁止|お控え|対応いたしかね|対応致しかね|受け付け[^。]{0,12}ません|受けつけ[^。]{0,12}ません|お受け[^。]{0,12}ません)',text)
                controls=soup.select('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=checkbox]):not([type=radio]),textarea,select')
                textarea=bool(soup.find('textarea'))
                email=any('mail' in (' '.join([c.get('type',''),c.get('name',''),c.get('id','')])).lower() for c in controls)
                out.update(control_count=len(controls),textarea=textarea,email_control=email,form_count=len(soup.find_all('form')),iframes=[t.get('src','') for t in soup.find_all('iframe')])
                if stop:out.update(check='SALES_RESTRICTED',restriction=stop.group(0))
                elif len(controls)>=2 and (textarea or email):out.update(check='FORM_PRESENT',contact_url=url)
                else:out['check']='FORM_UNCONFIRMED'
        except Exception as e:out.update(check='FETCH_ERROR',error=type(e).__name__+': '+str(e)[:220])
    path.write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8')
    return out

def main():
    rows=json.loads((BASE/'full_batch.json').read_text(encoding='utf-8'))
    lookup={r['idx']:r for r in rows}
    processed=set();total=0
    while True:
        files=sorted((BASE/'chunks').glob('results_*.json'))
        jobs=[]
        for f in files:
            if f.name in processed:continue
            data=json.loads(f.read_text(encoding='utf-8'))
            jobs.extend((lookup[r['idx']],r) for r in data['results'])
            processed.add(f.name)
        if jobs:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
                for out in pool.map(check,jobs):
                    total+=1
                    if total%100==0:print(json.dumps({'checked':total}),flush=True)
        manifest=json.loads((BASE/'chunk_manifest.json').read_text(encoding='utf-8'))
        if len(processed)==manifest['chunks']:break
        time.sleep(2)
    checks=[json.loads(p.read_text(encoding='utf-8')) for p in CACHE.glob('*.json')]
    assert len(checks)==len(rows)
    results=[{'idx':r['idx'],'method':'link' if r['contact_url'] else 'none','contact_url':r['contact_url']} for r in checks]
    (BASE/'checked_results.json').write_text(json.dumps({'results':results},ensure_ascii=False),encoding='utf-8')
    from collections import Counter
    print(json.dumps({'completed':len(checks),'checks':dict(Counter(r['check'] for r in checks))}),flush=True)

if __name__=='__main__':main()
