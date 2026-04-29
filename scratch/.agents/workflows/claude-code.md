---
description: AntigravityからClaude Codeを呼び出してタスクを実行する方法
---

# Claude Code 実行ワークフロー

Antigravityのターミナルから Claude Code エージェントにタスクを委任するワークフローです。

## 基本的な使い方

### 1. ワンショット実行（非対話・推奨）

ユーザーの指示を受け取り、Claude Code の `-p` フラグで実行します。

```powershell
claude -p "ここにユーザーの指示を記述" --output-format stream-json
```

// turbo-all

### 2. 自律モード（許可確認なし）

信頼できるタスクの場合、`--permission-mode auto` を付ける：

```powershell
claude --permission-mode auto -p "ここにユーザーの指示を記述"
```

### 3. 実行結果の確認

Claude Code の出力を確認し、ユーザーに結果を報告します。
エラーが発生した場合は、エラー内容を確認してリトライまたはユーザーに相談します。

## プロンプトのコツ

- **具体的なファイルを指す**: `@src/index.js のバグを修正して` のように `@` でファイルを指定
- **段階的に指示**: 「まず調査して、次に計画を立てて、最後に実装して」
- **検証方法を含める**: 「テストを実行して動作を確認して」

## 許可するツールを制限する例

```powershell
claude -p "コードをリファクタリングして" --allowedTools "Edit,Bash(git diff *)"
```

## 注意事項

- Claude Code と Antigravity で同じファイルを同時に編集しないこと
- 大規模な変更の前に Git でコミットしておくこと
- API使用量に注意すること（トークン消費）
