import json,csv,sys
from pathlib import Path
BASE=Path(__file__).parent
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
from prepare_pool import dk
holds={
'fa-japan.jp':'現在のサービス説明は採用・求人向けの集客支援。店舗への来店販促支援は確認できず保留。',
'nicco-kk.co.jp':'公式運営法人は株式会社日広。入力の長野造形株式会社と一致せず、別法人のサービスを根拠にしない。',
'takmy.co.jp':'学会・国際会議・展示会の運営が中心。現在確認できた取引先と提供内容から店舗集客ハブの適合根拠が不足。',
'ado-agent.com':'現在の説明はIT企業・外資系企業中心の販促。店舗型顧客への提案接点を確認できず保留。',
'f-cr.co.jp':'印刷会社向け製版・印刷工程の受託が主な根拠。店舗顧客に販促提案する商流を確認できず保留。'}
corrections={
'kyono-kougei.com':('https://www.kyono-kougei.com/about-us','公式会社案内で、店舗・企業の看板を企画・デザイン・設計・製作し、顧客の繁栄を支援する事業を確認。店舗の既存顧客へのMEO追加提案候補。外注意向・採算は未確認。'),
'heihan.co.jp':('https://www.heihan.co.jp/service/','公式サービスページで、Web制作・Webマーケティング・広告戦略と、企画から管理保守までの提供を確認。顧客の集客支援にMEOを追加する提案候補。外注意向・採算は未確認。'),
'jalbrand.co.jp':('https://www.jalbrand.co.jp/product/','公式商品・サービスページで、航空会社以外の企業へのコミュニケーションツール提供と広告主・代理店向け媒体提案を確認。MEOの追加提案候補だが、Web実績はJALグループ中心で店舗顧客の有無・外注意向・採算は未確認。'),
'iandk.co.jp':('https://www.iandk.co.jp/','公式トップで、現行のルートサンプリング、キャンプ場・夏祭り等の販促相談、配信広告出稿の対応を確認。販促支援にMEOを追加する提案候補。過去のMEO開始告知だけで現在の外注需要は判断せず、外注意向・採算は未確認。'),
'tmuomachi.jp':('https://tmuomachi.jp/','公式トップで魚町商店街の組合が共同出資する会社であること、商店街の懸垂幕・横断幕・袖看板の広告募集を確認。地域店舗への接点を持つMEO追加提案候補。ホームページ制作は設立目的のため現行受注実績とは扱わず、外注意向・採算は未確認。'),
'japanissimo.jp':('https://japanissimo.jp/','公式ページで広告クリエーティブ・媒体プランニングを提供し、医療機関との関係を掲げる事業を確認。顧客向けMEO追加提案候補。取引件数・外注意向・採算は未確認。')}
rows=list(csv.DictReader((BASE/'review_batch_005.csv').open(encoding='utf-8-sig')))
out={}
for r in rows:
 d=dk(r['url'])
 if d in holds:out[d]={'verdict':'HOLD','reason':holds[d],'reviewer':'primary'}
 elif d in corrections:
  u,w=corrections[d];out[d]={'verdict':'CORRECT_THEN_ACCEPT','reason':'引用の見出し・過去情報を現在の事業説明に差替え。','why_fit':w,'evidence_urls':[u],'hub_type':'ADD_ON_HUB','reviewer':'primary'}
 else:out[d]={'verdict':'ACCEPT','reason':'確認済み公式ページの引用を個別に読み、現在の顧客向け制作・広告・販促サービスの説明であることを確認。外注意向・継続契約・採算は推定せず未確認とする。','reviewer':'primary'}
p=BASE/'semantic_review_batch005.json'
if p.exists():raise SystemExit('do not overwrite')
p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('reviewed',len(out),'holds',len(holds),'corrections',len(corrections))
