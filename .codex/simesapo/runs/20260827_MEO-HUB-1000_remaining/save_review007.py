import csv,json,sys
from pathlib import Path
BASE=Path(__file__).parent
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
from prepare_pool import dk
groups=[
([0,36,116,118,129,198],'現在の根拠は求人・採用支援。店舗の来店販促支援の根拠を確認できるまで保留。'),
([15],'ホームページ作成サービスの引用はサイト作成ツールの定型案内で、当該会社の提供サービスではない。'),
([27,34,37,75,107,112,199],'引用は職員紹介・過去の沿革・他社紹介・自社活動等。現在の顧客向けサービスを示す独立した根拠へ差替えるまで保留。'),
([45,46,47,55,62,71,78,84,89,91,121],'グループ会社・持株会社の事業を混同する可能性があり、入力法人自身の提供サービスと商流を確定するまで保留。'),
([50,51,81,87,92,104,108,123,128,145,165,171,174,190],'引用は取引先・加盟団体・他社の記事で、自社の現在の販促提供内容を示す根拠として不足。'),
([83,85,88,90],'放送方針・サイト権利・経営方針の記述を、顧客向けサービスと判定しない。'),
([6,16,31,33,39,53,60,64,69,72,73,76,77,86,93,95,96,99,119,138,147,168,175,185],'確認範囲では印刷工程・設備・情報・媒体・ソフト・特定業界支援が中心。店舗顧客へ販促提案する商流の根拠が不足するため保留。'),
([56,102,133,134,140,141,143,189],'見出し・一般論・解説のみの引用では提供実態の根拠が不足。現在の具体的な顧客向けサービスを追加確認するまで保留。')]
holds={i:reason for indices,reason in groups for i in indices}
rows=list(csv.DictReader((BASE/'review_batch_007.csv').open(encoding='utf-8-sig')))
assert len(rows)==200
out={}
for i,r in enumerate(rows):
 out[dk(r['url'])]={'verdict':'HOLD' if i in holds else 'ACCEPT','reason':holds.get(i,'公式ページの引用を個別確認し、顧客向け制作・広告・販促サービスの説明と判断。外注意向・再販採算・継続関係は未確認であり保証しない。'),'reviewer':'primary'}
p=BASE/'semantic_review_batch007.json'
if p.exists():raise SystemExit('do not overwrite')
p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('reviewed',len(out),'held',len(holds),'accepted',len(out)-len(holds))
