import csv,json,subprocess,sys
from pathlib import Path

base=Path(__file__).parent
report=json.loads((base/'publication_report.json').read_text(encoding='utf-8'))
assert report['today_added_total']==1000 and report['total']==7000
assert report['candidate_readback_exact'] and report['exclusion_readback_exact']
after=json.loads((base/'target_after.json').read_text(encoding='utf-8'))
assert len(after)==7001
today=after[6001:7001]
assert len(today)==1000
with (base/'today_added_1000.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(after[0]);writer.writerows(today)
kept=[dict(zip(after[0],row)) for row in today]
(base/'today_verified_kept.json').write_text(json.dumps(kept,ensure_ascii=False),encoding='utf-8')
helper=Path(r'C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\.claude\skills\001-list-extract\scripts\write_list_csv.py')
subprocess.run([sys.executable,str(helper),str(base/'today_verified_kept.json'),str(base/'today_added_1000_standard.csv')],check=True)
first=json.loads((base.parent/'20260827_MEO-HUB-1000'/'publication_report.json').read_text(encoding='utf-8'))
ex=first['recheck_added']+report['recheck_added']
text=f'''# 2026年8月27日 MEOハブ候補 追加結果

本日1,000社を追加（先行168社＋今回832社）。累計7,000社。

- 本日の追加範囲：MEOハブ候補 A6002:O7001
- 会社名・ドメイン・電話番号で既存10タブと重複照合。
- 公式サイト上の会社・現行サービス・営業適合の根拠・連絡方法を確認。
- 外注意向、再販の承諾、月額15,000円での採算、受注可能性は未確認。営業仮説と確認済み事実を区別。
- 住所は公式サイトで一致しないものを空欄化。問い合わせ制限があるものは除外・要再確認へ記録し、手動確認が必要な候補は区別。
- 除外・要再確認リストへ本日{ex:,}件追加（先行{first['recheck_added']:,}件＋今回{report['recheck_added']:,}件）。再利用時は理由と再確認条件を確認する。
- 書込み後の読戻しは追加832社の全15列一致、既存候補6,168社の保持を確認。
- 独立確認の結果は同フォルダの監査記録を参照。

## 保存物

- today_added_1000.csv：本日の追加1,000社（本番読戻し由来）
- today_added_1000_standard.csv：001正規出力処理による基本項目・送信区分のCSV
- delivery.csv：今回の832社と判定根拠
- publication_report.json / publication_journal.json：反映範囲・件数・読戻し記録
- semantic_review*.json：意味内容の確認・修正・保留理由
- recheck_registry.csv：今回の除外・再確認対象

営業連絡は実施していません。
'''
(base/'run_summary.md').write_text(text,encoding='utf-8')
print(json.dumps({'today_csv_rows':len(today),'today_recheck_added':ex,'total':report['total']},ensure_ascii=False))
