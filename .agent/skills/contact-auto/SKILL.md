---
name: contact-auto
version: 0.4.0
description: 企業お問い合わせフォームへの自動送信スキル。CF7特化HTTP直接送信+高精度フィールド認識Playwright+マッピング不能スキップのハイブリッドアーキテクチャ。select/radio/checkbox完全対応。
tags: [form, automation, sales, playwright, http, hybrid, patchright, select, radio]
updated: 2026-04-29
disable-model-invocation: true
---

# contact-auto

> form-automation（半自動）の全自動版。CF7 HTTP直接送信 + Playwright高精度入力のハイブリッド。

## アーキテクチャ

```
URL -> CF7検出? -> HTTP直接送信(1-3秒) ← select/radio自動選択
               -> Playwright入力(10-30秒) ← select/radio/checkbox自動入力
               -> マッピング不能 -> スキップ
```

## ファイル構成

```
scratch/contact-auto/
  contact_auto.js          メインCLI
  core/
    cf7_http_submitter.js   CF7 REST API直接送信（multipart/form-data対応）
    playwright_submitter.js Playwright入力+結果検証（select/radio強化版）
    field_recognizer.js     5層フィールド認識エンジン
  config/
    profiles/               送信者プロファイル
    mappings/               フィールドマッピング(11カテゴリ)
    blacklist.json          送信禁止ドメイン
  compliance/
    compliance.js           NG検出90+,用途限定,レート制御
  logs/unmatched_fields/    マッピング不能パターン蓄積
  logs/cf7_evidence/        CF7送信エビデンスJSON
  screenshots/              送信前後エビデンス画像
  test_server.js            14バリエーションテストサーバー
  test_e2e.js               一括E2Eテストランナー
```

## select/radio 対応仕様（v0.4で強化）

### Playwrightルート
| 要素 | 処理 |
|---|---|
| `<select>` | SELECT_PREFERENCESで優先順にラベルマッチ → フォールバック: 先頭選択肢 |
| `<input type="radio">` | value/labelをSELECT_PREFERENCESでマッチ → name属性から意味推定 → フォールバック: 先頭（採用/応募系除外） |
| `<input type="checkbox">` | CONSENT_TRIGGERSで同意系を自動チェック |

### CF7 HTTPルート（v0.4で新規対応）
- detectCF7がselectのoptions一覧・radioのvalue/labelを収集
- radioは同name属性をグループ化して1エントリに統合
- SELECT_PREFERENCESで選択値を決定し、ペイロードに含める
- CF7 v5.7以降: `multipart/form-data` 形式でPOST（undici FormData）

### SELECT_PREFERENCES（優先順位テーブル）
```js
inquiry_type:      協業 > 業務提携 > パートナー > 制作依頼 > その他
preferred_contact: メール > メールで連絡 > どちらでも可
preferred_time:    いつでも > 不問 > 指定なし > 午前 > 午後
referral:          検索エンジン > Google検索 > その他
budget:            50万円未満 > 未定 > 検討中
deadline:          未定 > 検討中 > 急ぎ
```

### radioのmatchedKey自動推定ロジック
name属性のパターンマッチで意味を推定:
- `contact-way|contact-method|renraku` → preferred_contact
- `time|jikan` → preferred_time
- `referral|kikkake` → referral
- それ以外 → inquiry_type（デフォルト）

## エビデンスランク

| Rank | Evidence | Confidence | Sheet |
|------|----------|------------|-------|
| S | CF7 REST API mail_sent | 99% | 〇+日付 |
| A | 成功テキスト検出/URL遷移 | 90% | 〇+日付 |
| B | 確認ページ通過+ページ変化 | 75% | △ |
| C | エラーなし+ページ変化 | 50% | △ |
| D | 判定不能 | ? | 未 |
| error | バリデーションエラー | - | × |

判定ポリシー: 送信前に無かった文字列が送信後に出現した場合のみ成功

## フィールド分類(11カテゴリ / 500+URL調査)

1. 氏名: お名前/氏名/姓/名/フリガナ
2. 連絡先: メールアドレス/電話番号/FAX
3. 会社: 会社名/企業名/御社名/部署/役職
4. URL: ホームページURL/参考サイトURL
5. 本文: お問い合わせ内容/メッセージ本文
6. 件名: 題名/件名
7. **種別**: select/radio（協業>パートナー>その他）← v0.4強化
8. 詳細: 予算/納期/ページ数
9. 流入: サイトを知ったきっかけ
10. **連絡方法**: メール/電話 radio対応 ← v0.4強化
11. 同意: プライバシーポリシー同意チェック

## テスト環境（14バリエーション）

```bash
node test_server.js   # サーバー起動
node test_e2e.js      # 全14フォームを自動送信テスト
```

| Form | パターン | ルート |
|---|---|---|
| 1 | 標準ラベル付き | Playwright |
| 2 | placeholderのみ | Playwright |
| 3 | テーブルレイアウト | Playwright |
| 4 | 姓名・フリガナ分割 | Playwright |
| 5 | 電話・郵便番号3分割 | Playwright |
| 6 | name属性のみ（最難関） | Playwright |
| 7 | dl/dt/ddレイアウト | Playwright |
| 8 | select+チェックボックス | Playwright |
| 9 | CF7ダミー（テキストのみ） | CF7 HTTP |
| 10 | 営業NG | Compliance skip |
| 11 | **selectプルダウン3つ** | Playwright |
| 12 | **ラジオ（種別+連絡方法）** | Playwright |
| 13 | **CF7 + select/radio** | CF7 HTTP |
| 14 | **ラジオ（labelなし）** | Playwright |

## 設計判断

- LLMフォールバック不採用(コスト不適)
- HTTP直接送信はCF7限定(汎用化は保守地獄)
- Patchright採用(puppeteer-extra廃止)
- トークン消費ゼロ設計
- radioの「採用/応募」は自動除外（誤送信防止）

## 日次学習エンジン (skill_learner)

contact-auto は、送信中に遭遇した「未知のフォーム項目」を日次で自動学習・パッチ適用する機能を備えています。

### 動作フロー
1. 送信ループ中、`field_recognizer.js` で判定できなかった項目は `logs/unmatched_fields/` に蓄積される。
2. バッチの全送信が完了した後、末尾で `skill_learner.js` が自動起動する。
3. 当日の未マッチログを集計し、一定回数（デフォルト1回）以上出現した項目を抽出。
4. ラベル名・項目名から「既存カテゴリ（company, meeting, plan 等）」をヒューリスティックに推定。
5. 推定できたものは、`field_recognizer.js` および `cf7_http_submitter.js` のマッピング辞書に**直接コードを自動追記**。
6. この `SKILL.md` の末尾に「日次発見パターンログ」として結果を記録。
7. 推定不能だった項目は `unknown_fields_YYYY-MM-DD.json` に保存され、手動レビュー待ちとなる。

### 手動チューニング（オーナー作業）
SKILL.md のログに「⚠️ 要確認」として記載された項目は、オーナーが定期的に確認し、新しいカテゴリを追加するか、既存のルール（`skill_learner.js` 内の `CATEGORY_RULES`）を拡張してください。

## バージョン履歴

| Ver | Date | Changes |
|-----|------|---------|
| 0.1 | 2026-04-28 | 初版(リサーチ統合) |
| 0.2 | 2026-04-28 | ハイブリッドE改確定 |
| 0.3 | 2026-04-28 | 11カテゴリ統合+エビデンスランク+テスト10種 |
| 0.4 | 2026-04-29 | select/radio完全対応+CF7 multipart修正+テスト14種 |
| 0.5 | 2026-04-29 | 日次自動学習エンジン(skill_learner)実装 |
