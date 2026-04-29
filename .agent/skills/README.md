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

## 📋 スキル一覧

### 🛠️ システム・ツール系

| スキル名 | 概要 | フォルダ |
|---------|------|---------|
| **スキル管理** | スキルの作り方・命名規則・更新ルール（このREADMEの親） | `skill-management/` |
| **AntiCrow** | Discord経由AIエージェント連携（チームモード・IPC通信） | `anticrow/` |
| **フォーム自動入力** | PlaywrightでWebフォームに自動入力（Google Sheets連携） | `form-automation/` |
| **企業検索** | 企業情報の検索・収集・Sheets書き込み | `company-search/` |

### 📱 SNS・コンテンツ系

| スキル名 | 概要 | フォルダ |
|---------|------|---------|
| **SNS投稿** | Instagram/Threads/Facebook/Xの投稿生成・戦略 | `sns/` |

### 🌐 Web制作系

| スキル名 | 概要 | フォルダ |
|---------|------|---------|
| **ホームページ制作** | WordPress×SWELLの全工程（企画→デザイン→構築→公開） | `website-production/` |

### 📊 GBP・MEO系（Googleビジネスプロフィール）

| スキル名 | 概要 | フォルダ |
|---------|------|---------|
| **GBPコア** | GBP投稿の共通戦略・品質基準 | `gbp-meo-core/` |
| **GBP診断** | クライアントGBPの診断レポート生成 | `gbp-diagnostic/` |
| **GBP投稿コア** | GBP投稿文生成の共通スキル | `gbp-meo-post-core/` |
| **GBP歯科（咬合）** | 噛み合わせ特化歯科向け投稿 | `gbp-meo-post-dental-occlusion/` |
| **GBP歯科（予防）** | 予防歯科特化向け投稿 | `gbp-meo-post-dental-preventive/` |
| **GBPジェットプロデュース** | ジェットプロデュース専用投稿スキル | `gbp-meo-post-jetproduce/` |
| **GBP美容** | 美容院・エステ向け | `gbp-meo-beauty/` |
| **GBPボディワーク** | 整体・マッサージ向け | `gbp-meo-bodywork/` |
| **GBP教育** | 塾・スクール向け | `gbp-meo-education/` |
| **GBP士業** | 法律・税理士・司法書士向け | `gbp-meo-legal/` |
| **GBP医療** | 医療・クリニック向け | `gbp-meo-medical/` |
| **GBP不動産** | 不動産向け | `gbp-meo-real-estate/` |
| **GBP飲食** | 飲食店向け | `gbp-meo-restaurant/` |
| **GBP小売** | 小売店向け | `gbp-meo-retail/` |
| **GBPサービス業** | その他サービス業向け | `gbp-meo-service/` |

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
├── anticrow/                     ← AntiCrow連携
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
├── gbp-meo-core/
├── gbp-diagnostic/
├── gbp-meo-post-core/
├── gbp-meo-post-dental-occlusion/
├── gbp-meo-post-dental-preventive/
├── gbp-meo-post-jetproduce/
├── gbp-meo-beauty/
├── gbp-meo-bodywork/
├── gbp-meo-education/
├── gbp-meo-legal/
├── gbp-meo-medical/
├── gbp-meo-real-estate/
├── gbp-meo-restaurant/
├── gbp-meo-retail/
└── gbp-meo-service/
```

---

## 🗂️ 旧保存場所との対応表（移行記録）

| 旧パス | 新パス | 状態 |
|--------|--------|------|
| `scratch/sns-skill/` | `.agent/skills/sns/` | ✅ 移行完了（元ファイル残存） |
| `brain/08cba123.../homepage_production_skill.md` | `.agent/skills/website-production/` | ✅ 移行完了（汎用化済み） |
| `scratch/form_automation/PROCEDURE.md` | `.agent/skills/form-automation/SKILL.md` | ✅ 移行完了（元ファイル残存） |
| `scratch/.agent/skills/anticrow/` | `.agent/skills/anticrow/` | ✅ 同一内容（anticrowは自動配置） |
| `scratch/.agent/skills/company_search/` | `.agent/skills/company-search/` | ✅ 移行完了（元ファイル残存） |
