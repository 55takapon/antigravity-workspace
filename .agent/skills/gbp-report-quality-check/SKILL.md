---
name: gbp-report-quality-check
description: GBP月次レポートのHTML/PDF生成物が正しいかを機械的に検査・検証する。/gbp-report-quality-check で起動。
---

# gbp-report-quality-check

> GBP月次レポート生成後、異常値（閲覧数1桁など）や設定漏れ（ベンチマーク空欄など）がないかを自動チェックし、報告品質を担保する。

## 品質チェック手順

1. `batch_report.js` によるレポート生成完了後、必ずこのスキルを呼び出す。
2. `scripts/verify_report.js` を実行し、全クライアントのレポートを検査する。

```powershell
node .agent/skills/gbp-report-quality-check/scripts/verify_report.js
```

## NGパターン

- **目視チェックだけで済ませる**: AIの主観的な目視確認は漏れが生じるため、必ずスクリプトによる判定を通すこと。
- **エラーを無視して報告する**: スクリプトが1件でもエラー（NG）を出した場合は、ユーザーに報告する前に原因を特定・修正し、全件クリア（All OK）の状態にすること。

## ファイル構成

- `scripts/verify_report.js`: HTMLファイルをパースして、主要KPIやベンチマークの存在をテストするスクリプト。

## 変更履歴

- 2026-05-01: 初版作成（生成と検査の責務分離のため）
