# sales-copywriting-qa 廃止監査

## 結論

- 判定: RETIRE_WITH_LEGACY_SALES_COPYWRITING
- 理由:
  - `sales-copywriting-qa` は `SKILL.md` 1ファイルのみで、実行コード・設定ファイル・外部依存がない。
  - アクティブなハード依存は、既に廃版方針が決まっている `sales-copywriting` の必須QAゲートに集中していた。
  - `sales-copywriting` をQAなしで延命すると旧7ブロック設計を残すことになるため、同じ退避単位でアーカイブする。
  - `proposal-writing` は作成・接続していない。

## 対象の実態

- ファイル構成: `sales-copywriting-qa/SKILL.md` のみ
- サイズ: 7,504 bytes
- 最終更新: 2026-05-05 07:55:09
- SHA-256: `71B59FBF3100F87C0138D318D14422ACE9EB4B7FA3D2D07D06DF816AE0F9EF1A`
- frontmatter:
  - `name: sales-copywriting-qa`
  - `description: sales-copywritingスキルで作成した提案文の品質を辛口で検査するスキル... /sales-copywriting-qa で起動。`
- 実行コードの有無: なし。コードブロックは手順・出力フォーマット・ファイル構成の説明のみ。
- 主な機能: 旧 `sales-copywriting` の7ブロック構成に沿う8軸QA、合否判定、NG速攻チェック。

## QAルールの分類

| ルール | 分類 | 根拠 | 将来の再利用候補 |
|---|---|---|---|
| 冒頭2-3行で何者かを明確化 | 旧設計専用 | `SKILL.md:27` Block 1前提 | 条件付き |
| 権威性が安心装置として機能 | 新方針と衝突 | `SKILL.md:28` 権威性必須化 | なし |
| Block 1が4行以上に膨らまない | 旧設計専用 | `SKILL.md:29` Block制約 | なし |
| 定型文開始を避ける | 維持価値あり | `SKILL.md:30`, `SKILL.md:171` | あり |
| 実績は事実のみ | 維持価値あり | `SKILL.md:31` | あり |
| 業種・事業への具体言及 | 旧設計専用 | `SKILL.md:41` 個社パーソナライズ必須化 | 条件付き |
| テンプレ感を避ける要素 | 旧設計専用 | `SKILL.md:42` 個別化前提 | 条件付き |
| 根拠のない持ち上げなし | 維持価値あり | `SKILL.md:43` | あり |
| 同業種でよく聞く声として事実共有 | 旧設計専用 | `SKILL.md:53` 課題共感ブロック前提 | 条件付き |
| 煽り表現なし | 維持価値あり | `SKILL.md:54`, `SKILL.md:175` | あり |
| 脅しでなく寄り添い | 維持価値あり | `SKILL.md:55` | あり |
| 課題共感の具体性 | 旧設計専用 | `SKILL.md:56` 課題共感ブロック前提 | 条件付き |
| ベネフィット主語が貴社 | 旧設計専用 | `SKILL.md:66`, `SKILL.md:178` | 条件付き |
| 変化後の世界で描写 | 旧設計専用 | `SKILL.md:67` 旧セールス構成寄り | 条件付き |
| ①②③で区切る | 新方針と衝突 | `SKILL.md:68` 表記固定 | なし |
| 自社主語を避ける | 維持価値あり | `SKILL.md:69` | あり |
| CTAを1つに絞る | 維持価値あり | `SKILL.md:79`, `SKILL.md:176` | あり |
| 15分等の低ハードルCTA | 新方針と衝突 | `SKILL.md:80` 15分中心の固定 | なし |
| 押し付け表現なし | 維持価値あり | `SKILL.md:81` | あり |
| 選択権が相手にある | 維持価値あり | `SKILL.md:82` | あり |
| 営業メールだと即判断されない | 維持価値あり | `SKILL.md:92` | あり |
| 過剰敬語・よそよそしさなし | 維持価値あり | `SKILL.md:93` | あり |
| 人間味・温度感 | 旧設計専用 | `SKILL.md:94` 伴走者文体前提 | 条件付き |
| セールス臭MAX表現なし | 維持価値あり | `SKILL.md:95`, `SKILL.md:177` | あり |
| 煽りでなく事実共有 | 維持価値あり | `SKILL.md:96` | あり |
| 1000文字未満必須 | 新方針と衝突 | `SKILL.md:106`, `SKILL.md:173` 文字数固定 | なし |
| 600-800文字が理想 | 新方針と衝突 | `SKILL.md:107` 尺固定 | なし |
| 件名20文字以内 | 旧設計専用 | `SKILL.md:108`, `SKILL.md:174` 用途固定 | 条件付き |
| 2-3行で段落区切り | 維持価値あり | `SKILL.md:109` | あり |
| すっと読める | 維持価値あり | `SKILL.md:110` | あり |
| 誇張・盛った表現なし | 維持価値あり | `SKILL.md:120` | あり |
| あいまい表現なし | 維持価値あり | `SKILL.md:121` | あり |
| サービス内容の誤解可能性なし | 維持価値あり | `SKILL.md:122` | あり |
| 何をしてくれる人か分かる | 維持価値あり | `SKILL.md:123` | あり |
| 返信後に何が起きるか想像できる | 維持価値あり | `SKILL.md:124` | あり |

## 依存関係

| 参照元 | 行・箇所 | 種別 | 現在有効か | 対応 |
|---|---|---|---|---|
| `skill-management/SKILL.md` | 100-101 | 管理台帳 | 有効 | 一覧から削除 |
| `skill-management/SKILL.md` | 111 | 管理台帳 | 有効 | `client-chat-review` 説明から旧QA委譲を削除 |
| `client-chat-review/SKILL.md` | 3 | ルーティング依存 | 有効 | 新規フォーム営業提案文は対象外に変更 |
| `README.md` | 25-26, 32 | 管理台帳/ルーティング説明 | 有効 | 旧2スキルと自動連鎖を削除 |
| `blog-writing/SKILL.md` | 249 | ソフト参照 | 有効 | 連携表から削除 |
| `sales-copywriting/SKILL.md` | 3, 67, 70, 81, 91, 109 | ハード依存 | 有効 | `sales-copywriting` ごと退避 |
| `sales-copywriting/examples/good-output.md` | 35 | ソフト参照 | 有効だったが退避対象内 | `sales-copywriting` ごと退避 |
| `sales-copywriting/knowledge/profile-registry.md` | 17 | ソフト参照 | 有効だったが退避対象内 | `sales-copywriting` ごと退避 |
| `sales-copywriting/references/changelog.md` | 7 | 履歴 | 有効だったが退避対象内 | 履歴として保持したまま退避 |
| `.agent/.obsidian/workspace.json` | 16, 97, 116, 159, 188, 189, 197 | 履歴/エディタ状態 | 実行依存ではない | 変更なし |
| `sales-copywriting-workspace/**` | 複数 | 履歴/評価ワークスペース | 実行依存ではない | 変更なし |
| `scratch/skill-dashboard/skills-data.js` | 60, 420, 426-430 | 生成物 | アクティブスキルではない | 変更なし |

## 実利用調査

- 自動実行: ファイル検索上、`sales-copywriting-qa` を呼び出すスクリプト・CLI・JSON/YAML設定は見つからなかった。
- スクリプト: `.agent` 内の主要 `scripts/` 配下検索で該当なし。
- ルーティング: `sales-copywriting` の必須QAゲート、`client-chat-review` の説明、`README.md` の自動連鎖に参照あり。
- ログ: `.agent/history`, `.agent/work`, `.agent/clients` から該当なし。
- slash command / alias: `SKILL.md` description の `/sales-copywriting-qa` 以外に実行設定は見つからなかった。
- Windowsタスクスケジューラ: `schtasks` はパスエラー、`Get-ScheduledTask` はアクセス拒否で確認不能。
- 確認不能事項: 管理者権限が必要なタスクスケジューラ全件、外部アプリ側の非ファイル管理ルーティング。

## 廃止可否の根拠

- 実行コード、自動化、外部ツールからの実依存は確認されなかった。
- 現在有効なハード依存は `sales-copywriting` の旧QA必須ゲートのみ。
- `sales-copywriting` はユーザー決定済みで廃版方針のため、QAなしに改修・延命せず同時退避するのが安全。
- 一般品質として再利用候補はあるが、独立QAスキルを残す必要とは別問題である。

## 実施変更

| ファイル・フォルダ | 変更内容 | 理由 |
|---|---|---|
| `skills/sales-copywriting-qa/` | アーカイブへ移動 | 廃止対象 |
| `skills/sales-copywriting/` | アーカイブへ移動 | QA必須ゲートの参照切れ防止、既決の廃版方針 |
| `skills/skill-management/SKILL.md` | 現在一覧から旧2スキルを削除、client-chat-review説明を中立化 | 管理台帳の整合 |
| `skills/skill-management/references/changelog.md` | 廃止日・理由・退避先を追記 | 履歴保持 |
| `skills/client-chat-review/SKILL.md` | QA委譲記述を削除し対象外へ変更 | 存在しないQAへのルーティング防止 |
| `skills/README.md` | 旧2スキル行と自動連鎖を削除 | アクティブ索引の整合 |
| `skills/blog-writing/SKILL.md` | 連携表から旧 `sales-copywriting` を削除 | 存在しないスキルへの参照防止 |
| `skills/sales-copywriting-workspace/` | アーカイブへ移動 | `SKILL.md` のない旧評価ワークスペースだが、`skills` 直下に旧名参照を残さないため |
| `skills/sales-copywriting-qa.zip`, `skills/sales-copywriting.zip`, `skills/sales-copywriting-workspace.zip` | アーカイブへ移動 | 旧スキルの圧縮アーティファクトによる参照混乱防止 |

## 検証結果

- 参照再検索:
  - `skills/sales-copywriting-qa`, `skills/sales-copywriting`, `skills/sales-copywriting-workspace` は存在しない。
  - `skills/sales-copywriting-qa.zip`, `skills/sales-copywriting.zip`, `skills/sales-copywriting-workspace.zip` はアクティブ `skills/` 直下に存在しない。
  - アクティブ領域の旧名残存は `skill-management/references/changelog.md` の過去追加履歴と今回廃止履歴、`blog-writing/SKILL.md` の過去変更履歴のみ。
  - `proposal-writing` へのアクティブ参照はなし。
- Skill Checker:
  - 対象: `skill-management`, `client-chat-review`, `blog-writing`
  - 結果: 差分起因の fail なし。
  - `sales-copywriting` / `sales-copywriting-qa` へのアクティブな必須参照なし。
  - frontmatter破損、description意味破綻、連携表不整合なし。
  - 補足: `blog-writing/SKILL.md` は既存状態として変更履歴を本文内に持ち、概算2,042トークンで2,000目安を少し超えるが、今回差分に起因しない。
- ハッシュ照合:
  - 退避対象スキル本体: 10 files / 44,227 bytes。退避前マニフェストと退避後ハッシュ一致。
  - 旧評価ワークスペース: 25 files / 49,055 bytes。退避前記録と件数・サイズ一致。
  - zip artifacts: 3 files / 58,702 bytes。退避前記録とハッシュ一致。
- 未解決事項:
  - `skill-management/SKILL.md` のPre-flightで指定されている `knowledge/chat_ng_registry/artifacts/NG_RULES.md` は、指定相対パスにも `skills/` 配下検索にも存在しなかった。
  - Windowsタスクスケジューラは通常権限では確認不能。サブエージェント側の権限付き確認では対象名なしとの報告あり。
  - `.agent/.obsidian/workspace.json` と `scratch/skill-dashboard/skills-data.js` には非アクティブなエディタ状態・生成物として旧名が残る可能性がある。

## proposal-writingへ持ち越す検討候補

- 実績・数字・成果を創作しない。
- 誇張、煽り、押し付けを避ける。
- 根拠のない持ち上げを避ける。
- 曖昧表現やサービス内容の誤解リスクを確認する。
- CTAを増やしすぎない。
- 返信後に何が起きるか分かるようにする。
- 相手に選択権がある表現にする。
- 読みやすさ、段落、過剰敬語を確認する。
- 何をしてくれる人かが伝わるか確認する。
