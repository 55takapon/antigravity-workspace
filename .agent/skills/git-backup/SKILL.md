---
name: git-backup
description: |
  GitHubへのバックアップを実行するスキル。
  手動で「バックアップして」「gitに保存して」と言われたとき、または作業区切りのタイミングで必ず使用する。
  sync-github.ps1 スクリプトを呼び出してコミット＆プッシュを行う。
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

### 完了確認

実行後、スクリプト出力に push 成功（または `up to date`）が出ていることを必ず確認すること。
push 成功を確認するまで、バックアップ作業を完了扱いにしてはならない。

具体的な入力→出力の例は [examples/good-output.md](examples/good-output.md) を参照（必要なときだけ読む）。

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

## 禁止事項

- コマンド連結に `&&` を使ってはならない（PowerShellでは `;` またはスクリプトを使う）
- non-fast-forward 拒否の第一手として `git push --force` を使ってはならない（必ず `git pull --rebase` を先に試す）
- `*credentials*.json` 等の認証ファイルを `.gitignore` から外したり、手動で `git add -f` してはならない
- リポジトリルート以外のディレクトリから `sync-github.ps1` を実行してはならない

---

## エッジケース

| 状況 | 対応 |
|:-----|:-----|
| push が non-fast-forward で拒否された | `git pull --rebase origin main` → `git push origin main`（スクリプトは自動で rebase する） |
| GitHub Secret Protection でブロックされた | 過去コミットに認証ファイルが含まれている。`git filter-branch` で履歴から完全削除後に push（詳細手順は下記） |
| `google_credentials.json` が衝突・退避された | スクリプトが `pull --rebase` 時に自動退避・復元する。手動操作不要 |
| 画像・brain/ がコミットされない | `.gitignore` で除外済み（`*.png` / `*.jpg` / `*.webp` / `brain/` / `node_modules/`）。仕様であり異常ではない |

### Secret Protection ブロック時の履歴削除手順

```powershell
$env:FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch --force --index-filter `
  "git rm --cached --ignore-unmatch <ファイルパス>" `
  --prune-empty --tag-name-filter cat -- --all
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin main --force
```

※ この force push は履歴書き換え後の唯一の手段である場合のみ使う。

---

## 自己完了確認（省略禁止）

- [ ] リポジトリルートから `sync-github.ps1` を実行したか
- [ ] コミットメッセージがプレフィックス規則に従っているか
- [ ] push 成功（または `up to date`）を出力で確認したか

---

## 変更履歴

変更履歴は [references/changelog.md](references/changelog.md) に分離。

## NGパターン（NG_RULES棚卸しにより移管・このスキル実行時は必読）

| ID | When（いつ） | What（何をする/しないか） | How to verify（検証方法） |
|---|---|---|---|
| E-01 | Git でファイルをバックアップする時 | **`.gitignore` のパターンを事前に確認する。** 意図せず除外されているファイルがないかチェックし、必要なら `git add -f` を使用する。 | `git status` で追跡対象ファイルが正しく staging されていることを確認する。 |
| E-02 | ログ系ディレクトリを新規作成する時 | **作成と同時に `.gitignore` にそのパスを追加する。** | `git status` にログファイルが untracked として表示されないことを確認する。 |
