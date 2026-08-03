import csv,re
from pathlib import Path
from urllib.parse import urlparse

HERE=Path(__file__).parent
sources=[
 ('ビルメンフェア',HERE/'bmfair_crawled.csv'),
 ('ビルメンCONNECT',HERE/'building_connect_crawled.csv'),
 ('JAPAN SHOP',HERE/'retailtech_crawled.csv'),
]
BAD_NAME=('会社名','商号株式会社','名称株式会社','社名株式会社','Name株式会社','新たに','株式会社は','株式会社を','株式会社の','株式会社で','株式会社へ','株式会社から','株式会社に','私たち','について','サイトマップ','共同創業','従業員','製造メーカー株式会社','運営元株式会社','JAPAN株式会社','非鉄金属手配は','会社概要有限会社','商号を','・有限会社','株式会社ベルクは','運営部署株式会社','株式会社ユニティが')
BAD_CONTACT=('recruit','/news/','/information/','/topics/','privacy','sitemap','/blog/','/knowledge/','/product/','terms-of-use','announce','/document/','/download/','/performance/','/arrival-infomation','/information')
MAJOR=('アイリスオーヤマ','マキタ','リンレイ','ユシロ化学','J.フロント','ダイキン','大塚商会','パナソニック','TOPPAN','DNP','大日本印刷','リコー','キヤノン','三菱','住友','日立','東芝','富士通','NEC','オカムラ','コクヨ','LIXIL','YKK','文化シヤッター','セコム','ALSOK','レドバンス','ロッテ','NISSHA','日本写真印刷','店研創意')
TERMS=('店舗','施設','清掃','衛生','設備','保守','メンテナンス','内装','床','照明','什器','施工','空調','厨房','サイン','防滑','修繕','点検','建物','ビル','カーペット','ロボット','現場')
out=[]
for source_name,path in sources:
 for r in csv.DictReader(path.open(encoding='utf-8-sig',newline='')):
  n=r.get('company_name','').strip();c=r.get('contact_url','').strip();e=r.get('evidence','').strip()
  if not n or not c or len(n)>40 or n in ('株式会社','有限会社','合同会社'):continue
  if n in ('Japan合同会社','アスワン株式会社'):continue
  if any(x in n for x in BAD_NAME) or any(x.lower() in n.lower() for x in MAJOR):continue
  if any(x in c.lower() for x in BAD_CONTACT):continue
  if n.startswith(('公益財団法人','一般社団法人','公益社団法人')):continue
  if source_name=='JAPAN SHOP' and not any(x in e for x in TERMS):continue
  parsed=urlparse(r['url']);root=f'{parsed.scheme}://{parsed.netloc}/' if parsed.scheme and parsed.netloc else r['url']
  out.append({'company_name':n,'url':root,'contact_url':c,'区分':'A｜清掃・設備・店舗運営支援','検出ワード':source_name+'：'+e[:120],'source_url':r['source_url']})
seen=set();unique=[]
for r in out:
 domain=re.sub(r'^www\.','',re.sub(r'^https?://','',r['url']).split('/')[0])
 if domain in seen:continue
 seen.add(domain);unique.append(r)
fields=['company_name','url','contact_url','区分','検出ワード','source_url']
with (HERE/'facility_candidate_seed.csv').open('w',encoding='utf-8-sig',newline='') as h:
 w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(unique)
print({'raw':len(out),'seed':len(unique),'sources':{n:sum(1 for r in out if r['検出ワード'].startswith(n+'：')) for n,_ in sources}})
