---
name: skill-management
description: スキルの保存場所・命名規則・スキル一覧・タスク前確認(STEP 0)を定めた憲法スキル。スキルの新規作成は skill-creator、既存改善は skill-update、品質検査は skill-checker に委譲。【最重要】あらゆるタスク実行前に「現在のスキル一覧」を確認し、該当スキルがあればそのSKILL.mdを読んでから作業を開始すること。/skill-management で起動。
---

> ⚠️ **作業開始前に必ず knowledge/chat_ng_registry/artifacts/NG_RULES.md を読み、Pre-flight Check を実行すること。**


# skill-management

> 新しいスキルを作るたびに「どこに・どんな形で・何を書くか」が統一されるよう、ルールを定める。

## Anthropic公式 SKILL.md 仕様（準拠必須）

公式ソース: https://docs.anthropic.com/en/docs/claude-code/skills
照合レポート: `brain/f748ddd4-3d3c-444f-bfb7-a2d2d24e69f4/skill_audit_report.md`

### YAML Frontmatter — 使えるフィールド一覧

```yaml
---
name: skill-name              # 必須。小文字+ハイフン+英数字のみ。max 64文字。フォルダ名と一致させる
description: ...               # 必須。目的+トリガー条件。max 1024文字。毎セッションロードされるため簡潔に
disable-model-invocation: true # 任意。副作用のあるスキル（送信・削除等）に必須
allowed-tools: [...]           # 任意。使用許可するツールを制限
context: fork                  # 任意。サブエージェントとして独立コンテキストで実行
agent: Explore                 # 任意。専用エージェントで実行
when_to_use: ...               # 任意。自動起動条件をdescriptionと別に詳述
argument-hint: ...             # 任意。$ARGUMENTSのヒント
---
```

**以下は公式に存在しない — Claudeが無視するため YAML に書かない:**

```
❌ version      → 本文の「変更履歴」セクションに書く
❌ tags         → description に含めるか本文に書く
❌ updated      → 本文の「変更履歴」セクションに書く
❌ source_project
❌ last_synced
```

### Progressive Disclosure（3層設計）

```
Level 1: YAML Frontmatter（name + description）→ 常にロード
Level 2: SKILL.md 本文 → 関連性ありと判断時のみロード（500行以内推奨）
Level 3: references/ assets/ scripts/ → SKILL.md内からリンク、必要時のみ読込
```

---

## スキルの保存場所

```
C:\Users\hangy\.gemini\antigravity\.agent\skills\
│
├── [スキル名]/
│   ├── SKILL.md          ← 必須：スキル本体（500行以内推奨）
│   ├── references/       ← 任意：詳細ドキュメント（詳細データはここに分離）
│   ├── scripts/          ← 任意：実行スクリプト
│   └── assets/           ← 任意：テンプレート等
```

> ⚠️ `scratch/` や `brain/<会話ID>/` にスキルを保存しない。

---

## 現在のスキル一覧

| フォルダ名 | スキル内容 |
|-----------|-----------|
| `gbp-meo-core/` | GBP MEO戦略コアスキル（戦略立案・KPI設計・業種別広告規制リファレンス。旧業種別9スキルの法規部分を references/industry-regulations.md に集約） |
| `gbp-meo-post-core/` | GBP投稿文生成コアスキル（旧post系3スキルの固有ルールは各クライアントの knowledge.md へ移管済み） |
| `gbp-diagnostic/` | GBP診断レポート生成スキル |
| `gbp-review-analysis/` | GBP口コミ全件抽出・テキスト分析・強み/弱みレポート生成 |
| `gbp-review-reply/` | GBP口コミ返信案生成（スタイル4型判定・業種別法規リスク・クライアント別プロファイル・採用ログで継続改善。正本。codex側は同名ポインタ） |
| `sns-buzz-writer/` | SNSバズ投稿文作成（入力テキスト→X長文→辛口QA→ユーザー承認→Threads/IGキャプション並列作成。writer/QAサブエージェント分業・承認ゲート式。旧sns/は2026-07-10にアーカイブ退避） |
| `instagram-content-pro/` | Instagram運用の実務全域（アカウント戦略・プロフィール導線・月間カレンダー・リール台本・カルーセル・インサイト分析。正本。codex側は同名ポインタ。投稿文単体は sns-buzz-writer が担当） |
| `website-production/` | WordPress×SWELLホームページ制作 |
| `site-seo-launch/` | WordPress/SWELLサイト本番公開時のSEO設定一式（SEO SIMPLE PACK・GA4・Search Console・公開前後チェックリスト） |
| `swell-section-design/` | SWELLセクション単位パーツ設計（情報の役割からレイアウト型を判定→トークン連動→コントラスト検証→SWELL貼付コード生成。旧3col-design-tool廃止後継） |
| `contact-form-assist/` | 企業お問い合わせフォーム半自動送信（Playwright自動入力+人間が送信ボタン。Web UI/CLI両対応。正本。実行コードは `C:\Users\hangy\.cursor\test\contact-form-assist`。旧 form-automation / contact-auto は2026-07-17廃止・アーカイブ退避） |
| `company-search/` | 企業検索・データ収集スキル |
| `company-search-quality-check/` | 企業リスト品質チェック（4軸MECE・必須実行） |
| `gbp-report-quality-check/` | GBP月次レポートの品質検査（数値ズレ・設定漏れの自動テスト） |
| `gbp-monthly-report/` | GBP月次パフォーマンスレポート自動生成（Sheets/CSV→HTML/PDF・Node.js） |
| `gbp-partner-research/` | GBPパートナー候補 業種リサーチ・キーワード設計 |
| `daily-report/` | 毎日の振り返りレポート（Claude Code全セッション機械走査→トラブル→スキル反映・再発防止・進捗確認。2026-07-17にデータソースをbrain/から移行しv3再建） |
| `decision-record/` | 構造変更・設計判断・インシデントの履歴記録（ADR方式・トリガー発火型。history/INDEX.md で索引管理） |
| `daily-report-quality-check/` | デイリーレポートの品質検査（全セッション網羅・INCIDENT漏れ・事実確認） |
| `chat-ng-learner/` | チャットNG指摘をKI（NG_RULES.md）へ強制記録するメタスキル |
| `coconala-listing/` | ココナラ出品文の作成・文字数管理・キーワード分散戦略 |
| `small-company-research/` | 中小企業リサーチ・Web奉行連携・サイトプローブ |
| `great-presenter/` | プロフェッショナル・スピーチ＆プレゼンテーション（倫理法人会40分講話対応） |
| `content-strategy/` | ジェットプロデュースブログのコンテンツ戦略・ピラークラスター管理・KPI・編集カレンダー |
| `blog-title-research/` | ブログ記事タイトルのリサーチ・設計（5ステップフロー・SEO/AI検索対応） |
| `blog-writing/` | ブログ記事執筆（プロンプト仕様定義・PREP/PAS/AIDA構成・読者目線） |
| `blog-writing-qa/` | ブログ報告前品質検査（7軸スコア・法令・ブランドボイス・冒頭キャッチー度） |
| `sales-copywriting/` | お問い合わせフォーム営業の提案文ライティング（7ブロック構成・PDCA・バージョン管理） |
| `sales-copywriting-qa/` | 提案文の品質検査（8軸辛口チェック・合否判定・改善指摘） |
| `gbp-post-quality-check/` | GBP投稿文の品質検査（誇大表現・断言・健康効能・誤字の4軸チェック・合否判定） |
| `git-backup/` | GitHubへのバックアップ実行（「バックアップして」「gitに保存して」で起動） |
| `idea-inbox/` | アイデア・思いつき・メモの蓄積・整理 |
| `skill-creator/` | 新規スキル作成のゲート式ワークフロー（完成後に skill-checker を必ず実行） |
| `skill-checker/` | スキル品質検査（7カテゴリ+S1-S16チェックリスト・合否判定・修正ループ） |
| `skill-update/` | 既存スキル改善（旧版比較・評価つき。手動フローのみ採用、cron/自動修正は無効） |
| `skill-management/` | **このファイル**（保存場所・命名規則・一覧・STEP 0 の憲法） |
| `survey-app-deploy/` | 店舗向け星評価アンケートアプリの新規複製・Netlifyデプロイ・テキスト変更手順 |
| `transcript-knowledge-mining/` | 文字起こしからブログ/SNS素材をMECE抽出（逐語保持・出典付き素材カード→ナレッジ台帳追記・投稿フックの種付与）。2モード別台帳=S対話セッション(コーチング等)/O自己アウトプット(倫理法人会・セミナー・ボイスメモ)。話者区別困難時は確度付き推定＋報告 |

---

## スキルの作成・更新・検査（専用スキルへ委譲）

**このファイルでは作成・更新の手順を定めない。必ず以下の専用スキルを使うこと。**

| やりたいこと | 使うスキル | 起動トリガー例 |
|---|---|---|
| 新規スキルを作る | `skill-creator/` | 「これスキルにして」「スキルを作って」「自動化して」 |
| 既存スキルを直す・改善する | `skill-update/` | 「○○スキルを改善して」「精度上げて」「発火しないから直して」 |
| 品質検査だけする | `skill-checker/` | 「○○スキルをチェックして」（creator/update の最終工程でも自動実行） |

### 命名規則（skill-creator 実行時もここに従う）

命名規則: `[業務カテゴリ]-[具体的な用途]` （小文字・ハイフン・英数字のみ。max 64文字。フォルダ名と一致）

```
✅ 良い例:
  website-production    ← 業務カテゴリ明確
  gbp-meo-dental        ← GBP + 業種
  daily-report          ← 機能を表す

❌ 悪い例:
  skill1                ← 内容不明
  sakakibara-hp         ← 案件名（汎用性なし）
  新スキル              ← 日本語はNG
  company_search        ← アンダースコアはNG（ハイフンのみ）
```

### 作成・更新時の統一ルール（旧ルールとskill-checker基準の矛盾を裁定済み）

- 変更履歴・日付・バージョン番号は SKILL.md 本文に書かない。`references/changelog.md` に分離する
- description は発火条件込みで400字目安（公式上限は1024字）
- SKILL.md 本体は 2,000トークン以下（文字数÷4で概算）。旧「500行以内」ルールは廃止
- frontmatter は公式フィールドのみ。`version` / `tags` / `updated` / `dependencies` / `metadata` は書かない（依存パッケージは本文に記載）
- 副作用のあるスキル（送信・削除等）には `disable-model-invocation: true` を付ける
- スキル完成・更新後は skill-checker を必ず実行する
- 新スキル作成時は、このファイルの「現在のスキル一覧」テーブルへの行追加までを完了条件とする

### 既存スキルの扱い（グランドファーザー方式）

新基準適用前に作られた既存スキルの一括リライトは禁止。skill-update で中身を触るタイミングでのみ新基準に合わせる。

---

## タスク実行前のスキル確認フロー（全タスク共通・STEP 0）

**すべてのタスクは、作業開始前に以下のフローを実行する。**

```
STEP 0-1: ユーザーの依頼内容を確認する
          ↓
STEP 0-2: 「現在のスキル一覧」テーブルを参照し、該当するスキルがあるか確認する
          ↓
STEP 0-3: 該当スキルがある → そのSKILL.mdを開いて全文読み、以下を把握する：
          □ ファイル命名規則
          □ 保存場所
          □ テンプレート / フォーマット
          □ 実行フロー（STEPの順序）
          □ NGパターン
          ↓
STEP 0-4: SKILL.mdの実行フローに従って作業を開始する
          ※ 独自フォーマット・独自命名・独自保存場所での成果物作成は禁止
```

> ⚠️ このSTEP 0をスキップしてタスクを実行した場合、成果物の命名・フォーマット・保存場所が
> スキル定義と一致しなくなり、再作成が必要になる。

---

## スキルの更新タイミング

以下に該当したら `skill-update` を起動して更新する（手順は skill-update が定める）:

- 新しいノウハウ・ベストプラクティスが生まれたとき
- 以前の方法よりも良い方法を発見したとき
- ツール・プラットフォームの仕様変更があったとき
- 失敗事例・注意点が増えたとき

---

## スキルとして保存しないもの

| 種類 | 保存場所 |
|------|---------|
| 特定案件の固有情報（金額・スケジュール） | スキルの `clients/` フォルダ または `scratch/` |
| 実行スクリプト（.js, .py, .ps1） | `scratch/[ツール名]/` |
| 会話で生成した一時的なファイル | `brain/<会話ID>/` |
| Webサイト制作の成果物（HTML等） | `scratch/website_production/` |
| クライアントのナレッジファイル | `knowledge/` |

---

## 変更履歴

変更履歴は [references/changelog.md](references/changelog.md) に分離（本文に日付を書かない統一ルールに準拠）。
