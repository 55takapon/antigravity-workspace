# 店舗アンケートシステム

星評価で分岐する店舗向けアンケートシステムです。

## 🚀 使い方

### ローカルで起動

```bash
# survey-app ディレクトリで
npx -y serve .
```

ブラウザで `http://localhost:3000` を開きます。

### カスタマイズ

`js/app.js` 先頭の `CONFIG` オブジェクトを編集してください：

```javascript
const CONFIG = {
  shopName: "居酒屋ちょうちん",    // 店舗名
  shopLogo: "",                    // ロゴ画像パス（空=絵文字表示）
  shopEmoji: "🏮",                // shopLogoが空の時に表示

  lowRatingUrl: "https://...",     // 星1-3の遷移先
  highRatingUrl: "https://...",    // 星4-5の遷移先

  ratingThreshold: 3,             // この値以下がlowRatingUrl
};
```

### 店舗ロゴ画像の設定

1. `img/` フォルダにロゴ画像を配置
2. `CONFIG.shopLogo` にパスを設定（例: `"img/logo.jpg"`）
3. 四角い画像でもOK → 自動的に円形にトリミングされます

## 📁 ファイル構成

```
survey-app/
├── index.html      ← メインページ
├── css/
│   └── style.css   ← スタイル
├── js/
│   └── app.js      ← ロジック＋設定
├── img/             ← ロゴ画像配置先
└── README.md        ← このファイル
```
