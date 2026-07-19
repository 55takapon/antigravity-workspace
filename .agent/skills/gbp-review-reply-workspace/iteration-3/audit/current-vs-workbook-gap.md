# iteration-3 現行版と最新Excelの差分監査

## 1. Excelの同一性と読取範囲

対象:

```text
C:\Users\hangy\Downloads\GBP口コミ返信_模範候補30件_最新修正版.xlsx
```

SHA-256:

```text
C805E954836BBF43B9D2ECED1F39CE4156D753B5A504C114AC7C6B627BB56F52
```

次の全10シートを、非空セルを含め全行走査した。

1. `候補30件`
2. `選定サマリー`
3. `評価基準`
4. `出典監査`
5. `温度設計`
6. `プロ診断`
7. `改善履歴`
8. `NG良好事例`
9. `低評価設計`
10. `ルール改訂案`

## 2. Excel内の状態境界

Excel全体を同じ強さの根拠として扱わない。

| シート | iteration-3での扱い |
|:---|:---|
| `プロ診断` | 最新の判断原則候補。現行ルールとの整合を確認して設計へ使う |
| `改善履歴` | H01〜H16のBefore→中間→After監査証跡。phrase-level境界へ整理可能 |
| `NG良好事例` | phrase-levelのNG・良好・限定使用境界候補 |
| `低評価設計` | severityと構成の設計材料 |
| `ルール改訂案` | 実装候補。正本へ無条件コピーしない |
| `候補30件` | 全文返信の候補。ユーザーが個別選定するまでcandidateまたはpending-user-selection |
| `評価基準` | iteration-3 rubricの材料 |
| `出典監査` | evidence候補。外部原文を再確認してから採用可否を決める |
| `温度設計` | 簡潔と冷淡を混同しないための補助設計 |
| `選定サマリー` | 選定状態の索引。未選定をapprovedと解釈しない |

`候補30件` の全文は、Excelに収録されていることを理由にapprovedへ昇格させない。たとえばR01は★5本文なしの3文候補だが、現行の2文境界を自動で上書きする根拠にはしない。

## 3. 既に反映済みで変更しない領域

| 領域 | 現行状態 | 判定 |
|:---|:---|:---|
| 4スタイル | 現行生成ロジック・通常出力・feedbackから削除済み | 再実装しない。回帰だけ検査 |
| 通常出力 | 最終返信案のみ | 維持 |
| 修正方法 | 元口コミ・profile・確定指摘から全文再構成 | 維持 |
| SEO・knowledge | 既定OFF、profile許可節だけ参照 | 維持 |
| 販促CTAと歓迎 | 分離済み | 維持し、地域付き締めだけ再審査 |
| 強制類語化 | 廃止済み | 維持 |
| 標準歓迎締めの反復 | 自然なら重複可 | 維持 |
| E/C/I/U | 導入済み | 維持 |
| profile/log | clientに作成済み | 新規作成しない |
| active/historical/deprecated | 初期分類済み | phrase-level状態だけ追加検討 |

## 4. A. 自然な日本語の差分

| 論点 | 現行 | 最新Excel・指示 | 差分判定 |
|:---|:---|:---|:---|
| 標準歓迎締め | 「またのご来店」「またお立ち寄り」等を自然な歓迎として許可 | 飲食の第一候補は「またのご来店をお待ちしております」。「心より」は高温度時 | 部分反映。第一候補の明示が必要 |
| 不自然な言い換え | 珍しい類語を強制しないという抽象ルール | 「機会」「日」を使う4表現をconfirmed-ng化 | 具体境界が未反映 |
| 受領報告終わり | 店側感情・受領報告だけで終えない | 「拝見しました」「確認しました」「触れてくださいました」「ありがたく拝見しました」で終了しない | 概念反映済み、具体境界が未反映 |
| 時間への感謝 | `reply-rules.md` と `changelog.md` に「評価へ時間を割いた投稿者」と記載 | 「貴重なお時間を割いて」「大切なお時間を使って」はconfirmed-ng。背景理解を公開文へ変換しない | active説明の置換が必要 |
| 心理の物語化 | unsupported inferenceで一部対応 | 「勇気をもって」はinternal-context-leakとしてconfirmed-ng | 具体境界が未反映 |

Excel根拠:

- `改善履歴` H01以降の自然な締めBefore→After。
- `改善履歴` H12の「貴重なお時間」NG。
- `改善履歴` H14の「勇気をもって」NG。
- `NG良好事例` の `NG-C01`、`NG-A01`、`NG-A03`、`NG-A05`。
- `プロ診断` の「自然な定型句を壊さない」。
- `ルール改訂案` RR-01、RR-03、RR-10。

## 5. B. 低評価の謝罪・責任・改善・感謝

| 論点 | 現行 | 最新Excel・指示 | 差分判定 |
|:---|:---|:---|:---|
| severity | 星・本文・安全リスクの一般分岐 | L1軽微、L2明確、L3重大・複数、L4高リスク・未確認 | matrix未反映 |
| 直接謝罪 | 必要時に謝罪する一般則 | 明確な不備は「申し訳ございません」「誠に申し訳ございませんでした」「心よりお詫び申し上げます」 | 強度境界未反映 |
| 間接謝罪 | 明示NGなし | 「申し訳なく思っております」は内心説明であり原則NG | 未反映 |
| 真摯 | 低評価で使用可能 | 「真摯に受け止めております」単独終了NG。見直す対象と確認・改善行動が必要 | 部分反映 |
| 改善具体性 | 未確認の対応済み事実は禁止。実行可能性確認あり | 対象、行動、必要時のみ確認済み主体を明示 | 部分反映 |
| 意見への感謝 | 標準候補なし | 「貴重なご意見」を標準、「率直なご意見」を文脈使用 | 未反映 |
| 詳細提供への感謝 | 標準候補なし | 「具体的な状況を…」は個別確認で追加経緯を得た場合だけlimited-use | 未反映 |
| 公開上の安心 | 第三者に読まれる公開文という一般則 | 問題軽視なし、反論なし、改善対象理解、実行可能な対応を文章機能で示す | 実務チェック未反映 |
| 重大低評価の再来店誘導 | 入れない | 入れない | 反映済み |

Excel根拠:

- `低評価設計` のseverity別構成。
- `NG良好事例` の間接謝罪、空の誠意、背景漏入。
- `改善履歴` の謝罪、具体行動、感謝へのBefore→After。
- `ルール改訂案` RR-04、RR-05、RR-07。
- `評価基準` の事実忠実性、日本語、感謝、責任、守秘等。

## 6. C. 良好例・NG例・中間案の状態管理

| 項目 | 現行 | 最新要件 | 差分判定 |
|:---|:---|:---|:---|
| 全文approved | 実承認例をactive/historical/deprecated分類 | 候補30件は選定までcandidate | 自動昇格禁止を維持 |
| phrase boundary | 全文例とルール本文に分散 | confirmed-good / confirmed-ng / limited-use / candidate / historical / superseded-intermediate / pending-user-selection | 専用台帳候補が未整備 |
| 中間案 | changelogや旧資料に断片 | Before→中間→Afterを監査証跡として保持 | 状態定義の追加が必要 |
| A35 | active・active-conditional | 焦点選択例として再確認 | 維持候補 |
| A36 | active・active-conditional | 直接謝罪と意見への感謝が不足 | historical降格をユーザー確認 |

`quality-boundaries.md` を新設する場合は、全文の承認済み返信台帳と重複させず、phrase-levelの状態、使用条件、理由、scope、確認日、根拠、Before→Afterだけを置く。新設自体はユーザー承認前に本番へ反映しない。

## 7. D. client profileの差分

対象:

```text
C:\Users\hangy\.gemini\antigravity\.agent\clients\unaginokagura-kyoto\gbp-review\profile.md
```

| 論点 | 現行 | iteration-3候補 |
|:---|:---|:---|
| 飲食の標準締め | 「またのご来店を心より」「またお立ち寄り」を許可 | 第一候補「またのご来店をお待ちしております」、「心より」は高温度時 |
| 京都駅付き締め | ★5本文ありで条件付き現役許可 | 一時停止またはpromotional/regional CTAとして通常歓迎から分離。ユーザー再承認待ち |
| 自然語NG | 「またお会いできることを」「またのご利用ください」等 | 「機会」「日」系4表現、間接謝罪、時間感謝、勇気の物語化を追加 |
| 低評価 | 原因推測禁止、実行可能な共有・確認だけ | severity、直接謝罪、真摯＋具体行動、標準感謝、公開安心を追加 |
| A36 | 再審査済み実投稿候補 | 投稿済み事実は保持し、現役模倣可否だけ再分類候補 |

client `log.md` の過去36件本文は変更しない。A36の状態を更新する場合も、投稿済み事実を保持し、profile decisionとreview投稿記録を混同しない。

## 8. E. feedback-loopとタグ差分

既存タグを残しつつ、最新Excelの類似概念を次へ統合する。

### 事実・根拠

- `semantic-inflation`
- `unsupported-inference`
- `source-conflict`

### 焦点・構造・日本語

- `focus-selection`
- `empty-sentence`
- `construction-repetition`
- `structural-repetition`
- `length-mismatch`
- `unnatural-variation`

### 関係性・締め

- `cta-pressure`
- `brand-novelty`
- `closing-mismatch`
- `gratitude-mismatch`

### 低評価の責任対応

- `apology-mismatch`
- `empty-sincerity`
- `action-vagueness`
- `public-reassurance-gap`

### 安全・voice・工程

- `privacy-risk`
- `policy-risk`
- `voice-mismatch`
- `internal-context-leak`
- `patch-regression`

統合関係:

- `apology-underweight` + `severity-mismatch` → `apology-mismatch`
- `accountability-gap` → `action-vagueness` または `public-reassurance-gap`
- `gratitude-gap` / `generic-gratitude` / `relevance-gap` / `information-centric` → `gratitude-mismatch`
- `emotional-overreach` → `unsupported-inference` または `internal-context-leak`
- `respectful-gratitude` は失敗タグではなくgood属性

## 9. evidenceへの採用境界

- Google等の外部公式根拠、査読付き補助根拠、ユーザー確認済み運用境界を別種別として記録する。
- `出典監査` のURLや要約は、外部原文を再確認するまでevidenceの確定材料にしない。
- ユーザーが確定した自然語・感謝表現は「外部一般論」ではなく「運用上のconfirmed boundary」として記録する。
- Web上の見本やExcelの全文を承認済み実例へコピーしない。

## 10. source-of-truth conflictと判断待ち

ファイル版の正本競合はない。次は、最新版との未反映差分であり、本番反映前のユーザー判断対象である。

1. 鰻profileの京都駅付き締めを停止するか。
2. A36をactiveからhistoricalへ降格するか。
3. `examples/quality-boundaries.md` を新設するか。
4. Excelのcandidate全文からapprovedへ個別昇格するものがあるか。

4について、ユーザーが個別に選定しない限り、iteration-3では昇格0件とする。

## 11. iteration-3候補版の変更・非変更境界

### 変更候補

- 現行7ファイルを土台にした自然語・低評価・状態管理の増分。
- 承認された場合だけphrase-level boundary台帳。
- client candidateのprofile差分。
- iteration-3評価、benchmark、回帰、独立QA、skill-checker。

### 非変更

- 4スタイル削除のやり直し。
- iteration-1、iteration-2、全snapshot。
- 通常出力、E/C/I/U、profile/log作成、SEO既定OFF等の完了済み構造。
- A36の投稿済み本文・投稿事実。
- client過去36件本文と原資料。
- Excel候補30件全文のapproved一括登録。

