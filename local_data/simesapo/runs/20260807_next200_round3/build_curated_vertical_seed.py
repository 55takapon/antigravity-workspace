from __future__ import annotations

import csv, re
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

HERE=Path(__file__).parent
OUT=HERE/'curated_vertical_seed.csv'
HEAD={'User-Agent':'Mozilla/5.0 (compatible; SimesapoResearch/1.0)'}
CONTACT=re.compile(r'contact|inquiry|toiawase|otoiawase|form|お問い合わせ|お問合せ|問合せ|ご相談|見積',re.I)
ROWS=[
('株式会社Number','https://clinic-promotion.com/','医科・歯科'),
('ありがとうデザイン株式会社','https://www.seitai-homepage.com/','治療院'),
('有限会社ビジネススクウェア','https://www.clinic-seoplus.com/','医科・歯科'),
('株式会社ジット','https://gourmet.z-it.jp/','飲食店'),
('株式会社Method','https://www.method-innovation.co.jp/','医科・歯科'),
('株式会社ハロペ','https://halope.co.jp/halope-web.html','医科・歯科'),
('株式会社メディココンサルティング','https://www.medico-consulting.jp/','医科・歯科'),
('株式会社吉田企画','https://clinic-mkt.com/','医科・歯科'),
('株式会社リッチオール','https://www.richall-dental.com/','医科・歯科'),
('株式会社ノーマリズム','https://mitecow.com/','美容室・サロン'),
('株式会社集客ラボ','https://yadobee.jp/','旅館・ホテル'),
('株式会社ADGRAPHY','https://www.adgraphy.jp/','旅館・ホテル'),
('Do PLUS','https://www.do-plus.com/','店舗事業者'),
('BIZ SUP','https://www.bizsup-web.com/','地域店舗'),
('株式会社Loop','https://www.loop08.com/','店舗事業者'),
('株式会社クルム','https://kurum.jp/','地域事業者'),
('WEBCRAFTS','https://webcrafts.jp/gbp/','地域店舗'),
('株式会社オレンジ','https://orangelynx.jp/','店舗事業者'),
('My Choice株式会社','https://www.mychoice.co.jp/','医療・飲食'),
('株式会社大志','https://www.hpkoubou-taishi.com/','小規模事業者'),
('Kurumi株式会社','https://kurumi.co.jp/','店舗事業者'),
('株式会社BSKプランニング','https://bskplanning.jp/zennbu','小規模事業者'),
('株式会社プロスペラゴ','https://www.prospelago.co.jp/services/google-sns/','地域店舗'),
('株式会社MEcreate','https://mecreate.co.jp/store-seo-homepage/','店舗事業者'),
('株式会社Terra Design','https://www.terra-design.co.jp/area/tachikawa/','地域店舗'),
('株式会社リショウ','https://hanjo.pro/','店舗事業者'),
('株式会社MASTERPIECE','https://www.masterpiece-mp.com/web-marketing','店舗事業者'),
('株式会社ツナグ','https://tunaguinc.com/gbp/','店舗事業者'),
('FP&B','https://www.fpb-japan.com/web','店舗事業者'),
('株式会社Eプレゼンス','https://www.e-presence.jp/','地域事業者'),
('株式会社エイト','https://eight-media.co.jp/','地域事業者'),
('株式会社ビゴップ','https://big-up.link/recourse/consulting/','飲食店'),
('Sooon株式会社','https://kuchikore-meo.com/','店舗事業者'),
]
def host(u): return (urlparse(u).hostname or '').lower().removeprefix('www.')
def contact(url):
    if 'halope.co.jp' in url: return 'https://form.run/@halope-5000'
    try:
        r=requests.get(url,headers=HEAD,timeout=25); r.raise_for_status(); r.encoding=r.apparent_encoding
        s=BeautifulSoup(r.text,'html.parser'); found=[]
        for a in s.select('a[href]'):
            href=urljoin(r.url,a.get('href','')).split('#',1)[0]; sig=a.get_text(' ',strip=True)+' '+href
            if host(href)==host(r.url) and CONTACT.search(sig) and not re.search(r'recruit|採用|privacy|login|ログイン',sig,re.I): found.append(href)
        return list(dict.fromkeys(found))[0] if found else ''
    except Exception:return ''
rows=[]
for name,url,label in ROWS:
    c=contact(url)
    rows.append({'company_name':name,'url':url,'address':'','phone':'','contact_url':c,'区分':f'S｜{label}特化Web・集客支援','検出ワード':f'公式サイト確認：{label}顧客＋Web集客／制作＋運用支援','source_url':url})
with OUT.open('w',encoding='utf-8-sig',newline='') as f:
    fields=['company_name','url','address','phone','contact_url','区分','検出ワード','source_url']; w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
print({'rows':len(rows),'contact_ok':sum(bool(r['contact_url']) for r in rows),'out':str(OUT)})
