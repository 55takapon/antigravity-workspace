# iteration-4 candidate 実装サマリー

実装日: 2026-07-22  
実装先: `iteration-4/candidate-skill/gbp-review-reply`  
本番適用: 未実施

## 実装結果

- iteration-4 snapshotをcandidateへ機械コピーしてから編集した。
- 5工程と「通常は投稿可能な最終返信案だけ」の出力を維持した。
- 実行順を`K1〜K6最小安全核 → 軽量router → 該当例最大2〜3件 → 全文検査`へ変更した。
- 登録全文例26件を5カテゴリへ収録した。通常router参照候補はA35を除く25件で、W10は4条件成立時だけ参照可能。内訳は既存3件、新規confirmed-good 23件。
- G06-RPは全文例へ含めず、返信済み生成停止の`eval-only-workflow-control`としてindexに置いた。
- A35はcandidateで`active-conditional-proposed / router-eligible: false`とし、ユーザー確認まで参照禁止とした。posted事実、既存履歴本文、approved台帳のsource stateは変更していない。
- W10のユーザー確定本文は変更せず、口コミ本人の公開記載、profile許可、公開可否確認、センシティブ情報非反復の4条件成立時だけrouter参照可能とした。
- `quality-boundaries.md`は監査証跡としてsnapshotのまま保持し、通常runtime必読から外した。
- `approved-replies.md`の既存履歴本文は保持し、新規23件は全文を重複せずindex参照だけ追記した。
- staff-sharingを`allowed / disallowed / conditional / unknown`で定義した。unknown等で返信判断が分かれる時だけ2案、選択後はprofile保存・通常1案とした。
- 4スタイル、別名の装飾分類、VERSION、MANIFEST、deployment、専用リンターは追加していない。

## router構造

```text
K1〜K6を確定
  ↓
examples/case-index.md
  ↓ 1カテゴリだけ選択
cases/star-only.md
cases/positive-short.md
cases/positive-detailed.md
cases/mixed-low-rating.md
cases/high-risk-special.md
  ↓ 条件が近い節を最大2〜3件だけ参照
最終返信案を生成してK1〜K6再検査
```

全26例の一括読込は禁止。登録26件、通常参照候補25件（A35待機）を区別する。W10は条件付きであり、条件不明時はW15/G05等を使う。例はK1〜K6とprofileを上書きできない。

## 確定例件数

| カテゴリ | 件数 |
|:---|---:|
| star-only | 5 |
| positive-short | 2 |
| positive-detailed | 5 |
| mixed-low-rating | 7 |
| high-risk-special | 7 |
| 合計 | 26 |

index登録ID 26件、カテゴリ見出し26件、新規23件のapproved参照行23件を機械確認した。router上はA35を除外した25件を候補プールとし、W10は4条件成立時のみeligibleとする。

## candidateファイルと行数

| ファイル | 行数 | 処理 |
|:---|---:|:---|
| `SKILL.md` | 66 | 再編 |
| `references/reply-rules.md` | 107 | 大幅圧縮・router/staff-sharing追加 |
| `references/feedback-loop.md` | 86 | 承認状態ガバナンス維持・生成規則重複削減 |
| `references/evidence.md` | 40 | 根拠台帳へ圧縮 |
| `references/changelog.md` | 50 | 既存履歴を保持し2026-07-22追記 |
| `examples/good-output.md` | 23 | 軽量router入口へ再編 |
| `examples/approved-replies.md` | 398 | 既存履歴保持・新規23件の参照台帳追記 |
| `examples/quality-boundaries.md` | 48 | snapshotのまま証跡保持 |
| `examples/case-index.md` | 71 | 新規 |
| `examples/cases/star-only.md` | 73 | 新規・5例 |
| `examples/cases/positive-short.md` | 31 | 新規・2例 |
| `examples/cases/positive-detailed.md` | 74 | 新規・5例 |
| `examples/cases/mixed-low-rating.md` | 101 | 新規・7例 |
| `examples/cases/high-risk-special.md` | 103 | 新規・7例 |

candidate配下14ファイル。snapshotと同一の`quality-boundaries.md`を除く13ファイルがcandidate差分である。

## 変更していない範囲

- 本番 `skills/gbp-review-reply`
- `skill-snapshot/iteration-1`〜`iteration-4`
- iteration-1〜3
- `evals/evals.json`
- client配下
- 外部Excel・WEBRIES記事

## 次工程

- 旧版とcandidateを既存34件へ同条件で適用する。
- router固有の新規評価は別承認後だけ追加する。
- 確定全文例の完全一致、K1〜K6、profile境界、参照最大3件、4スタイル非復活を独立QAする。
- A35の`active-conditional`統一は本番反映前にユーザー確認する。

## 回帰修正追補

- ID5: C03/U-R05の店づくり方針文をprofile確認時だけ使う条件へ強化。未提示時は口コミ明記点への感謝と許可済み標準歓迎だけで完結する。
- ID11: W05の主観的接客印象と、質問遮断等の具体的不備を分離。具体的不備では謝罪を機械必須にせず、profile・確認状況・深刻度に合う場合にW04/W09の対象明示お詫びの役割を参照する。「申し訳ございません」系列は復活させていない。
- ID27: 高リスクでも公開可能な主要論点を過剰削除せず、費用と契約時説明への懸念を事実認定なしで両方受け止める条件へ補強した。
- 既存の確定返信本文26件は変更していない。新規全文例も追加していない。
