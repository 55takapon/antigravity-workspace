---
name: contact-auto
version: 0.6.0
description: 企業お問い合わせフォームへの自動送信スキル。CF7特化HTTP直接送信+高精度フィールド認識Playwright+マッピング不能スキップのハイブリッドアーキテクチャ。select/radio/checkbox完全対応。
tags: [form, automation, sales, playwright, http, hybrid, patchright, select, radio]
updated: 2026-04-30
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

## スプレッドシート列フォーマット（固定）

送信対象シートの列配列は以下で固定。変更禁止。

| 列 | ヘッダー名 | 用途 |
|---|---|---|
| A | № | 連番 |
| B | エリア | 都道府県・地域 |
| C | 企業名 | 送信先企業名（本文パーソナライズに使用） |
| D | 代表者名 | 宛名（本文の「様」前に使用） |
| E | URL | 企業ホームページURL |
| F | 問い合わせフォームURL | **送信先URL**（必須） |
| G | 送信日 | 送信完了日（スクリプトが自動書込） |
| H | 送信○× | 送信結果: 〇/△/×/未（スクリプトが自動書込） |
| I | 送信不可理由 | スキップ理由・エラー内容（スクリプトが自動書込） |
| J | 従業員数 | リサーチデータ |
| K | 資本金 | リサーチデータ |
| L | キーワードHIT | マッチしたキーワード |
| M | HIT詳細 | キーワードHIT詳細 |
| N | 取得日時 | リサーチデータ取得日時 |
| O | Web3分類 | Web制作/Webマーケ/その他の分類 |

## スキップ判定ルール

以下のいずれかに該当する行は送信をスキップする（`contact_auto.js` 実装）:

| 優先順 | 判定列 | 条件 | スキップ理由 |
|---|---|---|---|
| 1 | G列「送信日」 | 値あり | 送信済み |
| 2 | I列「送信不可理由」 | **文字入力あり（内容問わず）** | 営業NG・従業員数超過・資本金超過等 |
| 3 | F列「問い合わせフォームURL」 | 空 or http で始まらない | URLなし |
| 4 | F列（ドメイン） | blacklist.json に登録済み | ブラックリスト |

> **H列「送信○×」はスキップ判定に使用しない**（スクリプトが結果を書き込む列のため）

### I列スキップの例
```
営業NG          → スキップ
従業員20名以上   → スキップ
資本金1000万以上 → スキップ
フォームなし     → スキップ
（何か文字があれば全てスキップ）
```

## 実行コマンド

```bash
node contact_auto.js \
  --sheets <スプレッドシートID> \
  --sheet-name <シート名> \
  --rows <開始>-<終了> \
  [--profile web-company] \
  [--mapping web-company] \
  [--dry-run]
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

## CF7正規タグ補完仕様（v0.6で確定）

CF7メールテンプレートのデフォルトタグ4つを常時送信する:

| タグ | 値 | 理由 |
|---|---|---|
| `your-name` | profile.name | 差出人リテラル防止 |
| `your-email` | profile.email | 差出人リテラル防止 |
| `your-subject` | **空文字** | リテラル防止 + 本文【タイトル】との二重表記防止 |
| `your-message` | profile.message | 本文リテラル防止 |

> **設計根拠**: `your-subject` に値を入れると本文冒頭の【タイトル】と二重表記になる。空文字で送信することでリテラル `[your-subject]` の表示を防ぎつつ、二重表記も回避。

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
- your-subject は空文字送信（CF7テンプレートリテラル防止＋本文【題名】との二重表記防止）

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
| 0.6 | 2026-04-30 | 列フォーマット定義追加・スキップルール明文化・H列×スキップ追加・CF7正規タグ補完仕様確定 |

## 日次発見パターンログ

### 2026-04-30

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `予約プラン` | １日プラン | radio | ✅ plan | 8 | 🔧 自動パッチ済 |
| `acceptance-537` | プライバシーポリシーに同意する | checkbox | ❓ 未推定 | 5 | ⚠️ 要確認 |
| `予約時間` | — | text | ❓ 未推定 | 4 | ⚠️ 要確認 |
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `g-recaptcha-response` | — | textarea | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `checkbox-379[]` | 同意する / 同意する個人情報の取り扱いについて同意して送信する必須 / お問い合わせフォーム | checkbox | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `予約プラン` | １日プラン | radio | ✅ plan | 8 | 🔧 自動パッチ済 |
| `予約時間` | — | text | ❓ 未推定 | 4 | ⚠️ 要確認 |
| `acceptance-537` | プライバシーポリシーに同意する | checkbox | ❓ 未推定 | 4 | ⚠️ 要確認 |
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `g-recaptcha-response` | — | textarea | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `checkbox-379[]` | 同意する / 同意する個人情報の取り扱いについて同意して送信する必須 / お問い合わせフォーム | checkbox | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `予約プラン` | １日プラン | radio | ✅ plan | 8 | 🔧 自動パッチ済 |
| `予約時間` | — | text | ❓ 未推定 | 4 | ⚠️ 要確認 |
| `acceptance-537` | プライバシーポリシーに同意する | checkbox | ❓ 未推定 | 3 | ⚠️ 要確認 |
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `g-recaptcha-response` | — | textarea | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `checkbox-379[]` | 同意する / 同意する個人情報の取り扱いについて同意して送信する必須 / お問い合わせフォーム | checkbox | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `予約プラン` | １日プラン | radio | ✅ plan | 8 | 🔧 自動パッチ済 |
| `予約時間` | — | text | ❓ 未推定 | 4 | ⚠️ 要確認 |
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `acceptance-537` | プライバシーポリシーに同意する | checkbox | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `g-recaptcha-response` | — | textarea | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `checkbox-379[]` | 同意する / 同意する個人情報の取り扱いについて同意して送信する必須 / お問い合わせフォーム | checkbox | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `予約プラン` | １日プラン | radio | ✅ plan | 8 | 🔧 自動パッチ済 |
| `予約時間` | — | text | ❓ 未推定 | 4 | ⚠️ 要確認 |
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `g-recaptcha-response` | — | textarea | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `checkbox-379[]` | 同意する / 同意する個人情報の取り扱いについて同意して送信する必須 / お問い合わせフォーム | checkbox | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `acceptance-537` | プライバシーポリシーに同意する | checkbox | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `予約プラン` | １日プラン | radio | ✅ plan | 8 | 🔧 自動パッチ済 |
| `予約時間` | — | text | ❓ 未推定 | 4 | ⚠️ 要確認 |
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `g-recaptcha-response` | — | textarea | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `checkbox-379[]` | 同意する / 同意する個人情報の取り扱いについて同意して送信する必須 / お問い合わせフォーム | checkbox | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `予約プラン` | １日プラン | radio | ✅ plan | 8 | 🔧 自動パッチ済 |
| `予約時間` | — | text | ❓ 未推定 | 4 | ⚠️ 要確認 |
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `g-recaptcha-response` | — | textarea | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `予約プラン` | １日プラン | radio | ✅ plan | 8 | 🔧 自動パッチ済 |
| `予約時間` | — | text | ❓ 未推定 | 4 | ⚠️ 要確認 |
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `g-recaptcha-response` | — | textarea | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `予約プラン` | １日プラン | radio | ✅ plan | 8 | 🔧 自動パッチ済 |
| `予約時間` | — | text | ❓ 未推定 | 4 | ⚠️ 要確認 |
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `g-recaptcha-response` | — | textarea | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `予約プラン` | １日プラン | radio | ✅ plan | 6 | 🔧 自動パッチ済 |
| `予約時間` | — | text | ❓ 未推定 | 3 | ⚠️ 要確認 |
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `g-recaptcha-response` | — | textarea | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `予約プラン` | １日プラン | radio | ✅ plan | 4 | 🔧 自動パッチ済 |
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約時間` | — | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `g-recaptcha-response` | — | textarea | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `予約プラン` | １日プラン | radio | ✅ plan | 2 | 🔧 自動パッチ済 |
| `予約日時` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `予約時間` | — | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `g-recaptcha-response` | — | textarea | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |

### 2026-04-29

| フィールド名 | ラベル | 型 | 推定カテゴリ | 出現数 | 対応状況 |
|---|---|---|---|---|---|
| `s` | 検索ワード / contact #8 | text | ❓ 未推定 | 2 | ⚠️ 要確認 |
| `iin-mei` | 医院名 | text | ✅ company | 1 | 🔧 自動パッチ済 |
| `kibou-plan` | ご希望プラン | select | ✅ plan | 1 | 🔧 自動パッチ済 |
| `web-kaigi` | ウェブミーティング希望 | checkbox | ✅ meeting | 1 | 🔧 自動パッチ済 |
| `fushigi-field` | 謎のフィールド | text | ❓ 未推定 | 1 | ⚠️ 要確認 |
| `seisaku-time` | 制作時期 | select | ✅ deadline | 1 | 🔧 自動パッチ済 |