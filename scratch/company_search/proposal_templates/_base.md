# GBPパートナー協業提案文テンプレート（共通ベース）

---

## 変数一覧

| 変数 | 内容 | 取得元 |
|---|---|---|
| `{company_name}` | 企業名 | crawler.jsで自動取得 |
| `{representative}` | 代表者名（不明時「ご担当者」） | crawler.jsで自動取得 |
| `{region}` | 地域名 | config.yaml |
| `{category_name}` | カテゴリ表示名 | categories.yaml |
| `{cooperation_reason}` | 協業理由 | categories.yaml |
| `{approach_angle}` | アプローチ角度 | categories.yaml |

---

## ベーステンプレート

```
件名: 【協業のご提案】Googleビジネスプロフィール運用支援のパートナーシップについて

{company_name}
{representative}様

突然のご連絡失礼いたします。
Googleビジネスプロフィール（MEO）の運用支援を専門に行っております、
[あなたの会社名] の [あなたの名前] と申します。

貴社のWebサイトを拝見し、{category_name}として素晴らしいサービスを
展開されていることに大変感銘を受け、ご連絡差し上げました。

■ ご提案の背景
{cooperation_reason}

■ 協業イメージ
{approach_angle}

■ 当社が提供できること
・Googleビジネスプロフィールの初期設定・最適化
・投稿コンテンツの企画・運用代行
・口コミ管理・返信代行
・MEOレポーティング・効果測定
・御社のクライアント様への共同提案資料作成

■ 御社のメリット
・既存クライアント様へのアップセルメニュー追加
・GBP運用の実務負担ゼロで新たな収益源を創出
・成果報酬型・レベニューシェアなど柔軟な契約形態に対応

まずは30分ほどオンラインで情報交換させていただけないでしょうか。
貴社のご都合のよいお日にちをいくつかお教えいただけますと幸いです。

何卒よろしくお願いいたします。

[あなたの名前]
[あなたの会社名]
[電話番号]
[メールアドレス]
```

---

## 使用方法

1. エージェントが `categories.yaml` から対象カテゴリの `cooperation_reason` と `approach_angle` を取得
2. `crawler.js` で取得した `company_name` と `representative` を埋め込み
3. カテゴリ別テンプレート（`proposal_templates/{category_id}.md`）が存在すれば、カテゴリ固有の文面を使用
4. 存在しなければ、このベーステンプレートを使用
