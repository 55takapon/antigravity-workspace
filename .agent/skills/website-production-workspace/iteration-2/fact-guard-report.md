# Fact Guard 代替監査

独立した `fact-guard` スキルは環境内で確認できないため、実ファイルと実行結果を照合した。

| 報告予定の主張 | 根拠 | 判定 |
|:--|:--|:--|
| 指定iframeをスキルへ登録 | `references/03-site-design.md` のsrc・属性全文 | pass |
| デモサイトで標準実装 | `SKILL.md` ステップ4、エッジケース、自己完了確認 | pass |
| 仮マップの誤認を防止 | デモ注記と公開前差し替え注記を必須化 | pass |
| 旧版比較で改善 | `benchmark.json`: 0% → 100% | pass |
| 回帰なし | `auto_fix_gate.json`: regression/output collapseともfalse | pass |
| 実サイト2件へ反映 | staged HTML/CSSのiframe属性とレスポンシブ検証結果 | pass |

総合判定: pass
