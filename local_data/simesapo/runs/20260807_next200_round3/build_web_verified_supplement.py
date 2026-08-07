import csv
from pathlib import Path

rows=[
("株式会社WAYTOGO","https://salonsupport.waytogo.co.jp/","https://salonsupport.waytogo.co.jp/","S｜美容サロン特化Web・集客支援","美容サロン顧客＋Web制作＋LINE運用支援"),
("株式会社宿楽","https://www.yadoraku.co.jp/","https://www.yadoraku.co.jp/","S｜宿泊施設特化Web・集客支援","旅館・ホテル顧客＋Web集客＋継続運用代行"),
("株式会社Re:worth","https://www.reworth-dental.com/","https://www.reworth-dental.com/","S｜歯科特化Web制作・集客支援","歯科医院顧客＋Web制作＋問い合わせフォーム"),
("有限会社ハナダ・カンパニー","https://hanada-company.com/","https://hanada-company.com/","S｜宿泊施設特化Web・集客支援","旅館・ホテル顧客＋Web販促＋集客支援"),
("株式会社ADGRAPHY","https://www.adgraphy.jp/","https://www.adgraphy.jp/","S｜宿泊施設特化Web・集客支援","旅館・ホテル顧客＋Web制作＋運用支援"),
("合同会社QOL","https://kaigo-qol.com/","https://kaigo-qol.com/","S｜介護事業特化Web・集客支援","介護事業者顧客＋Web制作＋集客運用代行"),
("株式会社cantik","https://cantik.co.jp/","https://cantik.co.jp/","S｜治療院特化Web・集客支援","治療院顧客＋Web制作＋MEO・SNS運用"),
("株式会社リライト","https://relight-consulting.com/","https://relight-consulting.com/","S｜飲食店特化Web・集客支援","飲食店顧客＋Web制作＋GBP・SNS運用"),
("株式会社Third Arrow","https://www.third-arrow.site/","https://www.third-arrow.site/","S｜飲食店特化Web・集客支援","飲食店顧客＋Web集客＋SNS・MEO運用"),
("Kaz株式会社","https://kaz-medical.co.jp/","https://kaz-medical.co.jp/","S｜治療院特化Web・集客支援","整骨院顧客＋Web制作＋MEO・LINE支援"),
("株式会社LINK BANK","https://link-bank.co.jp/","https://link-bank.co.jp/","S｜治療院特化Web・集客支援","治療院顧客＋Web制作＋広告運用"),
("株式会社サイシア","https://saisia.co.jp/","https://saisia.co.jp/","S｜治療院特化Web・集客支援","整骨院顧客＋Web制作＋広告運用"),
("株式会社ホクシン","https://www.hok.co.jp/","https://www.hok.co.jp/contact/","A｜地域広告・販促・Web支援","地域事業者顧客＋広告・Web制作＋販促支援"),
("株式会社MATSURI","https://bau-marketing.jp/","https://bau-marketing.jp/","S｜動物病院特化Web・集客支援","動物病院顧客＋Web制作＋LINE・広告運用"),
("株式会社ゼロメディカル","https://zeromedical.tv/","https://zeromedical.tv/contact/","S｜医療特化Web・集客支援","医療機関顧客＋Web制作＋継続運用改善"),
("株式会社ミカタ","https://mikataga.jp/","https://mikataga.jp/","S｜工務店特化Web・集客支援","工務店顧客＋Web制作＋広告・SNS運用"),
("株式会社グルコム","https://grucom.jp/","https://grucom.jp/contact/","S｜動物病院特化Web・集客支援","動物病院顧客＋Web制作＋広告・改善運用"),
("シグニ株式会社","https://service.cygni.co.jp/","https://service.cygni.co.jp/","S｜動物病院特化Web・集客支援","動物病院顧客＋Web制作＋継続運用"),
("株式会社チタン","https://www.titun.jp/","https://www.titun.jp/","S｜工務店特化Web・集客支援","工務店顧客＋Web制作＋広告・SNS運用"),
("メディストペット株式会社","https://medistpet.jp/","https://medistpet.jp/contact/","S｜ペット業界特化Web・集客支援","ペット事業者顧客＋Web制作＋SNS・MEO支援"),
("合同会社HPアシスト","https://kakuyasu-homepage.jp/","https://kakuyasu-homepage.jp/","A｜地域店舗Web・集客支援","中小店舗顧客＋Web制作＋広告・GBP運用"),
("and only株式会社","https://web.andonly.co.jp/","https://web.andonly.co.jp/","A｜地域店舗Web・集客支援","地域店舗顧客＋Web制作＋GBP運用支援"),
("株式会社ラッシュビズ","https://rushbiz.co.jp/","https://rushbiz.co.jp/","S｜飲食店特化Web・集客支援","飲食店顧客＋開業・集客＋SNS運用"),
("株式会社Oakmont","https://oakmontjy.com/","https://oakmontjy.com/","A｜地域店舗Web・集客支援","地域店舗顧客＋Web制作＋広告運用"),
("Brand Hatch株式会社","https://brandhatch.co.jp/","https://brandhatch.co.jp/contact/","A｜地域店舗Web・集客支援","店舗顧客＋Web制作＋SNS・MEO運用"),
("株式会社ステップバイワーク","https://sbwinc.co.jp/","https://sbwinc.co.jp/","A｜地域店舗Web・集客支援","地域事業者顧客＋Web制作＋集客運用"),
("アクタスクリエイト株式会社","https://actus-create.com/","https://actus-create.com/","S｜美容店舗Web・集客支援","美容店舗顧客＋Web制作＋SNS・MEO運用"),
("株式会社プロジエ","https://559.co.jp/","https://559.co.jp/","A｜地域広告・販促・Web支援","地域事業者顧客＋Web制作＋広告運用"),
("株式会社ウェブズ","https://webz.co.jp/","https://webz.co.jp/","A｜地域広告・販促・Web支援","地域事業者顧客＋Web制作＋広告・SNS運用"),
("株式会社ネクストエッジ","https://nextedge.jp/","https://nextedge.jp/","A｜地域広告・販促・Web支援","地域店舗顧客＋Web制作＋SNS広告運用"),
("株式会社AREA","https://area9.work/","https://area9.work/","A｜地域広告・販促・Web支援","地域店舗顧客＋Web制作＋広告運用"),
("合同会社デジポップ","https://digipop.co.jp/","https://digipop.co.jp/","A｜地域広告・販促・Web支援","地域事業者顧客＋Web制作＋SNS・広告運用"),
("株式会社どっとWEB","https://dot-pc.com/","https://dot-pc.com/","A｜地域広告・販促・Web支援","地域事業者顧客＋Web制作＋SNS運用代行"),
("株式会社SHIFT","https://shift-to.co.jp/","https://shift-to.co.jp/","A｜地域広告・販促・Web支援","地域事業者顧客＋Web制作＋広告・SNS活用支援"),
("株式会社CoCoDigi","https://cocodigi.co.jp/","https://cocodigi.co.jp/","A｜地域広告・販促・Web支援","地域中小事業者顧客＋Web制作＋SNS広告運用"),
("有限会社Frida","https://frida-studio.com/","https://frida-studio.com/contact/","A｜地域広告・販促・Web支援","地域店舗顧客＋Web制作＋SNS運用支援"),
("株式会社ZEN","https://zen-focus.co.jp/","https://zen-focus.co.jp/","A｜地域SNS・店舗集客支援","地域店舗顧客＋SNS運用＋広告・PR支援"),
("株式会社青陵社","https://www.seiryosha.co.jp/","https://www.seiryosha.co.jp/","A｜地域広告・販促・Web支援","地域事業者顧客＋Web制作＋広告・SNS運用"),
("株式会社オファシム","https://ofasim.co.jp/","https://ofasim.co.jp/","A｜地域広告・販促・Web支援","地域中小企業顧客＋Web制作＋SNS運用"),
("株式会社TPS","https://www.tps.yamagata.jp/","https://www.tps.yamagata.jp/","A｜地域広告・販促・Web支援","地域店舗顧客＋Web制作＋SNS運用代行"),
("株式会社01","https://01-inc.jp/","https://01-inc.jp/","A｜地域広告・販促・Web支援","地域事業者顧客＋Web制作＋運用改善"),
("株式会社SUNSHINE WORKS","https://sunshine-works.co.jp/","https://sunshine-works.co.jp/","A｜地域広告・販促・Web支援","地域事業者顧客＋Web広告＋SNS運用"),
("株式会社KOiKi","https://koiki.co.jp/","https://koiki.co.jp/","A｜地域広告・販促・Web支援","地域事業者顧客＋Web制作＋広告運用"),
("株式会社ナレッジサービス","https://knowledge-service.net/","https://knowledge-service.net/","A｜地域広告・販促・Web支援","地域企業顧客＋Web制作＋SNS運用代行"),
("株式会社ウェブサイト","https://www.web3110.jp/","https://www.web3110.jp/","A｜地域広告・販促・Web支援","地域企業顧客＋Web制作＋SNS運用代行"),
("株式会社em","https://em-style.co.jp/","https://em-style.co.jp/contact/","A｜地域広告・販促・Web支援","地域事業者顧客＋Web制作＋SNS運用"),
("SAIUN TECHNOLOGY株式会社","https://saiun-technology.com/","https://saiun-technology.com/","A｜地域広告・販促・Web支援","地域店舗顧客＋Web制作＋SNS・広告運用"),
("株式会社VIRTA","https://virta-info.com/","https://virta-info.com/","A｜地域広告・販促・Web支援","地域事業者顧客＋Web制作＋広告・SNS運用"),
("株式会社アイポケット沖縄","https://www.ipocket-okinawa.co.jp/","https://www.ipocket-okinawa.co.jp/contact/","A｜地域広告・販促・Web支援","地域企業顧客＋Web制作＋SNS・広告運用"),
("株式会社PURPOSE","https://qpurpose.com/","https://qpurpose.com/","A｜地域広告・販促・Web支援","地域店舗顧客＋Web制作＋集客運用"),
("株式会社LinoPlus","https://linoplus.co.jp/","https://linoplus.co.jp/","A｜地域広告・販促・Web支援","地域事業者顧客＋Web制作＋SNS・広告運用"),
("株式会社Value Hack","https://www.value-hack.co.jp/","https://www.value-hack.co.jp/","A｜地域広告・販促・Web支援","地域店舗顧客＋Web制作＋継続運用"),
]
fields=["company_name","url","address","phone","maps_url","contact_url","message","sent_at","status","error_reason","screenshot_path","provider_used","提案区分","H1","区分","検出ワード"]
out=Path(__file__).with_name("web_verified_supplement_seed.csv")
with out.open("w",encoding="utf-8-sig",newline="") as f:
 w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
 for name,url,contact,cat,evidence in rows:
  w.writerow({"company_name":name,"url":url,"contact_url":contact,"提案区分":"未判定","区分":cat,"検出ワード":evidence})
print({"rows":len(rows),"output":str(out)})
