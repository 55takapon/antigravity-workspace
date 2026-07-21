# iteration-4 現行基準

確認日: 2026-07-21  
対象正本: `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply`

## 1. 結論

- `gbp-review-reply` 正本8 Markdownには、tracked / stagedとも差分がない。
- `skill-update` の `prepare` が作った `iteration-4` と `skill-snapshot\iteration-4` は存在し、manifestは評価ID 1〜34を列挙している。
- 正本8ファイルとiteration-4 snapshot 8ファイルは、SHA-256が8/8一致する。
- 正式な入力 `evals\evals.json` の実数は34件である。iteration-4はこの34件から作られている。
- iteration-3には「34件・136 assertions」と「36件・144 assertions」の両方の記録がある。今回はどちらかを推測採用せず、現行 `evals.json` の34件をbaselineとする。
- 本監査時点で本番、candidate、client、iteration-1〜3、`evals.json` は変更していない。`iteration-4` 全体はGit上で未追跡である。

## 2. Git状態

実行した対象限定確認:

```text
git diff --name-only -- .agent/skills/gbp-review-reply
git diff --cached --name-only -- .agent/skills/gbp-review-reply
git status --short -- .agent/skills/gbp-review-reply .agent/skills/gbp-review-reply-workspace/iteration-4
```

結果:

- 正本 `gbp-review-reply` の通常差分: 0件
- 正本 `gbp-review-reply` のstaged差分: 0件
- `iteration-4`: `?? .agent/skills/gbp-review-reply-workspace/iteration-4/`

したがって「正本はclean」である一方、リポジトリ全体をcleanとは表現しない。iteration-4は今回の作業領域として未追跡である。

## 3. prepareとsnapshot

`iteration_manifest.json` で確認した値:

| 項目 | 実値 |
|:---|:---|
| skill | `gbp-review-reply` |
| target | `...\.agent\skills\gbp-review-reply` |
| workspace | `...\.agent\skills\gbp-review-reply-workspace` |
| iteration | `...\iteration-4` |
| snapshot | `...\skill-snapshot\iteration-4\gbp-review-reply` |
| eval source | `...\evals\evals.json` |
| manifest eval IDs | 1〜34 |

prepare成功の実ファイル根拠:

- `iteration_manifest.json` が存在し、34件すべての評価名とパスを持つ。
- 34件の評価ディレクトリが存在する。
- 各評価に `old_skill` / `with_skill` の準備領域とmetadataがある。
- `skill-snapshot\iteration-4\gbp-review-reply` に正本8ファイルのコピーがある。

snapshot構成:

```text
gbp-review-reply/
├─ SKILL.md
├─ references/
│  ├─ reply-rules.md
│  ├─ feedback-loop.md
│  ├─ evidence.md
│  └─ changelog.md
└─ examples/
   ├─ quality-boundaries.md
   ├─ good-output.md
   └─ approved-replies.md
```

SHA-256比較: 8/8一致。snapshotは監査開始時点の正本を正確に保持している。

## 4. 現行正本8ファイル

| ファイル | 行数 | 現在の主責務 |
|:---|---:|:---|
| `SKILL.md` | 78 | 5工程、通常出力、主要ゲート |
| `references/reply-rules.md` | 254 | 共通・業種・低評価・profile・検査の詳細 |
| `references/feedback-loop.md` | 153 | 採否記録、22タグ、E/C/I/U、例の状態管理 |
| `references/evidence.md` | 125 | 公式・研究・運用記事・ユーザー境界の出典管理 |
| `references/changelog.md` | 42 | 変更履歴 |
| `examples/quality-boundaries.md` | 48 | phrase-level良好/NG境界 |
| `examples/good-output.md` | 134 | A35、U-R04、U-R05、A36と出力形式 |
| `examples/approved-replies.md` | 366 | active 3件とhistorical/deprecated 13件の台帳 |

合計1,200行。通常生成は `SKILL.md` から `reply-rules.md` を必読する一方、`good-output.md` と `approved-replies.md` を読まない設計である。このため、現状は具体例より禁止・検査ルールが実行時に強く効く。

## 5. 34件と36件の差異

現在確認できる事実:

1. `evals\evals.json` は34件。
2. iteration-4 manifestも34件。
3. iteration-3 `skill-checker-report.md` は「正式評価34件、136 assertions」と記録する。
4. iteration-3 `design\confirmed-boundary-eval-plan.md` は、既存34件へU-R04と医療の強度回帰の2件を加える36件設計を記録する。
5. iteration-3 `regression-results.md` と `benchmark.json` は、後段の拡張実行を36件・144 assertionsとして記録する。

したがって、以前の36件報告は「既存34件＋後段追加2件」の比較結果であり、現行の正規入力ファイルへ2件が統合されたことを意味しない。iteration-4 prepareが34件なのは現行 `evals.json` に忠実な結果である。

iteration-4では、追加ケースを作る場合も既存34件と混同せず、採用前に `evals.json` への正式統合またはiteration固有差分として明示する。

## 6. 変更対象と変更対象外

今回の設計対象候補:

- `SKILL.md`: 実行時のルール量を圧縮し、例ルーターを導入する候補
- `references/reply-rules.md`: 最小安全核とprofile/業種境界へ再編する候補
- `examples/good-output.md`: 軽量ルーター化の候補
- `examples/active/`: ケース別良好全文例の新設候補（設計・承認後のみ）
- `references/feedback-loop.md`: 例の状態・採否記録と生成規則を分離する候補
- `examples/quality-boundaries.md`: ユーザー確定NG語を保持したまま、通常runtimeから外す候補
- `examples/approved-replies.md`: 承認履歴として維持し、通常runtimeから外す候補

変更対象外:

- 本番正本（candidate比較・承認前は変更しない）
- `skill-snapshot\iteration-1`〜`iteration-4`
- `iteration-1`〜`iteration-3`
- `evals\evals.json`（評価設計担当以外は変更しない）
- クライアント配下全ファイル
- 外部Excel、ダウンロード資料、元記事
- 過去の投稿済み本文、承認事実、changelog既存履歴

## 7. 現段階の停止事項

- 具体的な良好全文例がユーザー確認を終える前に、過剰ルールを本番から削除しない。
- ユーザー確定済みNG語は、今回の「禁止中心から例中心へ」という方針だけを理由に消さない。runtimeでどう扱うかを個別に決める。
- 34件と36件を同じbaselineとして合算・混同しない。

