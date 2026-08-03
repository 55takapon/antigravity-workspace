import csv,re
from pathlib import Path
HERE=Path(__file__).parent
rows=list(csv.DictReader((HERE/'retailtech_crawled.csv').open(encoding='utf-8-sig',newline='')))
TERMS=('店舗','小売','飲食','POS','レジ','決済','オーダー','リテール','在庫','販促','サイネージ','券売','予約','キャッシュレス','チェーンストア','来店','店頭')
BAD_NAME=('会社名','私たち','にて','として','では','について','運営する','を設立','より','サイトマップ','共同創業','参加','サポ','Japan株式会社','インテグレーション株式会社','社名株式会社')
BAD_CONTACT=('recruit','/news/','/information/','/topics/','privacy','sitemap','/blog/','/knowledge/','/product/','terms-of-use','announce','/document/','/download/','/homemade/')
MAJOR=('SmartHR','STORES','U-NEXT','Preferred','WORKS株式会社','PagerDuty','Ridgelinez','i-PRO','ラクスル','マウスコンピューター','ブラザー販売','株式会社HBA','株式会社イシダ','クラスメソッド','セイコーソリューションズ','ローレルバンクマシン','ポスタス株式会社')
OFFICIAL_NAME_OVERRIDES={
    'MJYコンサルタント':'株式会社エムジェイワイコンサルタント',
    'infonerv':'株式会社infonerv',
    'エフケイシステム':'株式会社エフケイシステム',
    'コンポーネントデザイン':'コンポーネントデザイン株式会社',
    'スマート・ソリューション・テクノロジー':'株式会社スマート・ソリューション・テクノロジー',
    'タイムリープ':'タイムリープ株式会社',
    'トマトランド':'トマトランド株式会社',
    'マジックハット':'株式会社マジックハット',
    'リチェルカ':'株式会社リチェルカ',
    'リンコム':'株式会社リンコム',
    'ルミーズ':'ルミーズ株式会社',
    'ディーグラット':'株式会社ディーグラット',
    'ナスコー':'株式会社ナスコー',
    'TIプランニング':'株式会社TIプランニング',
    '高崎共同計算センター':'株式会社高崎共同計算センター',
    'ClipLine':'ClipLine株式会社',
    'Lazuli':'Lazuli株式会社',
    'Recustomer':'Recustomer株式会社',
    'iTAN':'株式会社iTAN',
    'ネフロック':'株式会社ネフロック',
    'リサーチ・アンド・イノベーション':'株式会社リサーチ・アンド・イノベーション',
    '杏林社':'株式会社杏林社',
    '森創':'株式会社森創',
    '和晃':'有限会社和晃',
    'トマトランド':'トマトランド株式会社',
    'フツパー':'株式会社フツパー',
    '北海道デジタル・アンド・コンサルティング':'北海道デジタル・アンド・コンサルティング株式会社',
    '光商事':'光商事株式会社',
}
out=[]
for r in rows:
    n=OFFICIAL_NAME_OVERRIDES.get(r.get('display_name',''),r.get('company_name','').strip());c=r.get('contact_url','').strip();e=r.get('evidence','')
    if not n or not c or len(n)>35 or n in ('株式会社','有限会社','合同会社'):continue
    if any(x in n for x in BAD_NAME) or any(x.lower() in n.lower() for x in MAJOR):continue
    if any(x in c.lower() for x in BAD_CONTACT):continue
    if not any(x in e for x in TERMS) and r.get('display_name','') not in OFFICIAL_NAME_OVERRIDES:continue
    out.append({'company_name':n,'url':r['url'],'contact_url':c,'区分':'A｜POS・予約・店舗DX・OA販売','検出ワード':'店舗DXハブ：'+e[:120],'source_url':r['source_url']})
fields=['company_name','url','contact_url','区分','検出ワード','source_url']
with (HERE/'retail_candidate_seed.csv').open('w',encoding='utf-8-sig',newline='') as h:
    w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(out)
print({'input':len(rows),'seed':len(out)})
