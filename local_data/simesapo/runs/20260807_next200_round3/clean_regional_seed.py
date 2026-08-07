import argparse, csv
from urllib.parse import urlparse

p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output',required=True); a=p.parse_args()
def host(u): return (urlparse(u).hostname or '').lower().removeprefix('www.')

REJECT={
 'ai-in-ko.or.jp','home-tv.co.jp','cocots.jp','eco3japan.com','princehotels.co.jp','chupicom.jp','jwa.or.jp',
 'chugoku-np.co.jp','heidelberg.com','nikkansports.com','videor.co.jp','dentsu.co.jp','stv.jp','motoya.co.jp',
 'print-jbf.jp','odahara.jp','zpx.co.jp','dip.co.jp','splive.co.jp','topiamedia.com','topia.or.jp','total-proof.jp',
 'okugaikoukoku.com','sign-expo.com','kakoukyou.com','edogawanavi.jp','hyojito.co.jp','jaaa.ne.jp','j-naming-award.jp',
 'crt-radio.co.jp','jaa.or.jp','riders-ad.jp'
}
NAMES={
 'befriend.co.jp':'株式会社ビーフレンド','bros-inc.jp':'株式会社ブロス','good-form.jp':'株式会社グッドフォーム',
 're-imagine.co.jp':'株式会社リ・イマジン','studio-orange.jp':'株式会社スタジオオレンジ',
 'nic-name.com':'株式会社ニックネーム・ドットコム','wspinc.co.jp':'株式会社ウェルストンプロモーション',
 'adhook.co.jp':'株式会社アドフック','ca-usc.com':'株式会社ユー・エス・シー','nakabi.jp':'nakabi株式会社',
 'takahashiinsatsu.com':'有限会社高橋印刷','sungr.co.jp':'株式会社北陸サンライズ','niigata-yomiuri-is.co.jp':'株式会社新潟読売IS',
 'oda-p.jp':'オダ精巧社印刷株式会社','hiromisangyo.jp':'ヒロミ産業株式会社','digima.co.jp':'デジタルマーケティングイノベーションラボ株式会社',
 'webcreation.co.jp':'web creation株式会社','hashigodesign.com':'ハシゴデザイン','sakudo.co.jp':'作道印刷株式会社',
 'sankei-ad.net':'株式会社産経広告社','bunkasya.co.jp':'株式会社文化社','mori-print.co.jp':'モリプリント株式会社',
 'sanjo-prn.co.jp':'三条印刷株式会社','inoue-sogo.co.jp':'井上総合印刷株式会社','tokaishiko.com':'東海紙工株式会社',
 'cando-design.jp':'株式会社キャンドゥ','hki.co.jp':'株式会社北海道機関紙印刷所','kp-c.co.jp':'駒田印刷株式会社',
 'genshoku.co.jp':'株式会社原色美術印刷社','ikbiso.com':'株式会社アイケー美創','kokusai-k.jp':'国際広宣株式会社',
 'itadaki.jp':'株式会社ITADAKI','akisenko.com':'安芸宣興株式会社','fujitoppan.co.jp':'富士凸版印刷株式会社',
 'fujikousoku.co.jp':'富士高速印刷株式会社','nakamotohonten.co.jp':'株式会社中本本店','ppad.co.jp':'株式会社ピー・パーク',
 'koshun.com':'有限会社恒春社印刷所','rakutsu.jp':'楽通株式会社','hidaka-print.com':'有限会社日高印刷所',
 'hoshi-ad.co.jp':'星企画株式会社','kobe-takagi.co.jp':'有限会社高木印刷所','tomei-p.com':'東名印刷株式会社',
 'higashiad.co.jp':'株式会社東日本広告社','e-asako.net':'株式会社東日本朝日広告社','totsumedia.co.jp':'株式会社東通メディア',
 '3ad.co.jp':'株式会社サン広告社','ad-chukoh.co.jp':'株式会社中央広告','neagariprint.com':'株式会社根上印刷所',
 'mba.co.jp':'株式会社橋本確文堂','kanoyasogo.co.jp':'株式会社綜合印刷','in-fit.co.jp':'株式会社infit',
 'maru-goto.net':'株式会社まるごとメディア新潟','imos.jp':'株式会社アイモス','ipns.co.jp':'株式会社イヅミ',
 'grip0051.com':'株式会社グリップ','cosmo-prt.co.jp':'株式会社コスモ綜合印刷','snr.co.jp':'株式会社サンライズ社',
 'trais.co.jp':'株式会社トライス','domeix.jp':'株式会社ドミックスコーポレーション','beeats.co.jp':'株式会社ビーツ',
 'fuji-cc.co.jp':'株式会社フジ・クリエイティブセンター','frame-d.jp':'株式会社フレーム','printing-shinwa.co.jp':'株式会社伸和',
 'sakabi.co.jp':'株式会社坂本美工','koho-an.com':'株式会社弘報案内広告社','bunposha.co.jp':'株式会社文方社',
 'maikosendai.co.jp':'株式会社毎日広告社仙台','hakubado.co.jp':'白馬堂印刷株式会社','kanda-p.co.jp':'神田印刷工業株式会社',
 'shobunsha.net':'祥文社印刷株式会社','senko-edit.com':'株式会社千広企画','fujinaript.co.jp':'藤成印刷株式会社',
 'n-global.co.jp':'西日本ビジネス印刷株式会社','himeori.jp':'株式会社読宣WEST','daiwa-printing.co.jp':'株式会社大和印刷社',
 'iwanaga-print.com':'株式会社岩永印刷所','daiichiprint.co.jp':'第一印刷株式会社','dai1.com':'第一印刷株式会社',
 'bunshodo-ps.jp':'株式会社文尚堂','arisdesign.wixsite.com':'ARIS DESIGN',
 'buntec.e-shigotonin.net':'株式会社ブンテック','k-koseisha.co.jp':'株式会社広正社','gemgem.jp':'株式会社GEMインターナショナル',
 'sign-saikosha.com':'有限会社彩光社','oginoart.com':'オギノアートデザイン','signskonan.co.jp':'株式会社コーナン',
 'shinyo-f6.com':'シンヨーネオン電気株式会社','lac-kougei.com':'ラック工芸株式会社','legrand.gran-info.com':'株式会社レグランド',
 'ad-board.co.jp':'中央アドボード株式会社','kubokobo.jp':'久保工房','kan-global.com':'株式会社カン・グローバル',
 'adwork.co.jp':'株式会社アドワーク','dai-art.jp':'有限会社ダイ・アート','daido-k.jp':'大同工芸株式会社',
 'owariokugai.co.jp':'尾張屋外広告株式会社','mediaroad.co.jp':'株式会社メディアロード','nakano-kanban.com':'中野看板',
 'asahino.co.jp':'株式会社旭商会','kyodo-n.net':'有限会社共同ネオン電機','401net.com':'有限会社田口工芸',
 'tomiyan.co.jp':'有限会社トミヤ','daisho-print.co.jp':'有限会社大昌印刷所','valeur.co.jp':'有限会社工房バルール',
 'nisshin-design.co.jp':'有限会社日新','kimura-kanban.co.jp':'木村看板株式会社','omino.ne.jp':'株式会社小美野',
 't-systec.com':'株式会社東京システック','enisic.co.jp':'株式会社エニシック','eishinkoho.co.jp':'株式会社栄伸',
 'k-neon.co.jp':'株式会社KAKIMOTO','goodcolor.fun':'株式会社グッドカラー','3aaa.co.jp':'株式会社サンエイ企画',
 'hiroshima-think-tank.co.jp':'株式会社シンク・タンク','tokidesign.co.jp':'株式会社トキ・デザイン','tohshin-sign.co.jp':'株式会社東進',
 'sign-marusen.com':'有限会社マルセン','sign-aiwa.com':'アイワ工芸株式会社','ad-bikoh.jp':'株式会社アド美廣',
 'ako-design.com':'アコーデザイン','bicosha.co.jp':'株式会社美工社','ad-waizu.jp':'株式会社アド・ワイズ',
 'chunichi-koh.co.jp':'株式会社中日広告社','meiki-tsushinsha.co.jp':'株式会社名機通信社','totsu-ag.com':'株式会社東通エージェンシー',
 'senkosya.net':'株式会社専広社','good-s.co.jp':'株式会社グッドエス','k-kazusa.co.jp':'株式会社上総',
 'kubota-sign.flips.jp':'有限会社クボタ看板','ee-central.jp':'株式会社セントラル','sankobo.jp':'有限会社サン工房',
 'gakunantoso.co.jp':'岳南塗装デザイン','akatsukakougei.jp':'有限会社赤塚工芸','gooro.jp':'株式会社グーロクリエイト',
 'ad-pln.co.jp':'株式会社アド・プランニング','neon30.jp':'株式会社ネオンサーティ','decosign-tohbi.co.jp':'株式会社東美',
 'sign-fukushima.com':'福島工芸','moritake.ne.jp':'モリタケ工芸株式会社','sign-takamori.com':'高森看板製作所',
 'oz-magic.co.jp':'株式会社オズ','peapdesign.com':'PEAP DESIGN','menkoi-ep.jp':'株式会社めんこいエンタープライズ',
 'tochicomi.com':'株式会社栃木コミュニティメディア','naturalcom.jp':'ナチュラルコム株式会社','senkousya.jp':'宣工社',
 'writealight.jp':'株式会社ライト・ア・ライト','ucreative.co.jp':'有限会社ユークリエイティブ','ad-brain.co.jp':'株式会社アドブレイン',
 'jamrock.co.jp':'株式会社JAMROCK'
}
with open(a.input,encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
out=[]; seen=set()
for r in rows:
 h=host(r['url'])
 if h in REJECT or h in seen: continue
 name=NAMES.get(h,r['company_name']).strip()
 if len(name)<3 or len(name)>40 or name in {'株式会社','有限会社','合同会社'}: continue
 r['company_name']=name; seen.add(h); out.append(r)
with open(a.output,'w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(out)
print({'input':len(rows),'rejected_or_invalid':len(rows)-len(out),'clean':len(out)})
