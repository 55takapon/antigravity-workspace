---
name: skill-management
version: 1.0.0
description: スキルの作り方・保存場所・命名規則・更新ルールを定めたメタスキル。新しいスキルを作るときは必ずこのファイルを参照する。
tags: [meta, skill-management, core]
updated: 2026-04-12
---

# 🧠 スキル管理コアスキル — スキルの作り方・育て方

> **このファイルの目的:** 新しいスキルを作るたびに「どこに・どんな形で・何を書くか」が統一されるよう、ルールを定める。

---

## 📍 スキルの保存場所（唯一の正解）

```
C:\Users\hangy\.gemini\antigravity\.agent\skills\
│
├── [スキル名]/
│   ├── SKILL.md          ← 必須：スキル本体
│   ├── README.md         ← 任意：使い方が複雑な場合
│   └── [サブフォルダ]/   ← 任意：テンプレート・案件データ等
│
└── README.md             ← 全スキル索引（このファイルを更新する）
```

> ⚠️ **`scratch/` や `brain/<会話ID>/` にスキルを保存しない。**
> スキルは必ず `.agent/skills/` に保存すること。

---

## 📁 現在のスキル一覧

| フォルダ名 | スキル内容 | バージョン |
|-----------|-----------|-----------|
| `anticrow/` | AntiCrow拡張機能の活用（チームモード・IPC通信等） | v1.1.0 |
| `gbp-meo-core/` | GBP投稿コアスキル（全業種共通） | - |
| `gbp-meo-beauty/` | 美容業種GBP投稿スキル | - |
| `gbp-meo-bodywork/` | ボディワーク業種GBP | - |
| `gbp-meo-education/` | 教育業種GBP | - |
| `gbp-meo-legal/` | 法律・士業GBP | - |
| `gbp-meo-medical/` | 医療業種GBP | - |
| `gbp-meo-real-estate/` | 不動産業種GBP | - |
| `gbp-meo-restaurant/` | 飲食業種GBP | - |
| `gbp-meo-retail/` | 小売業種GBP | - |
| `gbp-meo-service/` | サービス業GBP | - |
| `gbp-meo-post-core/` | GBP投稿文生成コアスキル | - |
| `gbp-meo-post-dental-occlusion/` | 歯科（咬合）GBP投稿 | - |
| `gbp-meo-post-dental-preventive/` | 歯科（予防）GBP投稿 | - |
| `gbp-meo-post-jetproduce/` | ジェットプロデュース専用GBP | - |
| `gbp-diagnostic/` | GBP診断レポート生成スキル | - |
| `sns/` | SNS投稿スキル（IG/Threads/FB/X） | v1.1 |
| `website-production/` | WordPress×SWELLホームページ制作 | v1.0 |
| `form-automation/` | Webフォーム自動入力スキル | v1.0 |
| `company-search/` | 企業検索・データ収集スキル | v1.6.0 |
| `company-search-quality-check/` | 企業リスト品質チェック（4軸MECE・必須実行） | v1.0.0 |
| `gbp-partner-research/` | GBPパートナー候補 業種リサーチ・キーワード設計 | v1.0.0 |
| `contact-auto/` | 企業お問い合わせフォーム自動送信（ハイブリッド型） | v0.1.0 |
| `skill-management/` | **このファイル**（スキルの作り方） | v1.0 |

---

## 🆕 新しいスキルの作り方（手順）

### STEP 1：スキル名を決める

命名規則: `[業務カテゴリ]-[具体的な用途]` （すべて小文字・ハイフン区切り）

```
✅ 良い例:
  website-production    ← 業務カテゴリ明確
  gbp-meo-dental        ← GBP + 業種
  form-automation       ← 機能を表す
  sns-instagram         ← SNS + プラットフォーム

❌ 悪い例:
  skill1                ← 内容不明
  sakakibara-hp         ← 案件名（汎用性なし）
  新スキル              ← 日本語・スペースはNG
```

### STEP 2：フォルダを作成する

```powershell
New-Item -ItemType Directory ".agent\skills\[スキル名]"
```

### STEP 3：SKILL.md を作成する

以下のテンプレートをコピーして使う：

```markdown
---
name: [スキル名（フォルダ名と同じ）]
version: 1.0.0
description: [1〜2行でスキルの目的を説明]
tags: [関連タグをカンマ区切りで]
updated: YYYY-MM-DD
---

# [スキルのタイトル]

## 🎯 このスキルの目的
[何のために使うか・どんな業務に使うか]

## 📋 使い方
[手順・チェックリスト・プロンプト等]

## ⚠️ 注意事項
[よくあるミス・NGパターン]

## 📈 バージョン履歴
| バージョン | 日付 | 更新内容 |
|-----------|------|---------|
| v1.0 | YYYY-MM-DD | 初版作成 |
```

### STEP 4：全索引（README.md）を更新する

`.agent/skills/README.md` の「現在のスキル一覧」テーブルに新しいスキルを追加する。

---

## ✏️ スキルの更新ルール

### いつ更新するか
- 新しいノウハウ・ベストプラクティスが生まれたとき
- 以前の方法よりも良い方法を発見したとき
- ツール・プラットフォームの仕様変更があったとき
- 失敗事例・注意点が増えたとき

### 更新時の手順
1. SKILL.md を編集
2. ファイル先頭の `updated:` 日付を更新
3. `version:` をインクリメント（バグ修正: patch, 機能追加: minor, 大幅変更: major）
4. `## 📈 バージョン履歴` に更新内容を追記

### バージョン番号の付け方（セマンティックバージョニング）
```
v[major].[minor].[patch]

例:
v1.0.0 → v1.0.1  ← 誤字修正・軽微な追記
v1.0.1 → v1.1.0  ← 新しいセクション・手順追加
v1.1.0 → v2.0.0  ← スキル全体の再設計・大幅改訂
```

---

## 🚫 スキルとして保存しないもの

以下は「スキル」ではなく、別の場所に保存する：

| 種類 | 保存場所 |
|------|---------|
| 特定案件の固有情報（金額・スケジュール） | スキルの `clients/` フォルダ または `scratch/` |
| 実行スクリプト（.js, .py, .ps1） | `scratch/[ツール名]/` |
| 会話で生成した一時的なファイル | `brain/<会話ID>/` |
| Webサイト制作の成果物（HTML等） | `scratch/website_production/` |
| クライアントのナレッジファイル | `knowledge/` |

---

## 🔍 スキルを参照するとき

AIに指示を出すとき、参照させたいスキルのパスを明示すると精度が上がる：

```
このスキルを読んで実行してください:
C:\Users\hangy\.gemini\antigravity\.agent\skills\[スキル名]\SKILL.md
```

---

## 📈 バージョン履歴

| バージョン | 日付 | 更新内容 |
|-----------|------|---------|
| v1.0.0 | 2026-04-12 | 初版作成（スキル散在問題の解決・統一ルール化） |

---
*スキル保存場所: `C:\Users\hangy\.gemini\antigravity\.agent\skills\skill-management\SKILL.md`*
