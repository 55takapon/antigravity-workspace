from __future__ import annotations
import csv,re
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup

HERE=Path(__file__).parent; OUT=HERE/'direct_agency_seed.csv'
HEAD={'User-Agent':'Mozilla/5.0 (compatible; SimesapoResearch/1.0)'}
CONTACT=re.compile(r'contact|inquiry|toiawase|otoiawase|form|お問い合わせ|お問合せ|問合せ|ご相談|見積',re.I)
ROWS=[
('株式会社Third Arrow','https://www.third-arrow.site/','飲食店'),
('株式会社Re:worth','https://www.reworth-dental.com/','歯科医院'),
('株式会社Din','https://www.dinmarketing001.com/','歯科医院'),
('株式会社weart','https://weart.co.jp/clinic/','歯科・美容クリニック'),
('株式会社Nexi','https://nex-i.net/','美容・エステサロン'),
('株式会社WJ Marketing','https://www.wjmarketing.net/','飲食店'),
('株式会社STABBLE','https://stabble.biz/','飲食店'),
('株式会社プロパティフォース','https://property-force.jp/web-agency/','不動産会社'),
('株式会社ディプシー','https://deepxi.net/','整骨院・治療院'),
('株式会社ベットパートナーズ','https://www.vetpartners.co.jp/advertising-and-promotion/','動物病院'),
('株式会社畠山企画','https://hatakeyama-kikaku.co.jp/','スクール・学習塾'),
('K2 WEB DESIGN','https://www.jukusite.pro/','スクール・学習塾'),
('整骨院web','https://seikotsuinweb.com/','整骨院・治療院'),
('株式会社セブンスフロア','https://www.7thfloor.co.jp/lp/funeral_marketing/','葬儀社'),
('株式会社フォーディメンション','https://4-dimensions.jp/web-ads/','ブライダル'),
('株式会社Do','https://do-inc.jp/','ブライダル'),
('合同会社ウノマス','https://unomas.jp/lp-sougi/','葬儀社'),
('株式会社AOM','https://www.aom-consult.com/','介護施設'),
('株式会社インフィール','https://wedding.imfeel.jp/','ブライダル'),
('ベーシック株式会社','https://www.basic-web.co.jp/service/promotion/','葬儀社'),
('株式会社LLB','https://llb.co.jp/','ブライダル'),
('株式会社CDM','https://www.wearecdm.jp/','ブライダル'),
('株式会社ブリリア','https://www.bulilia.com/','店舗事業者'),
('株式会社Textrade','https://business.textrade.org/','実店舗'),
('株式会社グッドラフ','https://goodlaugh.co.jp/lp/samurai/','士業'),
('株式会社Libra','https://libra-partners.jp/','士業'),
('山本コーポレーション','https://www.yamamotocorp.jp/','自由診療クリニック'),
('LnX合同会社','https://lnx.co.jp/','中小企業・店舗'),
('株式会社Medical Research','https://medicalresearch.jp/service/web/','医院・クリニック'),
]
def host(u):return (urlparse(u).hostname or '').lower().removeprefix('www.')
def find_contact(url):
 if 'goodlaugh.co.jp/' in url:return 'https://goodlaugh.co.jp/contact/'
 if 'libra-partners.jp/' in url:return 'https://libra-partners.jp/contact/'
 try:
  r=requests.get(url,headers=HEAD,timeout=25);r.raise_for_status();r.encoding=r.apparent_encoding;s=BeautifulSoup(r.text,'html.parser'); out=[]
  if s.find('form') and CONTACT.search(r.url+' '+s.get_text(' ',strip=True)[:4000]):out.append(r.url)
  for a in s.select('a[href]'):
   h=urljoin(r.url,a.get('href','')).split('#',1)[0];sig=a.get_text(' ',strip=True)+' '+h
   if host(h)==host(r.url) and CONTACT.search(sig) and not re.search(r'recruit|採用|privacy|login|ログイン',sig,re.I):out.append(h)
  return list(dict.fromkeys(out))[0] if out else ''
 except Exception:return ''
rows=[]
for name,url,label in ROWS:
 c=find_contact(url)
 rows.append({'company_name':name,'url':url,'address':'','phone':'','contact_url':c,'区分':f'S｜{label}特化Web・集客支援','検出ワード':f'公式サイト確認：{label}顧客＋Web／広告／SNSの受託運用','source_url':url})
with OUT.open('w',encoding='utf-8-sig',newline='') as f:
 fields=['company_name','url','address','phone','contact_url','区分','検出ワード','source_url'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
print({'rows':len(rows),'contact_nonblank':sum(bool(r['contact_url']) for r in rows),'output':str(OUT)})
