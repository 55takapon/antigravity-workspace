# iteration-4 確定例転記監査

## 結論

**PASS**

F01/F02修正後を再監査した。登録全文26件、通常router対象母集団25件、A35のpending保持・router除外、W10の条件付き参照、G06の工程制御分離が整合した。A35は未承認のまま通常生成から確実に除外されるため、安全上の未解決failではない。

候補版のファイルは編集していない。

## 監査対象

- `iteration-4/candidates/batch-01.md` 〜 `batch-06.md`
- 現行 `examples/good-output.md` の既存3例: `C01-A35`、`C02-UR04`、`C03-UR05`
- `iteration-4/design/case-corpus-27.md`
- `iteration-4/candidate-skill/gbp-review-reply/examples/case-index.md`
- `iteration-4/candidate-skill/gbp-review-reply/examples/cases/*.md`
- candidate `SKILL.md` の参照手順

## 判定一覧

| 確認項目 | 判定 | 事実 |
|:---|:---:|:---|
| 良好全文例26件 | PASS | category 5ファイルに26件。内訳は既存3件、新規23件 |
| 新規23件の完全一致 | PASS | batch-01〜05の各4件とbatch-06の3件をID単位で比較。欠落0、本文差分0 |
| 既存3件の完全一致 | PASS | candidateの3返信全文が現行 `good-output.md` に完全一致 |
| 状態・適用条件・不適用条件 | PASS | 26節すべてに3項目あり。欠落0 |
| A35の保持と除外 | PASS | 本文は登録に保持。`active-conditional-proposed`、`router-eligible: false`、ユーザー確認まで参照禁止がcategory・index・SKILLで一致 |
| W10の完全一致と条件付き状態 | PASS | batch-02確定全文とcandidate本文が完全一致。`active-conditional`で、4条件成立時だけrouter対象。1条件でも不明ならW15-SC/G05-MPへ退避 |
| G06-RPの分離 | PASS | category全文例に含まれず、`case-index.md` の `eval-only-workflow-control` にのみ登録 |
| 外部元返信 | PASS | 新規23件はユーザー確定batchと完全一致。外部記事は入力シナリオの要約元としてのみ表示され、元返信のactive転記0 |
| 候補・未承認の通常参照 | PASS | 未確認candidate 0。A35 pending 1件は登録保持のみでrouter対象外。未承認本文が通常生成へ入る経路0 |
| クライアント固有情報 | PASS | active corpusとindexで、鰻の神楽、京都店、京都駅、固有メニュー、client slugのヒット0。A35も匿名化済み |
| 重複全文 | PASS | 26返信を全文単位で集計し、重複グループ0 |
| case-index到達性 | PASS | category側26 IDとindex側26 IDが一致。欠落0、余分0、5リンクすべて実在。A35はindexから本文へ到達可能だがrouter eligibilityで除外 |
| 通常読込上限 | PASS | `case-index.md` とcandidate `SKILL.md` が1カテゴリ選択後に最大2〜3件だけ読むよう指定。26件全読込を禁止 |

## 件数検算

| 区分 | 件数 |
|:---|---:|
| `confirmed-good` | 24 |
| `active-conditional`（W10） | 1 |
| `active-conditional-proposed` | 1 |
| index登録全文 | 26 |
| 通常router対象母集団 | 25 |
| router除外pending（A35） | 1 |
| `eval-only-workflow-control` | 1 |
| 合計ケース | 27 |

category別件数は `star-only` 5、`positive-short` 2、`positive-detailed` 5、`mixed-low-rating` 7、`high-risk-special` 7で、合計26件。G06-RPは別枠の工程制御1件である。

## 完全一致の範囲

- batch-01: W13-SH、W14-SF、W01-HF、W03-HS
- batch-02: W02-HB、W10-HD、W11-HO、W12-HC
- batch-03: W04-LW、W05-LA、W06-LB、W07-LF
- batch-04: W08-LP、W09-LH、W16-SL、W17-SO
- batch-05: W15-SC、G01-MX、G02-B2B、G07-KL
- batch-06: G03-FL、G04-DP、G05-MP

G03-FLは公開返信となる英語全文が完全一致した。batch内の日本語は参考訳であり、通常出力へ自動併記しない条件どおりactive全文例には含めていない。

## 再監査結果

`C01-A35` の正本状態差は、本文を消さずにcandidate runtimeから隔離する形で解消された。

- 現行 `approved-replies.md`: `active`
- 現行 `good-output.md`: `active-conditional`
- candidate `positive-detailed.md`: `active-conditional-proposed`、ユーザー確認前を不適用条件へ明記
- candidate `case-index.md`: `router-eligible: false`
- candidate `SKILL.md`: A35をユーザー確認まで参照しない

A35を将来通常参照へ戻すには別途ユーザー確認が必要だが、現candidateの通常生成には入らない。W10は本文を変更せず、4条件付きの`active-conditional`へ限定された。転記監査上の未解決failは0件である。
