# Fact Guard 代替監査

独立した `fact-guard` スキルは環境内で確認できなかったため、実ファイルと実行結果を照合した。

| 報告予定の主張 | 根拠 | 判定 |
|:--|:--|:--|
| 新保存先へ複製済み | source/destinationとも12ファイル | pass |
| 複製内容が同量 | source/destinationとも3,310,113 bytes | pass |
| 旧フォルダを残した | 旧パスと新パスの双方でファイル存在を確認 | pass |
| 今後の既定保存先を設定 | SKILL.md末尾の「既定のプロジェクト保存先」 | pass |
| 明示された別パスを優先 | 同追記ルールと評価ケース2 | pass |
| 旧版比較で改善 | benchmark.json: 75% → 100% | pass |
| 回帰なし | auto_fix_gate.json: regression/output collapseともfalse | pass |

総合判定: pass
