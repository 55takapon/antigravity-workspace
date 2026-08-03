import csv
from pathlib import Path
from urllib.parse import urlparse

HERE=Path(__file__).parent
source=list(csv.DictReader((HERE/'funeral_fair_candidates.csv').open(encoding='utf-8-sig',newline='')))
TERMS=('葬','供養','遺影','遺体','遺族','骨壺','骨つぼ','棺','仏具','仏衣','祭壇','香典','会葬','霊園','位牌','火葬','返礼','墓','終活','生花','エンバーミング','納棺','葬送','メモリアル')
BAD_HOSTS=('youtube.com','youtu.be','facebook.com','instagram.com','x.com')
BAD_CONTACT=('category/news','category/exhibition','/information/','/topics/','/news/')
EXCLUDE_NAMES=(
    'エプソン販売株式会社','リンベル株式会社','株式会社アルバTOWA',
    '有限会社ワイ・イー・ワイ','有限会社和光造花製作所','株式会社コーリング',
    '株式会社ユニコーン',
    '株式会社エスビー・イトー','株式会社ユー花園',
)
rows=[]
for row in source:
    if row['company_name'] in EXCLUDE_NAMES:continue
    if not row.get('contact_url','').strip():continue
    evidence=row.get('evidence','')
    if not any(t in evidence for t in TERMS):continue
    hosts=((urlparse(row['url']).hostname or '').lower(),(urlparse(row['contact_url']).hostname or '').lower())
    if any(any(b in h for b in BAD_HOSTS) for h in hosts):continue
    if any(x in row['contact_url'] for x in BAD_CONTACT):continue
    rows.append({
        'company_name':row['company_name'],'url':row['url'],'contact_url':row['contact_url'],
        '区分':'S｜業界特化Web制作・店舗支援ハブ','検出ワード':'葬祭・供養業界ハブ：'+evidence[:120],
        'source_url':row['source_url'],
    })
fields=['company_name','url','contact_url','区分','検出ワード','source_url']
with (HERE/'funeral_candidate_seed.csv').open('w',encoding='utf-8-sig',newline='') as h:
    w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(rows)
print({'input':len(source),'filtered':len(rows)})
