# proposal-writing fact guard report

報告対象の事実は、実ファイルとコマンド出力で確認した内容に限定した。

| 確認項目 | 結果 | 根拠 |
|:--|:--|:--|
| 対象スキル | `proposal-writing` | `SKILL.md` frontmatter |
| 対象範囲 | Web制作会社向けのみ | `SKILL.md` と `references/01-target-web-production-company.md` |
| 外した条件 | 店舗型事業者の制作実績確認済み、実績掲載ありを必須にしない | `references/01-target-web-production-company.md` |
| 維持した対象外 | Webマーケティング会社、広告代理店、その他提案先 | `SKILL.md` 禁止事項、`references/01-target-web-production-company.md` |
| 個社調査・カスタマイズ | 引き続き対象外 | `SKILL.md` 禁止事項 |
| 評価結果 | 改善版 100.0%、旧版 28.571%、回帰なし | `benchmark.json` |
| ゲート | allowed true | `auto_fix_gate.json` |
| Skill Checker | 63項目、pass 59 / fail 0 / n/a 4 | `skill-checker-report.md` |

未確認事項:

- `python3` コマンドは WindowsApps の `python3.exe` 起動失敗により使えなかったため、同一スクリプトを `python` で実行した。
