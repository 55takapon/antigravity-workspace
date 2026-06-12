# git-backup 変更履歴

- （初版）: GitHubバックアップ手順を定義（sync-github.ps1 / コミットメッセージ規則 / トラブルシューティング）。frontmatter に version: "1.0.0" と tools: を含んでいた
- 2026-06-13: skill-update 手動フローの初回通し検証として改善。非公式 frontmatter フィールド（version / tools）を削除、禁止事項・エッジケース表・完了確認・自己完了確認を追加、トラブルシューティングをエッジケース表に統合、examples/good-output.md（評価ケース実出力3件）と本ファイルを新設。旧版比較: pass率 100%→100%（回帰なし）、自動修正ゲート allowed
