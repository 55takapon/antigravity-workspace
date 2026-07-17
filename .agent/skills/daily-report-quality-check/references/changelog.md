# daily-report-quality-check 変更履歴

- 2026-07-17: daily-report v3再建に追随。PHASE 1をcollector v3.0前提に更新（絶対パス・--date引数・終了コード2の扱い・リクエスト一覧とDONEの照合を追加）。client_registry.js の実パス（gbp-monthly-report内）と非GBPクライアントの照合方法を明記。呼び出し導線を「daily-reportステップ5から必ず呼ばれる」に修正（従来は本スキルだけが連携を自認する片方向参照だった）
- 2026-05-01: 初版作成（レポート漏れ防止のため、生成と検査の責務分離）
