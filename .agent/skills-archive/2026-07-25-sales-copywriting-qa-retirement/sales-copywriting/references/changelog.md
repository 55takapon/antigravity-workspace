# 変更履歴

- 2026-05-05: 初版作成
  - 全議論反映: 成約はゴールではなくスタート、煽りと事実共有の区別、3行プレビュー勝負、読み手のエネルギーを奪わない設計、バージョン管理ルール
  - 送信対象を B2B（フォームあり）に絞り込み。直接BtoCは対象外
  - 歯科クリニックはお手紙営業タイプ（L-01）として別途設計
  - sales-copywriting-qa スキルと連携
- 2026-07-17 v2.0: skill-update による連携修復と規約準拠の全面改修
  - 廃止済み contact-auto への連携・パス参照（scratch/contact-auto/config/profiles）を、正本 contact-form-assist（C:\Users\hangy\.cursor\test\contact-form-assist\config\profiles）へ全面付け替え
  - knowledge/profile-registry.md を新設（稼働中3プロファイル・廃止旧置き場・計画中テンプレT-03〜T-07/L-01の台帳。実ファイルを正とする）
  - リファレンス集だった本体を5ステップのワークフロー化（対象判定→設計→執筆→文字数実測+QA必須→バージョン付き反映）
  - 本体3,379トークン→2,000トークン以下に再編。送り先の現実・運用前提・3人の頭脳を references/02_sending-context.md へ移設（内容は全保持）
  - description にトリガー語・成果物・連携先を追加
  - 変更履歴を本文からこのファイルへ分離
  - 発見事項: 稼働中 web-company.json の message が約1,500字で1,000字未満制約を超過している疑い（台帳に要検査として記録。実ファイルは未編集）
