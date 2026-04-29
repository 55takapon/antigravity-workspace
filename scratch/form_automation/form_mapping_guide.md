# フォーム入力項目 マッピングルール一覧
> **このファイルは `.gitignore` に登録されていません（センシティブ情報は含まない）。**  
> フォームで新しい項目に対応が必要になったら、対応するカテゴリの配列に追記してください。

---

## 自動入力の仕様まとめ

| 条件 | 動作 |
|---|---|
| 通常実行（デフォルト） | 「必須（required）」マークのある項目のみ入力 |
| `--all-fields` オプション付き | 必須・任意問わず全項目に入力 |
| **問い合わせ内容・件名** | **必須・任意に関係なく、常に入力する（固定仕様）** |
| プライバシーポリシー同意チェックボックス | 常に自動チェック |

---

## カテゴリ別 対応キーワード一覧

### 1. 氏名（一括入力）`name`
フォームのラベル・プレースホルダー・name属性が以下を含む場合に `form_profile.json` の `name` の値を入力します。
```
お名前 / 氏名 / ご氏名 / ご担当者 / ご担当者名 / ご担当者様名 / ご担当者様 / 名前 / 担当者名
name / your-name / your_name / full-name / fullname
```

### 2. 姓のみ（分離入力）`name_sei`
姓・名が別フィールドに分かれている場合、`name` の値（例:「田中 克章」）の **最初** の部分（田中）を自動で入力します。
```
姓（せい）/ 姓 / せい
last-name / lastname / family-name
```

### 3. 名のみ（分離入力）`name_mei`
上記と同様、**後半**部分（克章）を入力します。
```
名（めい）/ 名（名前）/ めい
first-name / firstname / given-name
```

### 4. フリガナ `kana`
```
フリガナ / ふりがな / カナ / かな / お名前（カナ）/ 氏名（かな）/ ご担当者様 氏名（かな）
せい（ひらがな）/ めい（ひらがな）
furigana / kana / yomi
```
> ※ 姓・名分離の場合は `kana` の先頭部分 / 後半部分をそれぞれ埋めます。

### 5. メールアドレス `email`
確認用フィールドも同じ値で埋めます（重複入力型）。
```
メールアドレス / メールアドレス（確認）/ メールアドレス確認用 / メールアドレス【確認用】
Eメール / E-mail / Mail Address / メール / ご連絡先メール
email / e-mail / mail / your-email / your_email / email-confirm / email_confirm
```

### 6. 電話番号 `phone` / 分離入力 `phone_1` `phone_2` `phone_3`
`form_profile.json` の `phone` をハイフンで自動分割します（例: `090-1021-9695` → `090` / `1021` / `9695`）。
```
【一括】電話番号 / お電話番号 / お電話 / 電話 / TEL / tel / phone / your-tel / your_tel
【分離1】tel-1 / tel_1 / phone-1 / phone_1 / 電話番号1 / tel1
【分離2】tel-2 / tel_2 / phone-2 / phone_2 / 電話番号2 / tel2
【分離3】tel-3 / tel_3 / phone-3 / phone_3 / 電話番号3 / tel3
```

### 7. 会社名・組織名 `company`
バッチ処理時は CSVリストの「企業名」列の値で自動上書きされます。
```
会社名 / 企業名 / 企業・団体名 / 団体名 / 会社名・店舗名・屋号名 / 組織名
御社名 / 貴社名 / 法人名 / 法人名・屋号 / 店舗名・屋号・社名・個人名 / 会社名・店名
事務所名 / 医院名
company / company-name / organization
```

### 8. 部署・役職 `department`
```
部署 / 部署名 / 所属部署 / 所属部署・担当 / 所属 / 役職
department / position
```

### 9. 件名・題名 `subject`
**【常時入力：任意でも必ず入力される】**
```
件名 / 題名 / お問い合わせの件名
subject / your-subject / your_subject
```

### 10. 問い合わせ内容・メッセージ本文 `message`
**【常時入力：任意でも必ず入力される】**  
バッチ処理時は `{{company}}`・`{{rep_name}}` のプレースホルダーがCSVの値で置換されます。
```
お問い合わせ内容 / ご相談内容 / 相談内容 / ご質問内容 / メッセージ本文 / メッセージ / 内容
詳細 / 具体的な内容 / ご要望 / ご依頼内容 / お問合せ内容
message / body / inquiry / your-message / your_message / content
```

### 11. ホームページURL `url`
```
ホームページURL / ホームページ / ウェブサイトURL / WEBサイト / WEBサイト（URL）
現在のWebサイトURL / 参考サイトURL / 改善対象のURL / URL
url / website / site-url
```

### 12. 住所 `address`
```
住所 / ご住所 / ご住所1 / ご住所2 / ご住所3 / 所在地 / 市区町村以降の住所
address / your-address
```

### 13. 郵便番号 `zipcode` / 分離入力 `zipcode_1` `zipcode_2`
`form_profile.json` の `address` 欄の `〒NNN-NNNN` を自動で分割します（例: `〒675-0042` → `675` / `0042`）。
```
【一括】郵便番号 / 〒 / zip / postal-code / postcode / zipcode
【分離1（上3桁）】zip-1 / zip_1 / postal-1 / zipcode1 / 郵便番号1
【分離2（下4桁）】zip-2 / zip_2 / postal-2 / zipcode2 / 郵便番号2
```

### 14. 都道府県 `prefecture`
```
都道府県 / prefecture / region
```

---

## 新しいバリエーションへの対応方法

実際のサイトで未入力になった項目があった場合、コンソールに以下のように出力されます：
```
--- Unmatched Fields ---
- Type: text, Name: "inquiry_type", Context: "ご相談の種別"
```
この `Context` の文字列を確認し、対応するカテゴリの配列に追記するだけで次回から自動入力されるようになります。
