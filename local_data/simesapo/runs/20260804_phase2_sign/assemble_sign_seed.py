import csv
from pathlib import Path
HERE=Path(__file__).parent
rows=list(csv.DictReader((HERE/'sign_members_crawled.csv').open(encoding='utf-8-sig',newline='')))
BAD=('category/news','category/information','/news/','/topics/','/information/','/blog/','/faq','login','privacy','sitemap')
EXCLUDE_NAMES={
 'アオイネオン株式会社福岡支店','アバンギャルドフジコウ株式会社','エースネオン電装株式会社',
 'ケイズハウス株式会社','デコラテックジャパン株式会社東京本社','ヨシトメ工芸株式会社',
 '三和ネオン株式会社','斗南電装株式会社','有限会社コーワネオン','有限会社奥野電工',
 '有限会社山北看板店','有限会社石田整美堂','株式会社アドイースト',
 '株式会社オガワ東京支店','株式会社キハラネオン製作所','株式会社シモモト工芸社','株式会社シーエス・エイ',
 '株式会社タイセイデンコウ','株式会社デコラム',
}
BRANCH_SUFFIX=('東京本社','東京支社','東京支店','福岡支店','広島営業所','札幌営業所')
out=[]
for r in rows:
    if r['company_name'] in EXCLUDE_NAMES:continue
    c=r.get('contact_url','').strip()
    if not c or any(x in c.lower() for x in BAD):continue
    item={k:r.get(k,'') for k in ('company_name','url','contact_url','区分','検出ワード','source_url')}
    for suffix in BRANCH_SUFFIX:
        if item['company_name'].endswith(suffix):item['company_name']=item['company_name'][:-len(suffix)]
    out.append(item)
fields=['company_name','url','contact_url','区分','検出ワード','source_url']
with (HERE/'sign_candidate_seed.csv').open('w',encoding='utf-8-sig',newline='') as h:
    w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(out)
print({'input':len(rows),'seed':len(out)})
