import csv,re
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup
RUN=Path(__file__).parent
rows=[r for r in csv.DictReader((RUN/'oac_prefiltered.data').open(encoding='utf-8-sig')) if r['prefilter']=='pass']
forced={
'一般社団法人Interactive Communication Experts (I.C.E.)':('exclude','業界団体であり営業提携先企業ではない'),
'株式会社日本デザインセンター':('exclude','従業員269名、国内大手企業7社の共同出資による明確な大手制作会社'),
'株式会社 明治アドエージェンシー':('exclude','明治グループの広告会社'),
}
pat=re.compile(r'お問い合わせ|お問合せ|contact|inquiry|ご相談',re.I)
for r in rows:
 contacts=[];evidence=[];status=''
 try:
  res=requests.get(r['url'],timeout=20,headers={'User-Agent':'Mozilla/5.0'});res.raise_for_status();s=BeautifulSoup(res.text,'html.parser')
  evidence.append(res.url)
  for a in s.select('a[href]'):
   u=urljoin(res.url,a.get('href'));label=a.get_text(' ',strip=True)+' '+u
   if pat.search(label) and not u.startswith(('mailto:','tel:','javascript:')):contacts.append(u)
  contacts=list(dict.fromkeys(contacts))[:12]
  form=''
  for u in contacts:
   try:
    rr=requests.get(u,timeout=20,headers={'User-Agent':'Mozilla/5.0'});ss=BeautifulSoup(rr.text,'html.parser')
    if rr.ok and ss.find('form') and len(ss.select('input,textarea,select'))>=2:form=rr.url;evidence.append(rr.url);break
   except Exception:pass
  status='real_form_confirmed' if form else ('contact_page_no_form' if contacts else 'no_contact_link')
 except Exception as e:form='';status='site_fetch_failed:'+type(e).__name__
 decision,reason=forced.get(r['company_name'],('send' if status=='real_form_confirmed' else 'exclude','OAC広告制作法人会員・制作受託' if status=='real_form_confirmed' else '実在する問い合わせフォーム未確認'))
 r.update(classification='送付対象' if decision=='send' else '除外',audit_reason=reason,contact_url=form,contact_check=status,evidence_url=' ; '.join(dict.fromkeys(evidence)),audit_date='2026-08-12')
out=RUN/'oac_audit_10.data';fields=list(rows[0])
with out.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
from collections import Counter
print({'total':len(rows),'classifications':dict(Counter(r['classification'] for r in rows)),'contacts':dict(Counter(r['contact_check'] for r in rows))})
for r in rows:print(r['classification'],r['company_name'],r['contact_check'],r['contact_url'])
