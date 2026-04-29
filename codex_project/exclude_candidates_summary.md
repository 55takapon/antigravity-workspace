# 除外候補リスト サマリー

対象: 2つのGoogleスプレッドシートの全シート。ただし、シート名が「除外リスト」のものは対象外。

出力ファイル: `exclude_candidates_from_duplicates.csv`

## 件数

- チェック対象レコード数: 9,798
- 除外候補キー数: 2,031
- `exclude_strong`: 1,948
- `exclude_review`: 48
- `review`: 35

## 判定ラベル

- `exclude_strong`: 除外候補（強）。企業名+ドメイン、または代表者名+ドメインが複数回一致したもの。
- `exclude_review`: 除外候補（要確認）。同一ドメインに複数の企業名表記があるものが中心。
- `review`: 確認候補。同一企業名が複数の非共有ドメインで出ているものが中心。

## 理由コード

- `company_domain_duplicate`: 企業名とドメインが一致する行が複数ある。
- `representative_domain_duplicate`: 代表者名とドメインが一致する行が複数ある。
- `same_domain_multiple_company_names`: 同一ドメインに複数の企業名が紐づいている。表記ゆれ、ブランド名、支社名、グループ会社名の混在が疑われる。
- `same_company_multiple_domains`: 同一企業名が複数ドメインで出ている。関連サイト、旧ドメイン、サービスサイト、または同名別会社の可能性がある。

## 補足

`peraichi.com`、`studio.site`、`job-gear.net`、主要SNSなどの共有ホスト系ドメインは、ドメイン単位の除外キーにはしていません。無関係な企業までまとめて除外する誤判定を避けるため、共有ホスト系は企業名を除外キーとして扱っています。
