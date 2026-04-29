---
description: GoogleマップURLからレビュー口コミを抽出し、プロマーケター視点で分析する
---

# Google Maps レビュー口コミ分析ワークフロー

// turbo-all

## 手順

1. ユーザーからGoogleマップのURLを受け取る

2. SKILL.mdを確認する
```powershell
cat "C:\Users\hangy\.gemini\antigravity\scratch\.agents\skills\google_maps_review_analyzer\SKILL.md"
```

3. レビューを抽出する
```powershell
python "C:\Users\hangy\.gemini\antigravity\scratch\.agents\skills\google_maps_review_analyzer\scripts\extract_reviews.py" "{URL}" --output reviews_temp.json
```

4. 抽出結果を確認する
```powershell
python -c "import json; d=json.load(open('reviews_temp.json','r',encoding='utf-8')); print(f'抽出件数: {len(d.get(\"reviews\", []))}件')"
```

5. レビューを分析する
```powershell
python "C:\Users\hangy\.gemini\antigravity\scratch\.agents\skills\google_maps_review_analyzer\scripts\analyze_reviews.py" reviews_temp.json --output review_report.md --json-output review_data.json
```

6. 分析レポートをユーザーに提示する
   - `review_report.md` の内容を表示
   - 追加の深掘り分析の要否を確認
