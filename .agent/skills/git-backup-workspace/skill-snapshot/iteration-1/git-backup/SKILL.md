---
name: git-backup
description: |
  GitHubへのバックアップを実行するスキル。
  手動で「バックアップして」「gitに保存して」と言われたとき、または作業区切りのタイミングで使用する。
  sync-github.ps1 スクリプトを呼び出してコミット＆プッシュを行う。
version: "1.0.0"
tools:
  - run_command
---

> ⚠️ **作業開始前に必ず knowledge/chat_ng_registry/artifacts/NG_RULES.md を読み、Pre-flight Check を実行すること。**


# Git バックアップスキル

## 概要

このスキルは、作業内容をGitHubリポジトリにバックアップするための手順を定義します。

**リポジトリルート**: `C:\Users\hangy\.gemini\antigravity`  
**リモート**: `https://github.com/55takapon/antigravity-workspace.git`  
**ブランチ**: `main`

---

## 実行手順

### 1. 一回だけバックアップ（通常使用）

```powershell
cd C:\Users\hangy\.gemini\antigravity
.\sync-github.ps1 -Once
```

### 2. カスタムメッセージ付きでバックアップ

```powershell
.\sync-github.ps1 -Once -Message "feat: 新機能追加"
```

### 3. 定期自動バックアップ（5分ごと）

```powershell
.\sync-github.ps1
# Ctrl+C で停止
```

---

## 注意事項・既知の問題

### ⚠️ google_credentials.json について
- `.gitignore` で除外済みだが、**過去コミットに含まれていた場合** GitHub Secret Protection でブロックされる
- スクリプトは `pull --rebase` 時に自動的にファイルを退避・復元する

### ⚠️ .gitignore で除外されているファイル
```
*credentials*.json     # Google認証ファイル
*.png / *.jpg / *.webp # 画像ファイル（スクショ等）
brain/                 # 会話ログ
node_modules/          # パッケージ
```

### ⚠️ PowerShell の && 問題
PowerShellでは `&&` 演算子が使えないため、必ず `;` を使うか、スクリプトを使う。

---

## コミットメッセージ規則

| プレフィックス | 用途 |
|---|---|
| `backup:` | 定期自動バックアップ |
| `feat:` | 新機能・新スキル追加 |
| `fix:` | バグ修正 |
| `refactor:` | リファクタリング |
| `docs:` | ドキュメント更新 |

---

## トラブルシューティング

### push が拒否された場合（non-fast-forward）
```powershell
# 自動スクリプトが pull --rebase を行う
# 手動の場合：
git pull --rebase origin main
git push origin main
```

### GitHub Secret Protection でブロックされた場合
```powershell
# 対象ファイルを履歴から完全削除
$env:FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch --force --index-filter `
  "git rm --cached --ignore-unmatch <ファイルパス>" `
  --prune-empty --tag-name-filter cat -- --all
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin main --force
```
