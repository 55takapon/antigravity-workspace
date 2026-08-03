import csv,re
from pathlib import Path

HERE=Path(__file__).parent
rows=list(csv.DictReader((HERE/'retailtech_crawled.csv').open(encoding='utf-8-sig',newline='')))
BAD_NAME=('会社名','商号株式会社','名称株式会社','社名株式会社','Name株式会社','新たに','株式会社は','株式会社を','株式会社の','株式会社で','株式会社へ','株式会社から','株式会社に','株式会社ギアは','株式会社ライフレンジは','従業員感謝祭','は株式会社')
BAD_CONTACT=('recruit','/news/','/information/','/topics/','privacy','sitemap','/blog/','/knowledge/','/product/','terms-of-use','announce','/document/','/download/')
MAJOR=('C-United','HITOWA','SBI','セブン','じげん','第一興商','船井総研','ダイコク電機','ワオ・コーポレーション','シニアライフクリエイト','プロントコーポレーション','ファーストキッチン')
OVERRIDE={
 'CareNation\u200b':'株式会社CareNation','HLC「ソレイルミナーレ(リハビリ特化型デイサービス)」':'株式会社HLC',
 'K Village 韓国語教室':'株式会社K Village','Mobility Box':'Mobility Box株式会社','SUMiTAS':'株式会社SUMiTAS',
 'やる気':'株式会社やる気','エム・ワイ・ケー/美容室イレブンカット':'株式会社エム・ワイ・ケー','ギア':'株式会社ギア',
 'ベンリーコーポレーション / 生活支援サービス':'株式会社ベンリーコーポレーション','マコトフードサービス':'株式会社マコトフードサービス',
 'ライフレンジ':'株式会社ライフレンジ','レックス・ベリー':'株式会社レックス・ベリー','ワールドフランチャイズシステムズ / アパレル シューラルー':'株式会社ワールドフランチャイズシステムズ',
 '言楽舎':'株式会社言楽舎','和韓料理スンドゥブ専門店じゅろく':'株式会社UG','子供服・育児用品専門リユースショップ ECOLIFE COCO':'株式会社ECOLIFE COCO',
 'フランチャイズの窓口':'シェアリングテクノロジー株式会社','ビズライズ':'株式会社ビズライズ','ネコロボマン':'セレクチュアー株式会社',
 'ブレイバンス':'株式会社ブレイバンス',
}
out=[]
for r in rows:
 n=OVERRIDE.get(r.get('display_name',''),r.get('company_name','').strip());c=r.get('contact_url','').strip();e=r.get('evidence','').strip()
 if not n or not c or len(n)>40 or n in ('株式会社','有限会社','合同会社'):continue
 if n in ('株式会社K','株式会社X','株式会社TOYO','かめやグループ株式会社','株式会社UBX'):continue
 if any(x in n for x in BAD_NAME) or any(x.lower() in n.lower() for x in MAJOR):continue
 if any(x in c.lower() for x in BAD_CONTACT):continue
 out.append({'company_name':n,'url':r['url'],'contact_url':c,'区分':'A｜開業・出店・FC・店舗コンサル','検出ワード':'FC・多店舗ハブ：'+e[:120],'source_url':r['source_url']})

seen=set();unique=[]
for r in out:
 k=(r['company_name'],re.sub(r'^www\.','',re.sub(r'^https?://','',r['url']).split('/')[0]))
 if k in seen:continue
 seen.add(k);unique.append(r)
fields=['company_name','url','contact_url','区分','検出ワード','source_url']
with (HERE/'fc_candidate_seed.csv').open('w',encoding='utf-8-sig',newline='') as h:
 w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(unique)
print({'input':len(rows),'seed':len(unique)})
