# 本番適用前 最終Fact Guard

## 最終判定

**PASS（本番適用前ブロッカー0件）**

最終candidate、A35/U-R06独立QA、W10/W11独立QA、公式34評価、Skill Checker、2026-07-22 20:07再生成の`benchmark.json`と`auto_fix_gate.json`を読取専用で照合した。候補内容、評価成果物、時系列、gateの全てが整合している。

## 1. 最終数値

| 項目 | 最終値 | 判定 |
|---|---:|---|
| candidate評価ケース | 34/34 pass | PASS |
| candidate assertions | 136/136 pass | PASS |
| old評価ケース | 32/34 pass | 確認済み |
| old assertions | 134/136 pass | 確認済み |
| critical failure | candidate 0 / old 0 | PASS |
| 正規`outputs/response.md` | 34/34 | PASS |
| `grading.json` | 34/34 | PASS |
| flat誤配置`with_skill/response.md` | 0 | PASS |
| auto-fix gate | `allowed: true` | PASS |
| regression | false | PASS |
| output collapse | false | PASS |

candidateは100%、oldは98.529%、差は+1.471ポイントである。

## 2. Skill Checker

最終Skill Checkerは全63項目を個別判定している。

- pass: 54
- fail: 0
- n/a: 9
- 未解決: 0
- 最終結果: PASS

A35/U-R06反映後の第4回全件検査まで完了し、A35履歴、U-R06出典・本文境界、runtime件数、W10/W11、リンク、例配置、公式評価を再確認している。

## 3. A35 / U-R06

| 確認対象 | 判定 | 結果 |
|---|---|---|
| A35元入力 | PASS | iteration-4 snapshotとhistorical ledgerが文字列完全一致 |
| A35元返信 | PASS | snapshotのユーザー修正後最終文とhistorical ledgerが文字列完全一致 |
| A35 source状態 | PASS | source `active`、posted確認済み（2026-07-14）を保持 |
| A35 runtime | PASS | runtime IDから除外。historical ledgerでのみ保持 |
| U-R06状態 | PASS | 2026-07-22ユーザー確定、`confirmed-good`、通常router参照可 |
| U-R06本文 | PASS | ユーザー確定稿と完全一致 |

A35は削除・改変されず、実行時参照だけをU-R06へ置換している。U-R06の「励みになります」は口コミに明記された接客評価へ接続し、顧客感情を作っていない。「嬉しく思います」は全面禁止ではなく`limited-use`・近接連続非推奨である。

## 4. W10 / W11

- W10-HD: `confirmed-good`、通常router参照可
- W11-HO: `confirmed-good`、通常router参照可
- 両確定本文: ユーザー確定稿から不変
- 旧4条件ゲート/fallback特例: 現行runtimeから撤廃済み。changelogにsuperseded履歴のみ保持
- W10境界: 一般語「治療」は本人が公開した範囲だけ。痛み、効果、診断、処置、症状、具体的受診情報を反復しない
- W11境界: 明記された継続意思だけを扱い、肩、一度の施術、改善効果、症状、施術内容を反復しない

独立QAの同一入力4ケースはいずれもcritical 0。本文に「治療」がない歯科高評価と、継続意思がない整骨院高評価ではW10/W11を適用しない境界も確認済みである。

## 5. runtime corpusと工程制御

- runtime全文例: 26件
- 一意ID: 26件
- 通常router参照候補: 26件
- A35 runtime混入: 0
- U-R06: 1件、参照可
- W10/W11: 各1件、参照可
- G06-RP: `eval-only-workflow-control`、全文例数に含めず、返信済みなら生成停止

U-R06以外の25本文は正本比較で不変。A35/U-R06置換によるW10/W11/G06の回帰もない。

## 6. クライアント固有情報

runtime 5カテゴリと`case-index.md`を、対象クライアント名、京都店、京都駅、client slug、固有メニュー語で検索した。ヒット0件。

共通candidateへ、鰻の神楽固有の店舗名、地域名、商品、SEO、固定フッター、client voiceは混入していない。

## 7. 時系列

| 順序 | 成果物 | 更新時刻 |
|---:|---|---|
| 1 | 最終candidate更新 | 2026-07-22 19:55:49 +09:00 |
| 2 | 公式ID3正規output生成 | 2026-07-22 20:01:53 +09:00 |
| 3 | A35/U-R06独立QA | 2026-07-22 20:03:53 +09:00 |
| 4 | 公式ID3独立grading更新 | 2026-07-22 20:04:57 +09:00 |
| 5 | ID3独立採点報告 | 2026-07-22 20:05:35 +09:00 |
| 6 | 最終Skill Checker | 2026-07-22 20:06:58 +09:00 |
| 7 | `benchmark.json`再生成 | 2026-07-22 20:07:21 +09:00 |
| 8 | `auto_fix_gate.json`更新 | 2026-07-22 20:07:21 +09:00 |

benchmarkとgateは、candidate変更、ID3生成・採点、独立QA、Skill Checkerの全てより後に生成されている。staleな評価値ではない。

## 8. measurement

公式34件の`timing.json`は全て次の状態である。

- measurement status: unavailable系
- total tokens: null
- duration ms: null
- total duration seconds: null

benchmark上のmean token/durationは0表記だが、計測値ではなくplaceholderである。本番報告で「0 tokens」「0秒」「高速化」とは主張しない。

## 9. 本番適用前結論

次を全て確認した。

- candidate 34/34、136/136、critical 0
- old 32/34、134/136
- gate allowed、regressionなし、output collapseなし
- Skill Checker 54 pass / 0 fail / 9 n/a
- A35 historical無改変、U-R06 exact
- W10/W11 confirmed-goodと安全境界の整合
- runtime 26、G06工程制御維持
- 正規output 34、grading 34、flat 0
- client固有混入0
- measurement捏造0

**最終Fact Guard判定はPASS。本番適用前の未解決ブロッカーは0件である。**

この監査ではcandidate、評価出力、grading、benchmark、gateを変更していない。新規作成したのは本報告書だけである。
