# contact-form-assist 変更履歴

- 2026-07-17: 正本スキルとして新規作成。旧 form-automation（半自動・旧世代）/ contact-auto（全自動）は廃止し `skills-archive/2026-07-17-contact-tools-retirement/` へ退避。実行コードは `C:\Users\hangy\.cursor\test\contact-form-assist`（コード側に同名ポインタSKILL.mdを設置）
- 2026-07-17: コード品質改修を同時実施。(1) Googleサービスアカウント鍵をリポジトリ外 `%USERPROFILE%\.gcp\contact-form-assist\` へ隔離 (2) サーバー待ち受けを127.0.0.1に限定+WebSocket Origin検証追加 (3) URL正規化がクエリ文字列を捨てて二重送信防止が誤爆するバグを修正（DBキー811行中11行を再計算移行） (4) CLIモードで `{{rep_salutation}}` が未置換になるバグを修正（共通ライブラリ `src/lib/common.js` に統一） (5) CSVパーサを引用符対応に修正 (6) 強制キャンセル時のDB二重更新・ゾンビブラウザを修正 (7) 営業NGワードを旧contact-autoの90+と統合し `config/ng-keywords.json`（117語）へ外部化 (8) evidence/html も3日保持の日次クリーンアップ対象に追加
