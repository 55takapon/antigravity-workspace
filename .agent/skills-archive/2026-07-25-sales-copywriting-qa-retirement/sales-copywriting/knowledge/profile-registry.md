# プロファイル台帳（実在ファイルの正本一覧）

送信プロファイル（提案文＋差出人情報のJSON）の実在状況を管理する台帳。**実ファイルが正**であり、食い違いがあればこの台帳側を更新する。

## 正本置き場

```
C:\Users\hangy\.cursor\test\contact-form-assist\config\profiles\
```

送信実行は contact-form-assist スキルが担当。プロファイルは追加のみ（上書き禁止、`[業種]-v[N].json` 形式）。

## 稼働中プロファイル

| ファイル | 対象業種 | 備考 |
|:---------|:---------|:-----|
| web-company.json | ホームページ制作会社 | ⚠️ message が約1,500字あり、本スキルの1,000字未満制約を超過している疑い。次回改善時に sales-copywriting-qa で要検査 |
| web-marketing.json | Webマーケティング会社 | |
| web-production.json | Web制作会社 | |

## 廃止済みの旧置き場（参照禁止）

```
C:\Users\hangy\.gemini\antigravity\scratch\contact-auto\config\profiles\
```

- web-company.json / marketing-company.json の初期版が残置（PDCAの差分履歴として残す。新規参照・更新は禁止）
- contact-auto / form-automation スキル自体が廃止済み。正本は contact-form-assist

## 計画中テンプレート（未作成）

初版設計時に構想し、まだプロファイル化されていないもの。作成したら「稼働中」へ移す。

| ID | 業種 | 提案タイプ | フレームワーク |
|:--|:-----|:----------|:--------------|
| T-03 | 広告代理店 | パートナー提案 | BAB |
| T-04 | クリニック系支援会社 | パートナー提案 | PAS |
| T-05 | 飲食店舗集客支援会社 | パートナー提案 | BAB |
| T-06 | 美容系支援会社 | パートナー提案 | PAS |
| T-07 | 士業専門コンサル会社 | パートナー提案 | AIDA |
| L-01 | 歯科クリニック | お手紙営業（手書き・フォーム外） | 別設計 |
