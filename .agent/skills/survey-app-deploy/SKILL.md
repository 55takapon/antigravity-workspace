---
name: survey-app-deploy
description: |
  店舗向け星評価アンケートアプリ（survey-app）の新規クライアント複製・Netlifyデプロイ・テキスト変更・再デプロイの手順スキル。
  「アンケートアプリを作って」「新しいクライアントのアンケート」「デプロイして」などで起動。/survey-app-deploy で起動。
---

# survey-app-deploy

> 店舗向け星評価アンケートアプリをクライアントごとに複製・公開するための完全手順。

---

## 前提知識

### アプリの動作仕様
- 星1〜3（閾値以下）→ `lowRatingUrl` へ遷移（低評価フォーム）
- 星4〜5 → `highRatingUrl` へ遷移（Google口コミページ）
- 全設定は `js/app.js` の `CONFIG` オブジェクト1か所で管理

### フォルダ構成
```
C:\Users\hangy\.gemini\antigravity\scratch\survey-app\
├── _template/          ← コピー元テンプレート（触らない）
│   ├── index.html
│   ├── css/style.css   ← フォント最小16px設定済み
│   ├── js/app.js       ← CONFIG はプレースホルダー
│   └── img/
├── namba-dental/       ← なんば歯科医院
├── jetproduce/         ← ジェットプロデュース
├── （クライアントID）/  ← 追加クライアントはここに増やす
├── new-client.ps1      ← 複製スクリプト
└── README.md
```

### 低評価フォーム方式の選択（必ずクライアントに確認）

| 方式 | feedback.html | 必要なURL | 特徴 |
|---|---|---|---|
| **埋め込み（推奨）** | **必要** | `viewform?embedded=true` の長いURL | アプリ内でフォーム表示。離脱感なし |
| **直接リダイレクト** | 不要 | `forms.gle/...` 短縮URLでもOK | シンプル。Googleフォームに直接飛ぶ |

> ⚠️ **事前確認必須：** どちらの方式にするか、クライアントに確認してから着手すること。勝手に切り替えない。

---

## STEP 1：クライアント情報を収集する（確認必須）

以下を必ずユーザーに確認してから作業開始：

```
□ クライアントID（フォルダ名）: 半角英数字+ハイフン例: hakata-izakaya
□ 店舗名（日本語可）: CONFIG.shopName
□ ロゴ画像: あり→img/logo.png に配置 / なし→絵文字(shopEmoji)を設定
□ 絵文字（ロゴなし時）: CONFIG.shopEmoji
□ subtitle テキスト: CONFIG.subtitle（改行は \n）
□ 高評価URL（星4-5）: Google口コミURL
□ 低評価方式: 埋め込み or 直接リダイレクト
□ 低評価URL: Googleフォームの長いURL（埋め込み）or 短縮URL（直接）
□ フォントサイズ: 最小16px（デフォルト・変更なし）
```

---

## STEP 2：テンプレートから複製する

```powershell
cd C:\Users\hangy\.gemini\antigravity\scratch\survey-app
.\new-client.ps1 -ClientId "クライアントID"
```

→ `_template/` がコピーされて `クライアントID/` フォルダが作成される。

---

## STEP 3：CONFIG を編集する

`クライアントID/js/app.js` を開いて以下を設定：

```javascript
const CONFIG = {
  shopName: "店舗名",
  shopLogo: "img/logo.png",   // ロゴあり → このまま / なし → "" に変更
  shopEmoji: "🏪",            // ロゴなし時の絵文字

  lowRatingUrl: "https://...", // 低評価フォームURL or "./feedback.html"
  highRatingUrl: "https://maps.app.goo.gl/xxxxx",

  ratingThreshold: 3,

  title: "アンケート",
  subtitle: "ご利用ありがとうございます。\nサービスの満足度をお聞かせください。",
  buttonText: "次へ",
  footer: "ご協力ありがとうございます",

  ratingLabels: {
    1: "不満", 2: "やや不満", 3: "普通", 4: "満足", 5: "とても満足",
  },
};
```

---

## STEP 3b：埋め込み方式の場合のみ — feedback.html を作成

`namba-dental/feedback.html` をコピーして `クライアントID/feedback.html` に配置し、以下を編集：

```javascript
const FORM_CONFIG = {
  formEmbedUrl: "https://docs.google.com/forms/d/e/XXXXXXXXXX/viewform?embedded=true",
  // ↑ ?usp=header や ?usp=sf_link を ?embedded=true に変更すること
  shopName: "店舗名",
  shopEmoji: "🏪",
};
```

`app.js` の `lowRatingUrl` は `"./feedback.html"` にする。

---

## STEP 4：ロゴ画像を配置する（ロゴありの場合）

```
クライアントID/img/logo.png  ← ここに配置
```

- 正方形・円形どちらでもOK（CSS側で円形にトリミングされる）
- .gitignore で `*.png` が除外されているため **GitHub経由でNetlifyに反映されない**
- 必ず **CLIでローカルからデプロイ** すること（後述STEP 5）

---

## STEP 5：Netlifyにデプロイする

### 初回デプロイ（新規サイト作成）

```powershell
cd C:\Users\hangy\.gemini\antigravity\scratch\survey-app\クライアントID
netlify deploy --dir="." --prod --message "初回デプロイ"
```

→ 自動的に新サイトが作成される（ランダム名）

### サイト名を変更する（必須）

```powershell
# サイトIDを確認
netlify sites:list --json 2>&1 | ConvertFrom-Json | Where-Object { $_.default_domain -like "*ランダム名*" }

# APIでサイト名変更（PowerShell）
$token = (Get-Content "C:\Users\hangy\AppData\Roaming\netlify\Config\config.json" -Raw | ConvertFrom-Json).users.default.auth.token
$headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
Invoke-RestMethod -Method Patch -Uri "https://api.netlify.com/api/v1/sites/サイトID" -Headers $headers -Body '{"name":"クライアントID-survey"}'
```

### 再デプロイ（更新時）

```powershell
netlify deploy --dir="C:\Users\hangy\.gemini\antigravity\scratch\survey-app\クライアントID" --prod --site="サイトID" --message "変更内容"
```

---

## STEP 6：動作確認

- [ ] 星1〜3 → 低評価フォームへ遷移するか
- [ ] 星4〜5 → Google口コミページへ遷移するか
- [ ] ロゴが表示されているか（画像 or 絵文字）
- [ ] 全テキストが16px以上か（フッター含む）
- [ ] スマホ表示で崩れていないか

---

## STEP 7：Gitにコミットする

```powershell
cd C:\Users\hangy\.gemini\antigravity
git add -A scratch/survey-app/クライアントID/
git commit -m "feat: クライアント名 アンケートアプリ追加"
git push origin main
```

> ⚠️ ロゴ画像（*.png）は .gitignore で除外される。Netlifyへの反映はCLI直接デプロイのみ。

---

## 既存クライアント一覧

| クライアントID | 店舗名 | Netlify URL | 低評価方式 | サイトID |
|---|---|---|---|---|
| `namba-dental` | なんば歯科医院 | https://namba-dental-survey.netlify.app | 埋め込み（feedback.html） | c4553664-e06a-4d45-a982-b6e7416fe18c |
| `jetproduce` | ジェットプロデュース | https://jetproduce-survey.netlify.app | 直接リダイレクト | 45c9cb6b-806a-4ba4-92e8-488dd2cef15c |

---

## NGパターン（過去の失敗事例）

- ❌ 低評価方式を確認せずに勝手に切り替えた → 必ず事前確認
- ❌ GitHub連携（auto-deploy）でデプロイ → ロゴ画像が反映されない、base dir設定でバグ発生。CLIデプロイを使う
- ❌ forms.gle 短縮URLをiframeのsrcに使った → 埋め込みは長いURLの `?embedded=true` が必要
- ❌ ブラウザ操作でNetlify設定を変更しようとした → APIかCLIを使う
- ❌ namba-dental の旧style.css（font-size-xs: 0.75rem）を流用 → `_template` から複製すること

---

## 変更履歴

- 2026-05-14: 初版作成（namba-dental/jetproduce の構築・デプロイ経験から）
