import csv,re
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

RUN=Path(__file__).parent
rows=[r for r in csv.DictReader((RUN/'jaaa_prefiltered.data').open(encoding='utf-8-sig')) if r['prefilter']=='pass']
forced={
'株式会社 アイプラネット':'三菱電機グループ会社',
'アクセンチュア 株式会社':'世界規模コンサルティング企業の日本法人',
'株式会社 M&C SAATCHI':'世界規模広告グループの日本法人',
'株式会社 神奈中商事':'上場企業・神奈川中央交通グループ',
'松竹ナビ株式会社':'上場企業・松竹グループ',
'株式会社 大広九州':'博報堂DYグループ系広告会社',
'株式会社 東急エージェンシー':'東急グループの大手広告会社',
'ビーコンコミュニケーションズ株式会社':'世界規模Publicis系広告会社',
'株式会社 フロンテッジ':'ソニー・電通系広告会社',
'株式会社 マッキャン ジャパン':'世界規模McCann広告グループの日本法人',
'株式会社 メトロアドエージェンシー':'東京メトログループ広告会社',
}
pat=re.compile(r'お問い合わせ|お問合せ|contact|inquiry|ご相談',re.I)
def audit(r):
 if r['company_name'] in forced:
  r.update(classification='除外',audit_reason=forced[r['company_name']],contact_url='',contact_check='major_group_confirmed',evidence_url=r['url'],audit_date='2026-08-12');return r
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
 r.update(classification='送付対象' if form else '除外',audit_reason='JAAA登録広告会社・広告企画運用受託' if form else '実在する問い合わせフォーム未確認',contact_url=form,contact_check=check,evidence_url=' ; '.join(dict.fromkeys(evidence)),audit_date='2026-08-12');return r
with ThreadPoolExecutor(max_workers=6) as ex:rows=list(ex.map(audit,rows))
out=RUN/'jaaa_audit_21.data';fields=list(rows[0])
with out.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
from collections import Counter
print({'total':len(rows),'classifications':dict(Counter(r['classification'] for r in rows)),'contacts':dict(Counter(r['contact_check'] for r in rows))})
for r in rows:print(r['classification'],r['company_name'],r['contact_check'],r['contact_url'])
