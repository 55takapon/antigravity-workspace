# 店舗アンケートシステム — マルチクライアント管理

星評価で分岐する店舗向けアンケートシステムです。  
クライアントごとにフォルダを分けて管理します。

---

## 📁 フォルダ構成

```
survey-app/
├── _template/        ← コピー元テンプレート（編集しない）
│   ├── index.html
│   ├── css/style.css
│   ├── js/app.js     ← CONFIG はプレースホルダー
│   └── img/
│
├── namba-dental/     ← なんば歯科医院
├── jetproduce/       ← ジェットプロデュース
├── （クライアントID）/  ← 追加クライアント
│
├── new-client.ps1    ← 新規複製スクリプト
└── README.md         ← このファイル
```

---

## 🚀 新規クライアントを追加する

```powershell
# survey-app フォルダで実行
.\new-client.ps1 -ClientId "client-folder-name"

# 例
.\new-client.ps1 -ClientId "hakata-izakaya"
.\new-client.ps1 -ClientId "umeda-beauty"
```

作成後、`js/app.js` の CONFIG だけ編集すれば完成です。

---

## ⚙️ CONFIG 編集箇所（js/app.js）

```javascript
const CONFIG = {
  shopName: "店舗名",          // ← 変更
  shopLogo: "img/logo.png",   // ← ロゴ画像があれば設定（なければ空文字）
  shopEmoji: "🏪",            // ← ロゴなし時の絵文字

  lowRatingUrl:  "https://forms.gle/xxxxx",        // ← 低評価フォームURL
  highRatingUrl: "https://maps.app.goo.gl/xxxxx",  // ← Google口コミURL

  ratingThreshold: 3,  // この値以下が lowRatingUrl へ遷移
  subtitle: "ご利用ありがとうございます。\nサービスの満足度をお聞かせください。",
};
```

---

## ▶️ ローカル確認

```powershell
cd namba-dental   # or jetproduce / クライアントID
npx -y serve .
# → http://localhost:3000 で確認
```

---

## 📋 クライアント一覧

| フォルダ名 | クライアント | 備考 |
|---|---|---|
| `namba-dental` | なんば歯科医院 | Navy theme・feedback.html あり |
| `jetproduce` | ジェットプロデュース | Navy theme・フォント16px対応 |
