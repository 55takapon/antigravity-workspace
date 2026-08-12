import csv,re
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
RUN=Path(__file__).parent
rows=[r for r in csv.DictReader((RUN/'prsj_prefiltered.data').open(encoding='utf-8-sig')) if r['prefilter']=='pass']
forced={
'Allison(アリソン・アンド・パートナーズ株式会社)':('exclude','世界規模PRネットワークの日本法人で明確な大手'),
'株式会社バーソン・ジャパン':('exclude','世界規模PR会社Bursonの日本法人で明確な大手'),
'ホフマンジャパン株式会社':('exclude','グローバルPR会社The Hoffman Agencyの日本法人で規模不適合'),
}
pat=re.compile(r'お問い合わせ|お問合せ|contact|inquiry|ご相談',re.I)
def audit(r):
 if r['url'].startswith('htts://'):r['url']='https://'+r['url'][7:]
 contacts=[];evidence=[]
 try:
  res=requests.get(r['url'],timeout=12,headers={'User-Agent':'Mozilla/5.0'});res.raise_for_status();s=BeautifulSoup(res.text,'html.parser');evidence.append(res.url)
  for a in s.select('a[href]'):
   u=urljoin(res.url,a.get('href'));lab=a.get_text(' ',strip=True)+' '+u
   if pat.search(lab) and not u.startswith(('mailto:','tel:','javascript:')):contacts.append(u)
  contacts=list(dict.fromkeys(contacts))[:8];form=''
  for u in contacts:
   try:
    rr=requests.get(u,timeout=12,headers={'User-Agent':'Mozilla/5.0'});ss=BeautifulSoup(rr.text,'html.parser')
    if rr.ok and ss.find('form') and len(ss.select('input,textarea,select'))>=2:form=rr.url;evidence.append(rr.url);break
   except Exception:pass
  check='real_form_confirmed' if form else ('contact_page_no_form' if contacts else 'no_contact_link')
 except Exception as e:form='';check='site_fetch_failed:'+type(e).__name__
 dec,reason=forced.get(r['company_name'],('send' if check=='real_form_confirmed' else 'exclude','PRSJ登録PR・広告・制作受託会社' if check=='real_form_confirmed' else '実在する問い合わせフォーム未確認'))
 r.update(classification='送付対象' if dec=='send' else '除外',audit_reason=reason,contact_url=form,contact_check=check,evidence_url=' ; '.join(dict.fromkeys(evidence)),audit_date='2026-08-12')
 return r
with ThreadPoolExecutor(max_workers=6) as executor:
 rows=list(executor.map(audit,rows))
out=RUN/'prsj_audit_18.data';fields=list(rows[0])
with out.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
from collections import Counter
print({'total':len(rows),'classifications':dict(Counter(r['classification'] for r in rows)),'contacts':dict(Counter(r['contact_check'] for r in rows))})
for r in rows:print(r['classification'],r['company_name'],r['contact_check'],r['contact_url'])
