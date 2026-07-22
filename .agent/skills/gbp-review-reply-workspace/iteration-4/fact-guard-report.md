# iteration-4 Fact Guard 最終監査

## 判定

**FAIL（未解決1件）**

候補版14ファイル、`benchmark.json`、`auto_fix_gate.json`、`example-transfer-audit.md`、`independent-qa.md`を読取専用で照合した。確定全文の転記、状態管理、A35隔離、W10限定条件、評価数値には問題がない。一方、W11-HOが共通安全核K2と整合しない条件のまま通常routerへ入っているため、本番反映前に修正が必要である。

## 監査結果

| 観点 | 判定 | 根拠 |
|---|---|---|
| 確定26全文の改変・捏造 | PASS | 新規23件をユーザー確定batchと、既存3件をiteration-4 snapshotの`good-output.md`と正規化比較した。新規差分0、既存差分0。登録全文26件、重複0 |
| candidateのapproved誤昇格 | PASS | 未確認candidateの通常参照経路0。新規23件はユーザー確定出典。A35は登録保持のみで`router-eligible: false`。候補全文の自動昇格はない |
| K1〜K6と例文の衝突 | **FAIL** | W11-HOがK2の限定条件を局所条件に持たず、`confirmed-good`として通常routerへ入る。詳細はF01 |
| 未確認の共有・改善・医療/法務事実 | PASS（F01を除く） | K3、staff-sharing条件、業種境界が実在・実行意向・時制・privacy確認を要求する。未確認の責任者、研修、点検、改善済み、契約・案件結果を生成許可する規則は見つからない |
| A35の実行経路除外 | PASS | `active-conditional-proposed`、`router-eligible: false`、ユーザー確認まで参照禁止がSKILL、rules、index、categoryで一致 |
| W10本文と限定条件 | PASS | 確定本文はbatch-02から改変0。口コミ本人の公開記載、profile明示許可、法規・privacy確認、機微情報非反復の4条件がそろう時だけeligible。不明時はW15/G05へfallback |
| 最終報告数値の一致 | PASS | 候補版14ファイル、全文例26件、設定上の通常router母集団25件、G06工程制御1件、総ケース27件。評価34件・136 assertions。旧版134/136=98.529%、候補版136/136=100%、差+1.471pt |

## F01 — W11-HOのK2条件不足

判定: **FAIL / 本番前ブロッカー**

`examples/cases/high-risk-special.md`のW11-HOは、整骨院の口コミに対して次の確定返信を保持している。

> ご感想をお寄せいただき、ありがとうございます。「これからも通いたい」というお言葉が励みになりました。
> またのご利用をお待ちしております。

確定本文そのものは改変されていない。しかし、同例は`confirmed-good`であり、適用条件は「整骨院。肯定的な感想と継続意思だけを安全に扱う」に留まる。`case-index.md`でもW11-HOは無条件の`confirmed-good`である。

これに対して共通安全核K2は、医療・施術領域の利用・受診関係を既定では確認せず、一般表現であっても次を要求する。

1. 口コミ本人の公開記載
2. client profileの明示許可
3. 法規・privacy上の公開可否確認
4. 診断、処置、症状、効果、具体的受診情報を反復しない

W11-HOの「またのご利用」は利用関係を確認・歓迎する表現だが、W10のようなprofile・法規・privacy条件が付いていない。上位K2を優先する記載はあるものの、routerがW11を無条件の模範として提示するため、例文模倣時の衝突源が残る。

### 必要な是正

確定返信本文は変更しない。次のいずれかで安全に隔離する。

- W11-HOを`active-conditional`にし、K2と同じ限定条件をcategoryとindexへ明記する。
- 条件の妥当性を確認できない場合は`router-eligible: false`として履歴保持し、安全側の例へfallbackする。

## 数値・報告上の注意

- `auto_fix_gate.json`は`allowed: true`、regression/output collapseともfalseである。
- `independent-qa.md`は初回FAILを履歴として残すが、現行判定は末尾の再QA PASS・残存fail 0件である。
- ただし本Fact Guardは、既存評価が捕捉していないW11-HOのK2不整合を1件検出した。このため、機械gateの許可だけを根拠に「安全上の未解決0」とは報告できない。
- benchmarkのtoken・duration値は0だが、実測不能のplaceholderである。「0 tokens」「0秒で実行」と性能値として報告してはならない。
- 「通常router 25件」は現在の設定上の母集団数であり、F01解消前に「安全に利用可能な25件」とは表現しない。

## 変更有無

この監査では候補版14ファイルを変更していない。新規作成したのは本報告書のみである。

---

## 修正後再監査（2026-07-22）

### 最終判定

**内容Fact Guard: PASS（未解決0件）**

**最終数値・本番反映ゲート: FAIL（再benchmark未実施1件）**

前回F01の是正後、候補版14ファイルを再度読取専用で確認した。W11-HOの確定本文は変更されず、candidate routerだけが`active-conditional`へ限定された。K2との内容衝突は解消している。

ただし、`benchmark.json`と`auto_fix_gate.json`はW11修正前に生成されたファイルである。したがって、その数値とgate判定を修正後候補版の評価結果として主張することはできない。修正後候補版で同一評価を再実行し、成果物を更新するまで最終反映ゲートはFAILとする。

### 7観点の再検査

| 観点 | 再判定 | 再検査結果 |
|---|---|---|
| 確定26全文の改変・捏造 | PASS | 新規23件をbatch-01〜06、既存3件を確定正本と再比較。26/26完全一致、差分0。W11もbatch-02と完全一致 |
| candidateのapproved誤昇格 | PASS | 未確認candidateの通常参照経路0。A35は`router-eligible: false`を維持。W10/W11は「全文確定」と「router条件」を分離しており、自動active化ではない |
| K1〜K6と例文の衝突 | PASS | W11はK2に従う4条件付きとなり、例文が安全核を上書きする経路は解消 |
| 未確認の共有・改善・医療/法務事実 | PASS | K3、staff-sharing、業種境界を維持。W11は症状・効果・施術情報の非反復を必須化。未確認の共有、研修、改善済み、医療・法務事実の生成許可なし |
| A35の実行経路除外 | PASS | `SKILL.md`、`reply-rules.md`、`case-index.md`、category、`good-output.md`、`feedback-loop.md`、`approved-replies.md`で除外状態を維持 |
| W10本文・4条件・fallback | PASS | 確定本文不改変。4条件成立時だけeligible、1件でも不明ならW15-SC/G05-MPへfallback。W11修正による回帰なし |
| 最終報告数値 | **FAIL** | 記録値自体は旧134/136=98.529%、候補136/136=100%、差+1.471pt、34評価・136 assertionsで内部一致。ただしbenchmark生成は16:27、修正7ファイルは16:41〜16:43更新のため、修正後候補版の評価値としては未確認 |

### W11-HOの修正確認

確定本文は次のまま変更されていない。

> ご感想をお寄せいただき、ありがとうございます。「これからも通いたい」というお言葉が励みになりました。
> またのご利用をお待ちしております。

router条件は次の4点で統一された。

1. 口コミ本人が一般的な利用経験を公開文に明記している。
2. client profileが一般的な「ご利用」の歓迎を明示許可している。
3. 法規・privacy上の公開可否を確認済みである。
4. 症状、効果、施術情報を返信で反復しない。

次の7ファイルで状態と参照条件を照合した。

- `SKILL.md`: W10・W11は各4条件成立時だけ参照し、不明時はW15/G05へ切替
- `references/reply-rules.md`: K2、W10/W11条件、fallbackを明記
- `examples/case-index.md`: W11を`confirmed-good全文 / router active-conditional`とし、4条件とfallbackを列挙
- `examples/high-risk-special.md`: 確定本文を保持し、4条件、適用・不適用条件、fallbackを局所明記
- `examples/good-output.md`: W10/W11の条件付き参照と不明時fallbackを明記
- `references/feedback-loop.md`: 全文確定状態とrouter条件を分離し、4条件を列挙
- `examples/approved-replies.md`: W11を`confirmed-good全文 / router active-conditional`として記録し、4条件成立時だけ参照

7ファイル間の条件矛盾、A35/W10の回帰、W11の無条件参照経路は見つからなかった。

### benchmark数値の扱い

現存成果物から確認できる記録値は以下である。

- 旧版: 34評価、134/136 assertions、98.529%
- 候補版: 34評価、136/136 assertions、100%
- 差: +1.471ポイント
- `auto_fix_gate.json`: `allowed: true`、regression false、output collapse false

しかし、`benchmark.json`と`auto_fix_gate.json`の生成時刻は2026-07-22 16:27であり、W11修正対象7ファイルの更新時刻は16:41〜16:43である。最終報告では、再実行前に上記を「修正後候補版の結果」「最終gate PASS」と表現してはならない。token・durationの0も引き続き実測値として扱わない。

### 残る必要作業

修正後候補版に対してbenchmarkとauto-fix gateを再実行し、評価34件・136 assertions、critical、regression、output collapseを再確認する。その更新時刻と対象candidateの整合が取れれば、本Fact Guardの総合判定をPASSへ更新できる。

この再監査でも候補版14ファイルは変更していない。追記したのは本報告書だけである。
