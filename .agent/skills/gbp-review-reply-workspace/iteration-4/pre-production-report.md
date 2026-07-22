# iteration-4 本番反映前レポート

## 1. 現行正本

- 本番正本: `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply`
- 更新候補: `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply-workspace\iteration-4\candidate-skill\gbp-review-reply`
- 更新前snapshot: `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply-workspace\skill-snapshot\iteration-4\gbp-review-reply`
- 現時点で本番は8ファイル、候補版は14ファイル。本番反映は未実施。

## 2. 変更しなかった完了事項

- 4スタイル廃止、通常出力の最終返信案限定、E/C/I/U、SEO・販促の既定OFF、強制類語化廃止等の完了済み事項をやり直していない。
- iteration-1〜3、iteration-4 snapshot、`evals/evals.json`、クライアント資料、外部Excelを変更していない。
- 本番スキルとクライアントprofile/logは未変更。
- 別名スキル、VERSION、MANIFEST、deployment、専用リンターは追加していない。

## 3. 確定例反映

- ユーザー確定済み全文例26件を、`star-only 5 / positive-short 2 / positive-detailed 5 / mixed-low-rating 7 / high-risk-special 7`へ整理した。
- 投稿済みA35は元入力・元返信をhistorical sourceとして別保持し、runtimeでは同じ入力に対するユーザー確定稿U-R06へ置換した。runtime全文例は26件を維持し、他25件の本文は変更していない。
- 外部記事は入力シナリオと検査観点に限定し、記事の返信全文をapprovedへ自動昇格していない。
- 通常生成は1カテゴリ、最大2〜3例だけを参照し、26例の一括読込を禁止した。

## 4. 候補スキル変更

- 実行順を`K1〜K6最小安全核 → 軽量router → 該当例最大3件 → 全文検査`へ整理。
- 5工程に入出力・完了条件・明示ゲートを設け、5件のエッジケース表と簡潔な禁止事項節を追加。
- 例ファイル5件を`examples/`直下へ配置し、2階層目ファイルとリンク切れを0件にした。
- 通常は投稿可能な最終返信案1つだけを出し、返信済みは生成停止。staff-sharingが未確定で判断が分かれる時だけ確認用2案を許可。
- 高評価の自然な歓迎、本文なし、低評価の謝意・確認行動、高リスクの公開範囲を、確認済み全文例とprofile条件で選ぶ構造へ変更。
- 誤配置されたflat `with_skill/response.md`は0件。正規`outputs/response.md`とgradingは34/34存在。

## 5. 状態・条件（A35 / W10 / W11 / G06）

| ID | 現在の扱い |
|:---|:---|
| A35 | posted済み履歴本文、元入力、source `active`をhistorical sourceとして保持。runtimeでは参照しない |
| U-R06 | 2026-07-22ユーザー確定の`confirmed-good`。A35と同じ入力について、明記された雰囲気・食事・接客だけを扱い、接客評価を「励みになります」へ接続して歓迎で完結。未投稿の品質例 |
| W10 | 確定全文を改変せず`confirmed-good`として通常参照。口コミ本人が書いた一般語「治療」の範囲に留め、痛み・効果・具体的処置を拾わず、説明と落ち着いて受けられる環境へ焦点を絞る。口コミにない関係追加と症状・効果・施術内容の反復は通常の不適用条件 |
| W11 | 確定全文を改変せず`confirmed-good`として通常参照。「かなり軽くなった」「一度の施術」「肩」を拾わず、本人が明記した継続意思と感謝・一般的歓迎へ焦点を絞る。口コミにない関係追加と症状・効果・施術内容の反復は通常の不適用条件 |
| G06-RP | `eval-only-workflow-control`。返信済みで修正・追記依頼がない時は新規返信を生成しない。全文例26件には含めない |

## 6. 旧版比較

| 項目 | 旧版 | 最終候補版 |
|:---|---:|---:|
| 評価ケース | 34 | 34 |
| ケースpass | 32/34 | 34/34 |
| assertions pass | 134/136 | 136/136 |
| pass率 | 98.529% | 100.000% |
| critical failure | 0 | 0 |

- 改善幅は+1.471ポイント。regression=false、output collapse=false。
- `auto_fix_gate.json`は`allowed: true`。
- timing/tokenは全件`measurement_status: unavailable_in_subagent_interface`かつ計測値`null`。benchmark表示上の0は実測値ではないため、速度・トークン改善は主張しない。

## 7. 独立QA・skill-checker・Fact Guard

- 独立QA最終判定: PASS、残存fail 0件。
- skill-checker第2回: **54 pass / 0 fail / 9 n/a（全63項目）**。
- Fact Guard最終判定: PASS、未解決0件。
- 最終評価: candidate 34/34、136/136 assertions、critical 0。
- runtime全文例26件、A35の通常参照0、U-R06の`confirmed-good`通常参照、W10/W11の`confirmed-good`通常参照への同期、flat誤配置0を確認。A35の投稿済み本文はhistorical sourceに無改変で保持する。
- 2026-07-22 W10/W11正規化追補後は、確定全文26件hash不変、Markdownリンク切れ0、現役状態同期を確認した。上記34ケース・skill-checker・独立QAの数値は正規化前の最終実行値であり、正規化後の再実行は独立QA担当の範囲とする。
- 2026-07-22 A35確定追補では、A35元入力・元返信のhistorical source一致、U-R06確定稿のexact hash一致、他25件本文差分0、runtime 26件、Markdownリンク切れ0を確認した。この追補後の独立QA・skill-checkerは未実行である。

## 8. 本番反映予定14ファイル

1. `SKILL.md`
2. `references/reply-rules.md`
3. `references/evidence.md`
4. `references/feedback-loop.md`
5. `references/changelog.md`
6. `examples/approved-replies.md`
7. `examples/case-index.md`
8. `examples/good-output.md`
9. `examples/quality-boundaries.md`
10. `examples/star-only.md`
11. `examples/positive-short.md`
12. `examples/positive-detailed.md`
13. `examples/mixed-low-rating.md`
14. `examples/high-risk-special.md`

## 9. 本番未変更の証拠

- 本番8ファイルとiteration-4 snapshot 8ファイルを、相対パス別SHA-256で再比較した。
- ファイル不足0、余分0、hash差分0。
- したがって本番は、iteration-4開始時点のsnapshotから変更されていない。

## 10. ユーザー確認事項

1. **本番反映**: 上記14ファイルを本番へ反映してよいか、ユーザー承認が必要。

## 11. ロールバック

- 現在の戻し元は`skill-snapshot/iteration-4/gbp-review-reply`で、本番とのSHA-256差分は0。
- 本番適用直前に本番8ファイルの追加バックアップとhash一覧を保存する。
- 復元時はsnapshotまたは直前バックアップの8ファイルを戻し、iteration-4で新設する次の6ファイルだけを対象確認後に除く。
  - `examples/case-index.md`
  - `examples/star-only.md`
  - `examples/positive-short.md`
  - `examples/positive-detailed.md`
  - `examples/mixed-low-rating.md`
  - `examples/high-risk-special.md`
- iteration-1〜3、クライアント資料、他スキルはロールバック対象に含めない。
