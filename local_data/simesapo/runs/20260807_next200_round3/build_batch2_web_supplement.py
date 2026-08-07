import csv
from pathlib import Path
p=Path(__file__).parent
raw=[
("株式会社シーサイド","https://c-side.co.jp/","A｜地域Web・SNS運用支援"),("株式会社Fun","https://oita-fun.com/","A｜地域広告・Web・SNS支援"),
("株式会社nil","https://nil-inc.jp/","A｜地域Web・SNS運用支援"),("青森ネット広告株式会社","https://aomori-netkoukoku.com/","A｜地域Web・広告支援"),
("株式会社Craft Solution","https://craft-solution.jp/","A｜地域SNS・広告支援"),("株式会社吉和の森","https://yoshikazunomori-hachinohe.co.jp/","A｜地域Web・SNS運用支援"),
("Arte株式会社","https://arte.aomori.jp/","A｜地域Web・SNS・広告支援"),("グリーク株式会社","https://www.glic.co.jp/","A｜地域Web・広告・SNS支援"),
("株式会社トリアナ","https://triana.jp/","A｜地域Web・広告・SNS支援"),("株式会社シャーロック","https://sherlocks.co.jp/","A｜地域Web・広告支援"),
("株式会社プロモートウェブ","https://promote-web.jp/","A｜地域Web・広告・SNS支援"),("合同会社adconnect","https://adconnect-kumamoto.com/","A｜地域Web・広告支援"),
("株式会社システムキューブ","https://www.hp-wakayama.jp/","A｜地域Web・運用支援"),("株式会社カノヱ","https://www.soyuz.jp/","A｜地域Web・販促支援"),
("SHIN株式会社","https://www.shin-inc.jp/","A｜地域Web・広告運用支援"),("株式会社MIALI","https://miali.co.jp/","A｜地域Web・SNS運用支援"),
("有限会社テイク・シー","https://take-c.co.jp/","A｜地域広告・Web・SNS支援"),("株式会社グッドエブリデイ","https://adsnp.com/","A｜地域店舗Web・集客支援"),
("株式会社アレドレ","https://www.aredore.jp/","A｜地域広告・Web・SNS支援"),("株式会社coe","https://www.coecoe.jp/","A｜地域店舗SNS・広告支援"),
("株式会社DIXIA","https://di-xia.com/","A｜地域Web・SNS・広告支援"),("株式会社コモテック","https://www.comotec.ne.jp/","A｜地域Web・広告運用支援"),
("有限会社香月","https://kagetu-net.com/","A｜地域Web・広告支援"),("株式会社グレイトヘルプ","https://greathelp.co.jp/","A｜地域Web・広告・SNS支援"),
("株式会社NEOWERT","https://neowert.co.jp/","A｜地域広告・Web運用支援"),("スキマデザイン株式会社","https://schema-design.net/","A｜地域Web・集客運用支援"),
("株式会社NEXT岐阜","https://next-gifu.jp/","A｜地域Web・広告支援"),
("WEBTAN","https://webtantousha.com/","A｜地域Web・SNS・広告支援"),("NEOBU","https://neobu.jp/","A｜地域SNS・Web支援"),
("緑 web studio","https://midori-webstudio.com/","S｜宿泊施設Web・SNS運用支援"),("TerraPocket","https://terrapocket.jp/","S｜美容サロンWeb・集客支援"),
("Dental Web Atelier","https://dental-web-atelier.com/","S｜歯科Web・運用支援"),("LAPLAB","https://lapl.jp/","A｜地域Web・SNS・広告支援"),
("フューチャイズム","https://jimohack.com/","A｜地域Web・SNS運用支援"),("エイチレフデザイン","https://href.design/","A｜地域Web・SNS運用支援"),
("WANDERMUST","https://wandermust.net/","A｜地域Web・SNS運用支援"),("WSC-Potechi","https://www.wscpotechi.com/","A｜地域店舗Web・SNS支援"),
("RAI WEB SERVICE","https://rai-web.jp/","A｜地域Web・SNS・広告支援"),("ホムペリ","https://homuperi.biz/","A｜地域Web・運用支援"),
("アドミヤ","https://admiya.com/","A｜地域Web・運用支援"),("Pixel Craft","https://pixelcraft.jp/","A｜地域Web・SNS運用支援"),
("W-UP","https://ehime-web.jp/","A｜地域店舗Web・集客支援"),("ぬこファクトリー","https://nuko-factory.com/","A｜地域Web・SNS・広告支援"),
("あなたのホームページ屋さん","https://hp-yasan.com/","A｜地域中小企業Web支援"),("Pastime design works","https://pastimedesignworks.com/","A｜地域Web・SNS運用支援"),
("レクトデザイン","https://www.rectodesign.jp/","A｜地域Web・広告支援"),("バウハウス大分","https://www.bauhaus-oita.com/","A｜地域広告・Web支援"),
("株式会社Curiver","https://curiver.com/","A｜地域Web・SNS運用支援"),("株式会社ループコーポレーション","https://loop-co.com/","A｜地域Web・SNS広告支援"),
("株式会社Sense","https://www.sense0111.co.jp/","A｜地域Web・SNS・広告支援"),("えるさす株式会社","https://www.elseus.com/","A｜地域Web・SNS広告支援"),
("株式会社Aibin","https://www.aibin.design/","A｜地域SNS・広告支援"),("株式会社ピント","https://pintpint.com/","A｜地域店舗広告・Web・SNS支援"),
("PAZOOM","https://pazoom.jp/","A｜地域Web・SNS運用支援"),("株式会社ハジメクリエイト","https://hajimecreate.com/","A｜地域Web・広告運用支援"),
("株式会社ローカス","https://locus-web.jp/","A｜地域Web・SNS・広告支援"),("すずなりクリエイト","https://suzunari-create.com/","A｜地域Web・SNS運用支援"),
("株式会社ベルストラード","https://www.berstrads.com/","S｜飲食・観光SNS集客支援"),("テイクワン","https://snstake1.com/","A｜地域店舗SNS運用支援"),
("株式会社WJ Marketing","https://www.wjmarketing.net/","S｜飲食店SNS運用支援"),("株式会社Nexi","https://nex-i.net/","S｜美容サロンSNS集客支援"),
("株式会社TATANANA","https://www.tatanana.jp/","S｜飲食店SNS・PR支援"),("株式会社SHINANOKI","https://shinanoki.tokyo/","S｜宿泊施設SNS・PR支援"),
("株式会社THAN","https://than.co.jp/","S｜飲食店SNS運用支援"),("株式会社Bro","https://www.bro-sns.com/","A｜地域店舗SNS運用支援"),
("株式会社エンパワーメント","https://empt.co.jp/","S｜美容サロンSNS・Web運用支援"),("株式会社STABBLE","https://stabble.biz/","S｜飲食店Web・SNS集客支援"),
("株式会社ア・レステ","https://www.arester.jp/","S｜宿泊・観光Web集客支援"),("株式会社ココチナ","https://kokochina.co.jp/","S｜飲食店SNS運用支援"),
]
fields=["company_name","url","address","phone","maps_url","contact_url","message","sent_at","status","error_reason","screenshot_path","provider_used","提案区分","H1","区分","検出ワード"]
out=p/"batch2_web_supplement_seed.csv"
with out.open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
 for name,url,cat in raw:w.writerow({"company_name":name,"url":url,"contact_url":url,"区分":cat,"検出ワード":"地域事業者・店舗顧客＋Web制作＋SNSまたは広告の継続運用"})
print({"rows":len(raw),"output":str(out)})
