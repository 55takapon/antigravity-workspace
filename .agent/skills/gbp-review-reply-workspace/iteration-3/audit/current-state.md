# iteration-3 現行状態監査

監査日: 2026-07-19  
監査方式: 読取専用。正本、workspace、クライアント資料、Git、Codex側ポインタ、添付監査資料、最新Excelを実ファイルで照合した。本監査時点では本番スキル、クライアントファイル、iteration-1、iteration-2、snapshotを変更していない。

## 1. 現行正本

正本は次である。

```text
C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply
```

本番は7ファイル構成で、すべてGit追跡済みである。

| 相対パス | SHA-256 |
|:---|:---|
| `SKILL.md` | `E86A69E3DA391D81C96977ACBDC4222304F94D6861B0500D8980B07BC4648ECB` |
| `examples/approved-replies.md` | `2BD294A8BD637277D85AEA5691FD84A7125C8173B7857403ECA1FA02E63A5045` |
| `examples/good-output.md` | `2B8BE7A78538D80294FF33360990869E311DD6406E9618E03DD99B41210E9137` |
| `references/changelog.md` | `EC85D67C9C6852C20C3C8BA689B568E8DB8089639D838CE5C1F5E9646C14976F` |
| `references/evidence.md` | `EF3188B62DE34E94B5F68B2CDD2602A1C906F288300AB186EF57BEFA5CE20C8A` |
| `references/feedback-loop.md` | `00E6C68C8A35ED9946B4AD689F969BE1D1A84A84CA136D1B67883087C610C713` |
| `references/reply-rules.md` | `6115B3643F1996C00CC9A432B195C5267E3923370E5CE2C889DD020F2F39780B` |

## 2. iteration-2との同一性

比較先:

```text
C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply-workspace\iteration-2\candidate-skill\gbp-review-reply
```

- 本番7ファイルとiteration-2 candidateは、相対パス、ファイル数、SHA-256が全件一致した。
- candidate側だけに存在する追加ファイルはなかった。
- `skill-snapshot\iteration-2\gbp-review-reply` は7件すべて現行本番とハッシュが異なり、iteration-2適用前のbaselineとして保持されている。
- 添付ZIP内 `LATEST_GBP_SKILL_DIFF_AUDIT.md` に記載された本番7件のハッシュも実環境と一致した。

したがって、今回の更新ベースはiteration-2適用後の現行本番であり、旧版へ戻して作業を始める理由はない。

## 3. Codex側ポインタ

```text
C:\Users\hangy\.codex\skills\gbp-review-reply\SKILL.md
```

- シンボリックリンクではなく、`SKILL.md` 1件だけのポインタstubである。
- 正本として上記antigravity側の `SKILL.md` を明示している。
- 参照資料、実例、クライアント別 `gbp-review\profile.md` / `log.md` の参照先も現行構成と一致する。
- 本ポインタは今回の変更対象ではない。

## 4. Git状態

| 項目 | 確認結果 |
|:---|:---|
| Git root | `C:/Users/hangy/.gemini/antigravity` |
| branch | `main` |
| HEAD | `79a1e9022f9e590f2a7aa2260faad879ba86016d` |
| 本番7件 | 追跡済み、未コミット差分なし |
| client `profile.md` / `log.md` | 追跡済み、未コミット差分なし |
| workspace iteration-1 / 2 | 追跡済み |
| 無関係な未追跡 | `scratch/survey-app/unaginokagura-resevation` のみ。変更禁止 |

`git status` 時に `C:\Users\hangy/.config/git/ignore` へのpermission warningが出たが、対象3領域のstatus、diff、cached diffはいずれも空であり、今回の対象ファイル競合はない。

## 5. 既存workspaceの現在性

workspace:

```text
C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply-workspace
```

### iteration-1

- 旧来の広範な評価セットと `independent-qa.md`、`independent-qa-recheck.md` を持つ。
- iteration-3の評価や現行skill-checker判定へ、そのまま流用しない。
- 履歴・監査証跡として変更しない。

### iteration-2

- 10評価ケースを持つ。
- `benchmark.md` は旧版67.5%、候補100%、回帰false、出力崩壊falseを記録する。
- `auto_fix_gate.json` は `allowed: true` を記録する。
- iteration-2配下に独立QA成果物は見当たらないため、iteration-3では独立QAを別途作る必要がある。
- candidateが現行本番と同一であるため、iteration-2は完了済み履歴として変更しない。

### workspace共通資料

| ファイル | 現在性 |
|:---|:---|
| `evals/evals.json` | iteration-2用10ケース。SHA-256 `EA4941899F32C2D378A98CD2343CDD54D1A75255839FA53CFA1ACFF105170288`。iteration-3評価の正本にしない |
| `phase1-audit.md` | 「client profile/logが存在しない」と記載する旧時点資料。現在の実態と不一致。上書きせずhistorical扱い |
| `check-report-v2.0.md` | 4スタイルを現役前提で検査した旧版資料。現行QAへ流用せず保持のみ |
| `skill-snapshot\antigravity` / `codex` / `iteration-1` / `iteration-2` | 旧版・戻し点。変更禁止 |

## 6. クライアント資料

```text
C:\Users\hangy\.gemini\antigravity\.agent\clients\unaginokagura-kyoto\gbp-review\profile.md
C:\Users\hangy\.gemini\antigravity\.agent\clients\unaginokagura-kyoto\gbp-review\log.md
```

- 2ファイルとも実在し、Git追跡済みである。
- `profile.md` は★5・★4本文なしの2文方針、販促CTAと接客上の歓迎締めの分離、SEO・knowledge境界、重複管理を持つ。
- `profile.md` は、★5本文ありについて「京都駅にお越しの際は、またお立ち寄りいただけますと幸いです」を現役で条件付き許可している。
- `profile.md` は一般的な締めにも「またお立ち寄りいただけますと幸いです」を含める。
- `log.md` は過去36件を保持し、#29、#35、#36を `active-conditional` とする。
- #36は `posted`、返信日2026-07-14であり、投稿済み事実と本文を改変してはならない。
- 旧36件の本文、投稿状態、原資料は今回の変更対象ではない。

## 7. 現役ルールと履歴の境界

### 現役

- `SKILL.md` と `references/reply-rules.md` の現行5工程と生成・検査ルール。
- `examples/approved-replies.md` のA35、A36は現時点で `active`。
- `examples/good-output.md` のclient-record-35、client-record-36は現時点で `active-conditional`。
- client `log.md` の#29、#35、#36は現時点で `active-conditional`。

### 履歴または非模倣

- 4スタイル語は現行生成ロジックにはなく、`references/changelog.md` と旧workspace・snapshotだけに履歴として残る。
- `approved-replies.md` のM/F/P群は `historical` または `deprecated` として区別されている。
- `phase1-audit.md` と `check-report-v2.0.md` は旧時点資料である。
- iteration-1、iteration-2、全snapshotは履歴であり、iteration-3から編集しない。

### 境界注記が不足する箇所

- `changelog.md` の旧2026-07-18項目には「星だけ高評価は原則感謝1文」「CTA / SEOは既定OFF」が残る一方、冒頭の同日追補は★5本文なしを感謝＋歓迎の2文へ変更している。
- 履歴本文は削除せず、後の追補でsupersededされたことを明示する必要がある。

## 8. source-of-truth conflict判定

### ファイル正本の競合

なし。

- 本番7件とiteration-2 candidateは同一。
- Codex側ポインタは本番正本を正しく指す。
- 添付監査資料のハッシュも実環境と一致する。
- 対象ファイルに未コミット競合はない。

### 最新方針との未反映差分

これは正本競合ではなくiteration-3で扱う増分差分である。

1. client profileの京都駅付き締めが現役許可のまま。
2. A36が共通例・client profile・logでactive系のまま。
3. `reply-rules.md` と `changelog.md` に「評価へ時間を割いた投稿者」という説明が残り、最新の「時間や心理を公開文へ漏らさない」境界と混線し得る。
4. 低評価severity、直接謝罪、空の真摯、具体行動、意見への感謝、公開上の安心形成が未実装または部分実装。
5. phrase-level境界を全文のapproved例と分けて管理する台帳が未整備。

## 9. iteration-3の変更対象

- 本番7ファイルの候補コピーに対する、自然語と低評価責任対応の増分差分。
- 承認された場合のみ `examples/quality-boundaries.md` を新設する候補。
- client candidateの `profile.md` に対する地域締め、標準締め、自然語NG、低評価差分。
- client `log.md` は、ユーザーがA36の再利用状態変更を承認した場合、その状態とprofile decisionの記録だけを候補化する。過去本文は変更しない。
- iteration-3独自の評価、benchmark、回帰、独立QA、skill-checker成果物。

## 10. iteration-3の非変更対象

- iteration-1、iteration-2およびその全成果物。
- `skill-snapshot` 配下の全ファイル。
- `phase1-audit.md`、`check-report-v2.0.md`。
- Codex側ポインタ。
- clientの過去36件本文、投稿済み事実、既存原資料、`knowledge.md`。
- 4スタイルを記録した過去のchangelog本文。
- Excel候補30件全文のapproved一括登録。
- `skill-management` 等、今回の5領域外のスキル。

