# Antigravity ワークスペース

Antigravity (AI コーディングアシスタント) の作業ディレクトリです。
Web開発、自動化スクリプト、データ処理など多目的に使用しています。

## ディレクトリ構成

```
scratch/
├── .agents/workflows/       # Antigravity ワークフロー定義
├── chatgpt_automation/      # ChatGPT 連携ツール
├── company_search/          # 企業検索ツール（スキル: ../.agent/skills/company-search/）
├── form_automation/         # フォーム自動入力ツール（スキル: ../.agent/skills/form-automation/）
├── google_maps_data/        # Google Maps データ収集
├── sns-skill/               # SNS投稿スキルの旧フォルダ（移行先: ../.agent/skills/sns/）
├── website_production/      # Webサイト制作プロジェクト成果物（21サイト）
│   ├── michi-lp/            # お好み焼き「道」LP
│   ├── sakakibara-tax/      # 榊原税理士事務所
│   ├── shibamoto-office/    # 柴本司法書士事務所
│   ├── luxury-salon-website/ # 高級サロンサイト
│   ├── nagomi-seitai/       # なごみ整体
│   └── ... (他16サイト)
└── *.py / *.ps1             # ユーティリティスクリプト
```

## 主なプロジェクト

### 🌐 Web サイト制作 (`website_production/`)
クライアント向けの LP・コーポレートサイトを制作。HTML/CSS/JS で構築。
現在 21 のプロジェクトが格納されています。

### 📝 フォーム自動化 (`form_automation/`)
Playwright ベースの Web フォーム自動入力ツール。
Google Sheets API と連携し、企業への営業フォーム送信を一括処理。
> 📚 **スキルは移行済み:** `C:\Users\hangy\.gemini\antigravity\.agent\skills\form-automation\SKILL.md`

### 🔍 企業検索 (`company_search/`)
企業情報の検索・収集ツール。

### 🤖 ChatGPT 連携 (`chatgpt_automation/`)
ChatGPT を活用した自動化ツール。

## 環境情報

| 項目 | バージョン |
|------|-----------|
| OS | Windows 10+ |
| Node.js | v22 |
| Python | 利用可能 |
| Shell | PowerShell |
| Git | インストール済 |
| エディタ | Antigravity |

## ワークフロー

- `.agents/workflows/remote-commands.md` — 外出先から Discord 経由で実行可能な turbo コマンド集
- `.agents/workflows/claude-code.md` — Claude Code 関連ワークフロー
