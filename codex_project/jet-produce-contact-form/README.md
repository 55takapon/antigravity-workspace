# Jet Produce Contact Form

ジェットプロデュース公式サイト用の Contact Form 7 貼り付けコード一式です。

## ファイル

- `contact-form-7-form.txt`  
  Contact Form 7 の「フォーム」タブに貼り付けます。

- `mail-settings.txt`  
  Contact Form 7 の「メール」タブに設定する内容です。件名の先頭に `[inquiry-type]` を入れています。

- `additional.css`  
  WordPress 管理画面の「外観 > カスタマイズ > 追加CSS」に貼り付けます。

- `preview.html`  
  見た目確認用の静的HTMLです。ブラウザで直接開けます。

## 実装メモ

- CSSの接頭辞は `jp-contact-` に統一し、WordPressテーマやSWELL系classとの衝突を避けています。
- ラジオボタンは Contact Form 7 の標準出力を前提に、カード型の選択UIへ整えています。
- 受信メールの件名は `[お問い合わせ]` のような角括弧ではなく、選択値をそのまま先頭に置く形式です。
  例: `協業 ジェットプロデュースへのお問い合わせ`
