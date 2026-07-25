# 🧠 スキルライブラリ — 全索引

> **スキルの作り方・保存ルール:** `skill-management/SKILL.md` を参照
> **最終更新:** 2026-04-12

---

## 📍 スキル保存場所

```
C:\Users\hangy\.gemini\antigravity\.agent\skills\
```

> ⚠️ **スキルはここ以外に保存しない。** `scratch/` や `brain/<会話ID>/` に置かない。

---

## 🗣️ 文章・営業系スキルの使い分けと発動フレーズ（早見表）

> 選び方の軸: **その文章は誰に向けたものか。**

| 誰に向けた文章か | 使うスキル | 発動フレーズ例 |
|---|---|---|
| 検索して自分から来る見込み客（記事） | `blog-writing` | 「〇〇のブログ記事書いて」/blog-writing |
| フォーム送信の実行 | `contact-form-assist` | 「フォーム営業を実行して」「送信リストを処理して」※自動発火しない設定・明示依頼が必須 |
| ココナラで比較検討中の購入者（出品ページ） | `coconala-listing` | 「ココナラ出品文作って」「タイトル考えて」「出品を改善して」 |
| すでにやり取りしている相手（返信） | `client-chat-review` | 下書きを貼る+「これ送っていい？」「添削して」「辛口で見て」。採点は「フルで」 |
| 文章でなくサイト公開作業 | `site-seo-launch` | 「サイト公開のSEO設定して」「公開前チェックして」 |

自動連鎖: blog-writing→blog-writing-qa（PASS必須）/ contact-form-assist（送信のみ明示依頼）。

## 📋 スキル一覧

### 🛠️ システム・ツール系

| スキル名 | 概要 | フォルダ |
|---------|------|---------|
| **スキル管理** | スキルの作り方・命名規則・更新ルール（このREADMEの親） | `skill-management/` |
| **チャットNG学習** | 指摘されたNGをKI（Knowledge Item）に即座に記録し絶対再発防止 | `chat-ng-learner/` |
| **フォーム自動入力** | PlaywrightでWebフォームに自動入力（Google Sheets連携） | `form-automation/` |
| **企業検索** | 企業情報の検索・収集・Sheets書き込み | `company-search/` |

### 📱 SNS・コンテンツ系

| スキル名 | 概要 | フォルダ |
|---------|------|---------|
| **SNS投稿** | Instagram/Threads/Facebook/Xの投稿生成・戦略 | `sns/` |
| **ブログ戦略** | ジェットプロデュース向けコンテンツ戦略・ピラークラスター管理・KPI | `content-strategy/` |
| **ブログタイトルリサーチ** | SEO/AI検索対応の記事タイトル設計・5ステップリサーチフロー | `blog-title-research/` |
| **ブログ執筆** | 読者目線×SEO最適化記事生成（PREP/PAS/AIDA・プロンプト仕様定義） | `blog-writing/` |
| **ブログQA** | 報告前品質検査（7軸スコア・法令・ブランド・冠頭キャッチー度） | `blog-writing-qa/` |

### 💬 営業・クライアント対応系

| スキル名 | 概要 | フォルダ |
|---------|------|---------|
| **クライアントチャット添削** | 返信下書きを貼るだけの辛口壁打ち（即レス添削がデフォルト、採点はフルモード時のみ、台帳で育成） | `client-chat-review/` |
| **提案文作成** | 問い合わせフォーム用パートナー提案文の構成設計・新規作成・辛口レビュー・ブラッシュアップ・一変数A/B案。第1弾はWeb制作会社向けGBP協業提案に限定 | `proposal-writing/` |

### 🌐 Web制作系

| スキル名 | 概要 | フォルダ |
|---------|------|---------|
| **意思決定・履歴記録** | 構造変更・設計判断・インシデントをADR方式で記録（`history/INDEX.md`で索引） | `decision-record/` |
| **ホームページ制作** | WordPress×SWELLの全工程（企画→デザイン→構築→公開） | `website-production/` |
| **サイト公開SEO設定** | 本番公開時のSEO設定一式（SEO SIMPLE PACK・GA4・Search Console・インデックス・公開前後チェックリスト） | `site-seo-launch/` |

### 📊 GBP・MEO系（Googleビジネスプロフィール）

| スキル名 | 概要 | フォルダ |
|---------|------|---------|
| **GBPコア** | GBP MEO戦略・KPI設計・業種別広告規制リファレンス | `gbp-meo-core/` |
| **GBP診断** | クライアントGBPの診断レポート生成 | `gbp-diagnostic/` |
| **GBP口コミ分析** | 口コミ全件抽出・テキスト分析・強み/弱みレポート生成 | `gbp-review-analysis/` |
| **GBP口コミ返信** | 口コミ返信案を星評価別×5トーンで自動生成（SEOキーワード埋込対応） | `gbp-review-reply/` |
| **GBP投稿コア** | GBP投稿文生成の共通スキル（クライアント別ルールは各 knowledge.md） | `gbp-meo-post-core/` |

> 2026-07-07: 業種別9スキル（beauty/bodywork/education/legal/medical/real-estate/restaurant/retail/service）とpost系3スキル（post-dental-occlusion/post-dental-preventive/post-jetproduce）は廃止。`skills-archive/2026-07-07-gbp-meo-retirement/` に退避（移管先は同フォルダのREADME参照）。

---

## 🆕 新しいスキルを追加する手順

1. `skill-management/SKILL.md` の手順に従う
2. `.agent/skills/[スキル名]/SKILL.md` を作成
3. **このREADMEのスキル一覧に追記する**

---

## 📁 フォルダ構造

```
.agent/skills/
│
├── README.md                     ← このファイル（全索引）
│
├── skill-management/             ← スキルの作り方メタスキル
│   └── SKILL.md
│
├── form-automation/              ← フォーム自動入力
│   └── SKILL.md
│
├── company-search/               ← 企業検索
│   └── SKILL.md
│
├── sns/                          ← SNS投稿（旧: scratch/sns-skill/）
│   ├── README.md
│   ├── 00_CORE_SKILL_SNS_STRATEGY.md
│   ├── 01_POST_GENERATOR_SKILL.md
│   ├── 02_TOPIC_RESEARCH_SKILL.md
│   ├── 03_AI_EXECUTION_PROMPTS.md
│   ├── 04_X_SKILL.md
│   ├── account_profiles/
│   └── output/
│
├── website-production/           ← ホームページ制作
│   ├── SKILL.md
│   └── clients/                  ← 案件固有情報
│       └── sakakibara-tax.md
│
├── site-seo-launch/              ← サイト公開SEO設定
│   └── SKILL.md
│
├── gbp-meo-core/
├── gbp-diagnostic/
├── gbp-meo-post-core/
├── content-strategy/          ← ブログ戦略
│   └── SKILL.md
├── blog-title-research/       ← ブログタイトルリサーチ
│   └── SKILL.md
└── blog-writing/              ← ブログ執筆
    └── SKILL.md
└── blog-writing-qa/           ← ブログ報告前品質検査
    └── SKILL.md
```

---

## 🗂️ 旧保存場所との対応表（移行記録）

| 旧パス | 新パス | 状態 |
|--------|--------|------|
| `scratch/sns-skill/` | `.agent/skills/sns/` | ✅ 移行完了（元ファイル残存） |
| `brain/08cba123.../homepage_production_skill.md` | `.agent/skills/website-production/` | ✅ 移行完了（汎用化済み） |
| `scratch/form_automation/PROCEDURE.md` | `.agent/skills/form-automation/SKILL.md` | ✅ 移行完了（元ファイル残存） |
| `scratch/.agent/skills/anticrow/` | — | 廃止（anticrowスキルは2026-07-07削除） |
| `scratch/.agent/skills/company_search/` | `.agent/skills/company-search/` | ✅ 移行完了（元ファイル残存） |
