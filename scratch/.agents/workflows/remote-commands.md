---
description: 外出先からDiscord経由でよく使うコマンドを自動承認で実行するワークフロー
---

# リモートコマンド実行ワークフロー

外出先から Discord (Anti-Crow) 経由で安全に実行できるコマンド集です。
すべてのコマンドステップに `// turbo` アノテーションが付いているため、承認なしで自動実行されます。

// turbo-all

## Git 操作

### 現在の状態を確認
// turbo
1. Git の状態を確認します
```bash
cd C:\Users\hangy\.gemini\antigravity\scratch && git status
```

### 最近のコミット履歴を確認
// turbo
2. 直近10件のコミット履歴を表示します
```bash
cd C:\Users\hangy\.gemini\antigravity\scratch && git log --oneline -n 10
```

### 変更差分を確認
// turbo
3. 未ステージの変更差分を表示します
```bash
cd C:\Users\hangy\.gemini\antigravity\scratch && git diff --stat
```

## Node.js プロジェクト操作

### form_automation の依存関係確認
// turbo
4. form_automation の package.json を確認します
```bash
cd C:\Users\hangy\.gemini\antigravity\scratch\form_automation && cat package.json
```

### form_automation のdev サーバー起動
// turbo
5. form_automation の開発サーバーを起動します
```bash
cd C:\Users\hangy\.gemini\antigravity\scratch\form_automation && npm run dev
```

## ファイル操作

### ワークスペースのファイル一覧
// turbo
6. ワークスペースのファイル構成を表示します
```bash
cd C:\Users\hangy\.gemini\antigravity\scratch && Get-ChildItem -Recurse -Depth 1 -Name
```

### ディスク使用量確認
// turbo
7. ワークスペースのサイズを確認します
```bash
cd C:\Users\hangy\.gemini\antigravity\scratch && Get-ChildItem -Recurse | Measure-Object -Property Length -Sum | Select-Object @{N='TotalSizeMB';E={[math]::Round($_.Sum/1MB,2)}}
```

## システム情報

### Node.js / npm バージョン確認
// turbo
8. Node.js と npm のバージョンを確認します
```bash
node --version && npm --version
```

### Python バージョン確認
// turbo
9. Python のバージョンを確認します
```bash
python --version
```

## Web サイト制作プロジェクト操作

### website_production のプロジェクト一覧
// turbo
10. website_production 内の全プロジェクトを一覧表示します
```bash
cd C:\Users\hangy\.gemini\antigravity\scratch\website_production && Get-ChildItem -Directory -Name
```

### 特定プロジェクトの index.html を確認
// turbo
11. 指定したプロジェクトの index.html の先頭50行を表示します（プロジェクト名は引数で指定）
```bash
cd C:\Users\hangy\.gemini\antigravity\scratch\website_production && Get-ChildItem -Directory -Name | ForEach-Object { if (Test-Path "$_\index.html") { Write-Host "=== $_ ===" ; Get-Content "$_\index.html" -TotalCount 5 ; Write-Host "" } }
```

### 特定プロジェクトのファイル構成
// turbo
12. website_production 内の各プロジェクトのファイル数を表示します
```bash
cd C:\Users\hangy\.gemini\antigravity\scratch\website_production && Get-ChildItem -Directory | ForEach-Object { $count = (Get-ChildItem $_.FullName -Recurse -File).Count; Write-Host "$($_.Name): $count files" }
```
