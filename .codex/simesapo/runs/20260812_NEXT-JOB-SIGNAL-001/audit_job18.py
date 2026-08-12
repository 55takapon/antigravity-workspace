import csv,re
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
RUN=Path(__file__).parent
rows=[r for r in csv.DictReader((RUN/'job30_prefiltered.data').open(encoding='utf-8-sig')) if r['prefilter']=='pass']
contactpat=re.compile(r'お問い合わせ|お問合せ|contact|inquiry|ご相談|資料請求',re.I)
servicepat=re.compile(r'(クライアント|お客様|企業|店舗|法人).{0,50}(集客|広告|sns|web|マーケティング|販促)|(広告運用|sns運用|web制作|集客支援|販促支援|マーケティング支援)',re.I|re.S)
forced={
'株式会社BLITZ Marketing':'事業規模・多角化が個人事業主の提携先想定を超えるため',
'株式会社トランス':'上場企業トランザクショングループの連結子会社',
'株式会社NDPマーケティング':'大手デジタル広告案件中心で規模適合性が低いため'}
def audit(r):
 if r['company_name'] in forced:r.update(classification='除外',audit_reason=forced[r['company_name']],contact_url='',contact_check='enterprise_or_group',evidence_url=r['url']);return r
 contacts=[];texts=[];evidence=[]
 try:
  res=requests.get(r['url'],timeout=15,headers={'User-Agent':'Mozilla/5.0'});res.raise_for_status();s=BeautifulSoup(res.text,'html.parser');texts.append(s.get_text(' ',strip=True));evidence.append(res.url)
  for a in s.select('a[href]'):
   u=urljoin(res.url,a.get('href'));lab=a.get_text(' ',strip=True)+' '+u
   if contactpat.search(lab) and not u.startswith(('mailto:','tel:','javascript:')):contacts.append(u)
  contacts=list(dict.fromkeys(contacts))[:10];form=''
  for u in contacts:
   try:
    rr=requests.get(u,timeout=15,headers={'User-Agent':'Mozilla/5.0'});ss=BeautifulSoup(rr.text,'html.parser');texts.append(ss.get_text(' ',strip=True)[:3000])
    if rr.ok and ss.find('form') and len(ss.select('input,textarea,select'))>=2:form=rr.url;evidence.append(rr.url);break
   except Exception:pass
  service=bool(servicepat.search(' '.join(texts)))
  check='real_form_confirmed' if form else ('contact_page_no_form' if contacts else 'no_contact_link')
 except Exception as e:form='';service=False;check='site_fetch_failed:'+type(e).__name__
 send=bool(form and service)
 r.update(classification='送付対象' if send else '除外',audit_reason='第三者向けWeb・広告・SNS・販促受託と実在フォームを確認' if send else ('第三者向け受託根拠未確認' if not service else '実在する問い合わせフォーム未確認'),contact_url=form,contact_check=check,evidence_url=' ; '.join(dict.fromkeys(evidence)),service_match=str(service));return r
with ThreadPoolExecutor(max_workers=6) as ex:rows=list(ex.map(audit,rows))
with (RUN/'job18_audited.data').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
from collections import Counter
print({'total':len(rows),'classifications':dict(Counter(r['classification'] for r in rows)),'contacts':dict(Counter(r['contact_check'] for r in rows))})
for r in rows:print(r['classification'],r['company_name'],r.get('service_match'),r['contact_check'],r['contact_url'])
