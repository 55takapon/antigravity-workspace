# skill-checker 7 fail最小修正記録

## 対象と変更境界

- 対象: `iteration-4/candidate-skill/gbp-review-reply`
- 本番、`skill-snapshot/iteration-4`、確定例の返信本文は変更していない。
- `skill-checker-report.md`の7 failに対応する構造修正と、Fact Guard暫定指摘のW11参照条件だけを反映した。

## 7 failへの対応

| 修正 | 解消対象 |
|:---|:---|
| 工程2・3・5へ入力と出力を明示 | 内容品質: ワークフロー形式 |
| 5件の短いエッジケース表を追加 | 内容品質: エッジケース、構造1・4、S6 |
| K1〜K6違反、全例総読込、未確定状態記録を禁じる独立節を追加 | 構造1・4、S6 |
| 5カテゴリファイルを`examples/`直下へ移動 | ネスト制限 |
| 全5工程へ明示ゲートを追加 | スキップ防止: ゲート条件 |

## ファイル移動

- `examples/cases/star-only.md` → `examples/star-only.md`
- `examples/cases/positive-short.md` → `examples/positive-short.md`
- `examples/cases/positive-detailed.md` → `examples/positive-detailed.md`
- `examples/cases/mixed-low-rating.md` → `examples/mixed-low-rating.md`
- `examples/cases/high-risk-special.md` → `examples/high-risk-special.md`

`case-index.md`、`reply-rules.md`、`approved-replies.md`の参照先を新配置へ更新した。

## W11 Fact Guard

W11の確定返信本文は変更せず、candidate routerだけを`active-conditional`にした。参照には次の4条件を全て要求する。

1. 口コミ本人が一般的な利用経験を公開文に明記している。
2. client profileが一般的な「ご利用」の歓迎を許可している。
3. 法規・privacy上の公開可否を確認済みである。
4. 症状、効果、施術情報を返信で反復しない。

1つでも不明ならW11を参照せず、W15-SCまたはG05-MP等へfallbackする。状態は`SKILL.md`、`reply-rules.md`、`case-index.md`、`high-risk-special.md`、`good-output.md`、`feedback-loop.md`、`approved-replies.md`で同期した。

## 機械検査

| 検査 | 結果 |
|:---|:---|
| Markdown相対リンク | 24件確認、リンク切れ0 |
| `cases/`残存参照 | 0件 |
| `examples/`配下の2階層目ファイル | 0件 |
| 移動対象ファイル | 5 / 5存在、旧配置ファイル0 |
| 登録全文例ID | 26件、重複0 |
| 工程ゲート | 5工程すべてに存在 |
| エッジケース | 5件 |
| 独立禁止事項 | 3件 |
| W11確定本文SHA-256 | 修正前後とも`C9EF3CA96D3839D1CB45382137B6FF639D905A786FD9A07E12514E5F1E689931` |

W11 hashは`**返信**`直後から次の見出し直前までをUTF-8で抽出し、修正前後を同一手順で比較した。
