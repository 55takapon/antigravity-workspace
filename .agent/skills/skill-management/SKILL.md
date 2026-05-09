---
name: skill-management
description: スキルの作り方・保存場所・命名規則・更新ルールを定めたメタスキル。【最重要】あらゆるタスク実行前に「現在のスキル一覧」を確認し、該当スキルがあればそのSKILL.mdを読んでから作業を開始すること。/skill-management で起動。
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
| `anticrow/` | AntiCrow拡張機能の活用（チームモード・IPC通信等） |
| `gbp-meo-core/` | GBP投稿コアスキル（全業種共通） |
| `gbp-meo-beauty/` | 美容業種GBP投稿スキル |
| `gbp-meo-bodywork/` | ボディワーク業種GBP |
| `gbp-meo-education/` | 教育業種GBP |
| `gbp-meo-legal/` | 法律・士業GBP |
| `gbp-meo-medical/` | 医療業種GBP |
| `gbp-meo-real-estate/` | 不動産業種GBP |
| `gbp-meo-restaurant/` | 飲食業種GBP |
| `gbp-meo-retail/` | 小売業種GBP |
| `gbp-meo-service/` | サービス業GBP |
| `gbp-meo-post-core/` | GBP投稿文生成コアスキル |
| `gbp-meo-post-dental-occlusion/` | 歯科（咬合）GBP投稿 |
| `gbp-meo-post-dental-preventive/` | 歯科（予防）GBP投稿 |
| `gbp-meo-post-jetproduce/` | ジェットプロデュース専用GBP |
| `gbp-diagnostic/` | GBP診断レポート生成スキル |
| `gbp-review-analysis/` | GBP口コミ全件抽出・テキスト分析・強み/弱みレポート生成 |
| `gbp-review-reply/` | GBP口コミ返信案自動生成（星評価別×5トーン・SEOキーワード埋込） |
| `sns/` | SNS投稿スキル（IG/Threads/FB/X 独立スキル含む） |
| `website-production/` | WordPress×SWELLホームページ制作 |
| `site-seo-launch/` | WordPress/SWELLサイト本番公開時のSEO設定一式（SEO SIMPLE PACK・GA4・Search Console・公開前後チェックリスト） |
| `form-automation/` | Webフォーム自動入力スキル |
| `company-search/` | 企業検索・データ収集スキル |
| `company-search-quality-check/` | 企業リスト品質チェック（4軸MECE・必須実行） |
| `gbp-report-quality-check/` | GBP月次レポートの品質検査（数値ズレ・設定漏れの自動テスト） |
| `gbp-partner-research/` | GBPパートナー候補 業種リサーチ・キーワード設計 |
| `contact-auto/` | 企業お問い合わせフォーム自動送信（ハイブリッド型） |
| `daily-report/` | 毎日の振り返りレポート（トラブル→スキル反映・再発防止・進捗確認） |
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
| `skill-management/` | **このファイル**（スキルの作り方） |

---

## 新しいスキルの作り方

### STEP 1：スキル名を決める

命名規則: `[業務カテゴリ]-[具体的な用途]` （小文字・ハイフン・英数字のみ。max 64文字）

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

### STEP 2：フォルダとSKILL.md を作成する

```powershell
New-Item -ItemType Directory ".agent\skills\[スキル名]"
```

以下のテンプレートをコピーして使う：

```markdown
---
name: [スキル名（フォルダ名と同じ・小文字ハイフンのみ）]
description: [目的+トリガー条件を1〜2行で。/[スキル名] で起動。]
---

# [スキル名]

> [1行サマリー]

## [メインコンテンツ]

[手順・チェックリスト・プロンプト等]

## NGパターン

[よくあるミス]

## ファイル構成

[references/等があれば記載]

## 変更履歴

- YYYY-MM-DD: 初版作成
```

**テンプレートの重要ポイント:**
- YAML frontmatter は `name` と `description` のみ
- `version`, `tags`, `updated` は書かない（Claudeが無視する）
- バージョン管理は本文末尾の「変更履歴」セクションで行う
- 副作用のあるスキルには `disable-model-invocation: true` を追加する

### STEP 3：一覧テーブルを更新する

このファイルの「現在のスキル一覧」テーブルに新しいスキルを追加する。

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

## スキルの更新ルール

### いつ更新するか
- 新しいノウハウ・ベストプラクティスが生まれたとき
- 以前の方法よりも良い方法を発見したとき
- ツール・プラットフォームの仕様変更があったとき
- 失敗事例・注意点が増えたとき

### 更新時の手順
1. SKILL.md を編集
2. 本文末尾の「変更履歴」に更新内容を追記
3. 500行を超えていないか確認（超えたら references/ に分離）

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

- 2026-04-12: 初版作成（スキル散在問題の解決・統一ルール化）
- 2026-04-30: Anthropic公式仕様に準拠したテンプレートに全面改訂（非公式フィールド排除・Progressive Disclosure明文化）
- 2026-05-02: 「タスク実行前のスキル確認フロー（STEP 0）」追加。スキル未読のままデイリーレポートを独自フォーマットで作成したインシデントを受け、構造的な歯止めとして追加
- 2026-05-05: `sales-copywriting`・`sales-copywriting-qa` を一覧に追加
- 2026-05-06: `gbp-post-quality-check` を一覧に追加（iami-kakogawa全件QAの知見から新規作成）
- 2026-05-09: `site-seo-launch` を一覧に追加（WordPress/SWELLサイト本番公開時のSEO設定スキル）
- 2026-05-09: `gbp-review-reply` を一覧に追加（GBP口コミ返信案自動生成スキル）
