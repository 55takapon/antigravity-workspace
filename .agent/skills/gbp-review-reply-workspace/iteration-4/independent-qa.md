# iteration-4 candidate-skill 独立QA

確認日: 2026-07-22  
比較対象:

- 旧版: `skill-snapshot/iteration-4/gbp-review-reply`
- 候補版: `iteration-4/candidate-skill/gbp-review-reply`

## 結論

**本番反映ゲート: FAIL（未解決2件）**

設計の主目的である、K1〜K6の保持、禁止中心runtimeの縮小、軽量router、通常1案、返信済み生成停止は実現している。一方、通常生成が到達できる例レジストリに、状態不一致1件と安全核K2との内容衝突1件が残る。候補版の作業継続は可能だが、このまま本番へ反映してはならない。

## 未解決事項

### F01 — C01-A35の状態が正本間で不一致

判定: **FAIL / 本番前ブロッカー**

- `examples/approved-replies.md`: `active`
- `examples/case-index.md`: `active-conditional-proposed`
- `examples/cases/positive-detailed.md`: `active-conditional-proposed`
- candidate changelog / feedback-loop: 本番状態変更はユーザー確認待ち

本文のposted事実と匿名化は保持されている。問題は本文ではなく、通常生成で参照できる状態の正本が一致していない点である。

**独立判定:** `active-conditional-proposed`のままcandidateに保持すること自体は条件付き許容。ただし、本番適用前にユーザー判断を得て、`approved-replies.md`、`case-index.md`、`positive-detailed.md`の状態を同じ確定値へ同期する必要がある。未確認のままならA35を通常routerから外す。したがって本番前ブロッカーである。

### F02 — W10-HDがK2と自身の不適用条件に衝突

判定: **FAIL / 本番前ブロッカー**

W10-HDの返信には次がある。

> これからも落ち着いて治療をうけていただけるよう努めてまいります。

一方、共通安全核K2は診療・受診関係の反復を禁止し、W10-HD自身の不適用条件も「治療効果、受診関係を追認する」を挙げる。事業者側から「治療を受けていただけるよう」と返す例を`confirmed-good`として通常routerへ置くと、安全核優先の指示があっても模倣時の衝突源になる。

ユーザー確定稿である事実は保持すべきだが、承認済みであることと安全核に適合する現役模倣元であることは別である。全文を無断修正せず、次のいずれかをユーザー判断で行う必要がある。

1. 現行全文をhistorical / eval-onlyへ移し、通常routerから外す。
2. K2に適合する別全文をユーザーが確定した後で差し替える。
3. 医療でこの一般的な「治療」言及を許容するなら、K2とW10の不適用条件を矛盾なく限定し、公開安全性を再評価する。

## 重点項目の判定

| 項目 | 判定 | 事実 |
|:---|:---:|:---|
| K1〜K6保持 | PASS | `SKILL.md`と`reply-rules.md`に同じ6核があり、profile・例より上位と明記 |
| 例が安全核を上書きしない構造 | PASS | 衝突時はK1〜K6優先と3か所で明記。ただしW10の内容衝突はF02として別途FAIL |
| 過剰禁止のruntime削減 | PASS | 旧詳細列挙をK1〜K6、最小分岐、例routerへ縮小。`quality-boundaries.md`は通常必読から除外 |
| router最大2〜3例 | PASS | 1カテゴリ選択後に0〜3件。全26例・複数カテゴリ総当たりを禁止 |
| 通常出力1案 | PASS | 意味差判断またはstaff-sharing未確定時以外は最終返信案1つ |
| staff-sharing例外 | PASS | `unknown`または案件判断が分かれる時だけ2案。選択後profile保存、通常1案へ戻す。実在・実行意向・時制・単独事業者・privacy条件あり |
| 4スタイル回帰 | PASS | runtime・active例・出力に0件。語のヒットはappend-only changelogの過去履歴だけ |
| client固有情報のactive混入 | PASS | active corpusとindexに鰻の神楽、京都店、京都駅、client slug、固有メニューのヒット0。既存changelogの過去記録は履歴扱い |
| G06-RP no-output | PASS | 全文例26件から除外し、`eval-only-workflow-control`として新規返信生成を停止 |
| A35状態注記 | PASS | posted事実、提案状態、本番前確認要件は明記。ただし状態不一致はF01 |
| changelog append-only | PASS | snapshot本文が候補版の完全な先頭部分として残り、iteration-4節だけを末尾追記 |
| 既存履歴保持 | PASS | approved-repliesのM1〜M4、F1〜F5、P1〜P3本文と状態履歴を保持。historical / deprecatedを通常生成から除外 |
| 新規全文例の転記 | PASS | 転記監査上、新規23件の本文差分0。G03の日本語は参考訳で通常出力に含めない |
| 例件数・索引到達性 | PASS | 5カテゴリ計26例、G06工程制御1件。indexとカテゴリID一致、リンク実在、全文重複0 |

## snapshotとの差分レビュー

候補版は14ファイル。snapshotの8ファイルに対し、共通8ファイルを更新し、router用6ファイルを追加した。

追加:

- `examples/case-index.md`
- `examples/cases/star-only.md`
- `examples/cases/positive-short.md`
- `examples/cases/positive-detailed.md`
- `examples/cases/mixed-low-rating.md`
- `examples/cases/high-risk-special.md`

更新:

- `SKILL.md`: 5工程を維持し、K1〜K6と軽量routerへ変更
- `references/reply-rules.md`: 過剰な個別禁止をruntimeから外し、安全核・最小分岐へ縮小
- `references/evidence.md`: 根拠の所在と適用限界へ圧縮
- `references/feedback-loop.md`: 通常生成から分離し、状態ガバナンスとE/C/I/Uを保持
- `references/changelog.md`: iteration-4候補履歴を末尾追記
- `examples/good-output.md`: 出力境界とrouter案内へ変更
- `examples/approved-replies.md`: 既存履歴本文を保持し、新規23件は正本への索引だけを追加
- `examples/quality-boundaries.md`: snapshotと同一

## 合格後に再確認する項目

F01とF02を解消した後、次だけを再検査する。

1. A35の状態が3正本で一致し、未承認状態が通常routerへ残っていない。
2. W10がK2および自身の適用・不適用条件と衝突しない。
3. 26例、5カテゴリ、G06工程制御1件の件数とindex到達性が維持されている。
4. 4スタイル、client固有情報、二重返信がruntimeへ回帰していない。

skill-checker本実行は本書の範囲外であり、未実施。

## F01/F02修正後の再QA

再確認日: 2026-07-22  
再QA結論: **PASS（未解決fail 0件）**

この節は、上記の初回FAIL判定を修正後の実ファイルで再評価した最終判定である。本番反映可否は、後段のskill-checkerおよび統括ゲートを別途満たすことを前提とする。

### F01再検査 — A35

判定: **解消 / PASS**

- 既存`approved-replies.md`の`active`は、posted済み履歴のsource stateとして本文とともに保持されている。
- candidate routerでは`active-conditional-proposed / router-eligible: false`へ責務分離されている。
- `SKILL.md`、`reply-rules.md`、`good-output.md`、`case-index.md`、`positive-detailed.md`の全てが、ユーザー確認までA35を通常参照しないと明記している。
- A35は登録・監査用本文として残るが、通常routerの選択対象母集団25件には含まれない。未承認状態を通常生成へ昇格する経路はない。

既存履歴状態とcandidate runtime状態を同一値へ改変せず、用途別に分離した修正は妥当である。将来routerへ戻す場合だけ、別途ユーザー確認が必要。

### F02再検査 — W10

判定: **解消 / PASS**

- ユーザー確定済み返信本文は無改変で、batch-02と完全一致している。
- candidate router状態は`active-conditional`であり、次の4条件を全て要求する。
  1. 口コミ本人が治療一般を公開文に明記している。
  2. client profileが一般的な治療関係への言及を明示許可している。
  3. 法規・privacy上の公開可否を確認済みである。
  4. 診断、処置、症状、効果、具体的受診情報を返信で反復しない。
- 条件が1つでも不明ならW10を参照せず、W15-SCまたはG05-MP等の安全側の例へfallbackする。
- K2、業種境界、SKILL、case-index、W10の適用・不適用条件が同じ限定条件で同期している。

一般的な「治療」言及だけを狭い例外とし、診断・処置・症状・効果の反復を許可していない。profile未確認・法規privacy未確認時も参照不可であり、K2を空文化する広い例外ではない。

### 件数・回帰

| 項目 | 判定 | 結果 |
|:---|:---:|:---|
| 登録全文例 | PASS | 26件。category別5 + 2 + 5 + 7 + 7 |
| 通常router対象母集団 | PASS | 25件。A35を除外 |
| W10条件付き参照 | PASS | 25件内だが4条件成立時だけeligible |
| G06工程制御 | PASS | 全文例外の`eval-only-workflow-control` 1件 |
| 合計ケース | PASS | 26全文 + G06 = 27 |
| 本文重複・索引不一致 | PASS | 重複0、indexとcategoryの欠落・余分0 |
| 新しい状態矛盾 | PASS | source履歴、candidate登録状態、router eligibilityを明示分離 |
| 本番先行変更 | PASS | 本番8ファイルとiteration-4 snapshotのSHA-256差分0 |

**最終独立QA判定: PASS。残存fail 0件。**
