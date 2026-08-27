import csv,json,sys
from pathlib import Path
BASE=Path(__file__).parent
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
from prepare_pool import dk
groups=[
([2,13,15,120,134,136],'現在の引用は求人・採用の支援。店舗来店・販売促進の提供実態を別途確認するまで保留。'),
([9,14,28,42,56],'引用は取引先・顧客コメント・窓口分類であり、自社の具体的な販促サービスの説明として不足。'),
([63,84,85,88],'経営方針・過去の沿革・職業体験の引用で、現在の顧客向けサービスを説明する根拠に差替えるまで保留。'),
([86,97,116],'入力法人と現在の運営法人・サービス提供主体の一致に疑義があるため保留。'),
([1,12,17,37,48,49,68,70,75,106,112,114,123,140],'確認できた説明では工業製造・印刷工程・ソフト提供・通販や特定業界対応が中心。店舗集客ハブとしての商流を追加確認するまで保留。'),
([20,22,27,132,137],'見出し・仕様・フッターだけの根拠では、現在の顧客向け販促支援の具体性が不足するため保留。'),
([139],'ホームページ作成の引用はJimdoの定型文で、会社自身の提供サービスではない。')]
holds={i:reason for indices,reason in groups for i in indices}
rows=list(csv.DictReader((BASE/'review_batch_008.csv').open(encoding='utf-8-sig')))
assert len(rows)==142
out={dk(r['url']):{'verdict':'HOLD' if i in holds else 'ACCEPT','reason':holds.get(i,'公式ページの引用を個別に読み、現在の顧客向け広告・制作・販促支援の説明と確認。外注意向・継続契約・再販採算は保証せず未確認とする。'),'reviewer':'primary'} for i,r in enumerate(rows)}
p=BASE/'semantic_review_batch008.json'
if p.exists():raise SystemExit('do not overwrite')
p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('reviewed',len(out),'held',len(holds),'accepted',len(out)-len(holds))
