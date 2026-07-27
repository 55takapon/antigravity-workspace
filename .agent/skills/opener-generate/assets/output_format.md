# 出力フォーマット

## 出力CSV
入力の統一CSVに `message` 列を追加したもの（既存列は保持）。

| 列 | 内容 |
|---|---|
| company_name, url, contact_url, ... | 入力のまま |
| message | 生成した「冒頭文 + 共通本文」。失敗社は空 or 既存値 |

## message の構造
```
<その会社向けの冒頭文（2〜4文）>

<shared/common_body.md の共通本文>
```
冒頭文と共通本文の間は空行1つで区切る（`generate_openers.py` が結合）。

## 後段（form-send）との接続
- form-send は `message` 列をそのまま送信本文として使う。
- 送信先URLは `contact_url`（無ければ `url`）。form-send 側のアダプタが詰め替える。
