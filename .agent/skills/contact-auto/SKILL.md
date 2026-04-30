---
name: contact-auto
version: 0.6.0
description: 企業お問ぁE��わせフォームへの自動送信スキル、EF7特化HTTP直接送信+高精度フィールド認識Playwright+マッピング不�EスキチE�EのハイブリチE��アーキチE��チャ。select/radio/checkbox完�E対応、Etags: [form, automation, sales, playwright, http, hybrid, patchright, select, radio]
updated: 2026-04-30
disable-model-invocation: true
---

# contact-auto

> form-automation�E�半自動）�E全自動版、EF7 HTTP直接送信 + Playwright高精度入力�EハイブリチE��、E
## アーキチE��チャ

```
URL -> CF7検�E? -> HTTP直接送信(1-3私E ↁEselect/radio自動選抁E               -> Playwright入劁E10-30私E ↁEselect/radio/checkbox自動�E劁E               -> マッピング不�E -> スキチE�E
```

## ファイル構�E

```
scratch/contact-auto/
  contact_auto.js          メインCLI
  core/
    cf7_http_submitter.js   CF7 REST API直接送信�E�Eultipart/form-data対応！E    playwright_submitter.js Playwright入劁E結果検証�E�Eelect/radio強化版�E�E    field_recognizer.js     5層フィールド認識エンジン
  config/
    profiles/               送信老E�Eロファイル
    mappings/               フィールド�EチE��ング(11カチE��リ)
    blacklist.json          送信禁止ドメイン
  compliance/
    compliance.js           NG検�E90+,用途限宁Eレート制御
  logs/unmatched_fields/    マッピング不�Eパターン蓁E��E  logs/cf7_evidence/        CF7送信エビデンスJSON
  screenshots/              送信前後エビデンス画僁E  test_server.js            14バリエーションチE��トサーバ�E
  test_e2e.js               一括E2EチE��トランナ�E
```

## スプレチE��シート�Eフォーマット（固定！E
送信対象シート�E列�E列�E以下で固定。変更禁止、E
| 刁E| ヘッダー吁E| 用送E|
|---|---|---|
| A | ℁E| 連番 |
| B | エリア | 都道府県・地埁E|
| C | 企業吁E| 送信先企業名（本斁E��ーソナライズに使用�E�E|
| D | 代表老E�� | 宛名�E�本斁E�E「様」前に使用�E�E|
| E | URL | 企業ホ�Eムペ�EジURL |
| F | 問い合わせフォームURL | **送信允ERL**�E�忁E��！E|
| G | 送信日 | 送信完亁E���E�スクリプトが�E動書込�E�E|
| H | 送信○ÁE| 送信結果: 、E△/ÁE未�E�スクリプトが�E動書込�E�E|
| I | 送信不可琁E�� | スキチE�E琁E��・エラー冁E���E�スクリプトが�E動書込�E�E|
| J | 従業員数 | リサーチデータ |
| K | 賁E��釁E| リサーチデータ |
| L | キーワードHIT | マッチしたキーワーチE|
| M | HIT詳細 | キーワードHIT詳細 |
| N | 取得日晁E| リサーチデータ取得日晁E|
| O | Web3刁E��E| Web制佁EWebマ�Eケ/そ�E他�E刁E��E|

## スキチE�E判定ルール

以下�EぁE��れかに該当する行�E送信をスキチE�Eする�E�Econtact_auto.js` 実裁E��E

| 優先頁E| 判定�E | 条件 | スキチE�E琁E�� |
|---|---|---|---|
| 1 | G列「送信日、E| 値あり | 送信済み |
| 2 | I列「送信不可琁E��、E| **斁E���E力あり（�E容問わず！E* | 営業NG・従業員数趁E��・賁E��金趁E��筁E|
| 3 | F列「問ぁE��わせフォームURL、E| 空 or http で始まらなぁE| URLなぁE|
| 4 | F列（ドメイン�E�E| blacklist.json に登録済み | ブラチE��リスチE|

> **H列「送信○×」�EスキチE�E判定に使用しなぁE*�E�スクリプトが結果を書き込む列�Eため�E�E
### I列スキチE�Eの侁E```
営業NG          ↁEスキチE�E
従業員20名以丁E  ↁEスキチE�E
賁E��釁E000丁E��丁EↁEスキチE�E
フォームなぁE    ↁEスキチE�E
�E�何か斁E��があれば全てスキチE�E�E�E```

## 実行コマンチE
```bash
node contact_auto.js \
  --sheets <スプレチE��シーチED> \
  --sheet-name <シート名> \
  --rows <開姁E-<終亁E \
  [--profile web-company] \
  [--mapping web-company] \
  [--dry-run]
```

## select/radio 対応仕様！E0.4で強化！E
### PlaywrightルーチE| 要素 | 処琁E|
|---|---|
| `<select>` | SELECT_PREFERENCESで優先頁E��ラベルマッチEↁEフォールバック: 先頭選択肢 |
| `<input type="radio">` | value/labelをSELECT_PREFERENCESでマッチEↁEname属性から意味推宁EↁEフォールバック: 先頭�E�採用/応募系除外！E|
| `<input type="checkbox">` | CONSENT_TRIGGERSで同意系を�E動チェチE�� |

### CF7 HTTPルート！E0.4で新規対応！E- detectCF7がselectのoptions一覧・radioのvalue/labelを収雁E- radioは同name属性をグループ化して1エントリに統吁E- SELECT_PREFERENCESで選択値を決定し、�Eイロードに含める
- CF7 v5.7以陁E `multipart/form-data` 形式でPOST�E�Endici FormData�E�E
### SELECT_PREFERENCES�E�優先頁E��テーブル�E�E```js
inquiry_type:      協業 > 業務提携 > パ�Eトナー > 制作依頼 > そ�E仁Epreferred_contact: メール > メールで連絡 > どちらでも可
preferred_time:    ぁE��でめE> 不問 > 持E��なぁE> 午前 > 午征Ereferral:          検索エンジン > Google検索 > そ�E仁Ebudget:            50丁E�E未満 > 未宁E> 検討中
deadline:          未宁E> 検討中 > 急ぁE```

### radioのmatchedKey自動推定ロジチE��
name属性のパターンマッチで意味を推宁E
- `contact-way|contact-method|renraku` ↁEpreferred_contact
- `time|jikan` ↁEpreferred_time
- `referral|kikkake` ↁEreferral
- それ以夁EↁEinquiry_type�E�デフォルト！E
## CF7正規タグ補完仕様！E0.6で確定！E
CF7メールチE��プレート�EチE��ォルトタグ4つを常時送信する:

| タグ | 値 | 琁E�� |
|---|---|---|
| `your-name` | profile.name | 差出人リチE��ル防止 |
| `your-email` | profile.email | 差出人リチE��ル防止 |
| `your-subject` | **空斁E��E* | リチE��ル防止 + 本斁E��タイトル】との二重表記防止 |
| `your-message` | profile.message | 本斁E��チE��ル防止 |

> **設計根拠**: `your-subject` に値を�Eれると本斁E�E頭の【タイトル】と二重表記になる。空斁E��で送信することでリチE��ル `[your-subject]` の表示を防ぎつつ、二重表記も回避、E
## エビデンスランク

| Rank | Evidence | Confidence | Sheet |
|------|----------|------------|-------|
| S | CF7 REST API mail_sent | 99% | 、E日仁E|
| A | 成功チE��スト検�E/URL遷移 | 90% | 、E日仁E|
| B | 確認�Eージ通過+ペ�Eジ変化 | 75% | △ |
| C | エラーなぁEペ�Eジ変化 | 50% | △ |
| D | 判定不�E | ? | 未 |
| error | バリチE�Eションエラー | - | ÁE|

判定�Eリシー: 送信前に無かった文字�Eが送信後に出現した場合�Eみ成功

## フィールド�E顁E11カチE��リ / 500+URL調査)

1. 氏名: お名剁E氏名/姁E吁EフリガチE2. 連絡允E メールアドレス/電話番号/FAX
3. 会社: 会社吁E企業吁E御社吁E部署/役職
4. URL: ホ�Eムペ�EジURL/参老E��イチERL
5. 本斁E お問ぁE��わせ冁E��/メチE��ージ本斁E6. 件吁E 題名/件吁E7. **種別**: select/radio�E�協業>パ�Eトナー>そ�E他）�E v0.4強匁E8. 詳細: 予箁E納期/ペ�Eジ数
9. 流�E: サイトを知ったきっかけ
10. **連絡方況E*: メール/電話 radio対忁EↁEv0.4強匁E11. 同意: プライバシーポリシー同意チェチE��

## チE��ト環墁E��E4バリエーション�E�E
```bash
node test_server.js   # サーバ�E起勁Enode test_e2e.js      # 全14フォームを�E動送信チE��チE```

| Form | パターン | ルーチE|
|---|---|---|
| 1 | 標準ラベル付き | Playwright |
| 2 | placeholderのみ | Playwright |
| 3 | チE�EブルレイアウチE| Playwright |
| 4 | 姓名・フリガナ�E割 | Playwright |
| 5 | 電話・郵便番号3刁E�� | Playwright |
| 6 | name属性のみ�E�最難関�E�E| Playwright |
| 7 | dl/dt/ddレイアウチE| Playwright |
| 8 | select+チェチE��ボックス | Playwright |
| 9 | CF7ダミ�E�E�テキスト�Eみ�E�E| CF7 HTTP |
| 10 | 営業NG | Compliance skip |
| 11 | **selectプルダウン3つ** | Playwright |
| 12 | **ラジオ�E�種別+連絡方法！E* | Playwright |
| 13 | **CF7 + select/radio** | CF7 HTTP |
| 14 | **ラジオ�E�Eabelなし！E* | Playwright |

## 設計判断

- LLMフォールバック不採用(コスト不適)
- HTTP直接送信はCF7限宁E汎用化�E保守地獁E
- Patchright採用(puppeteer-extra廁E��)
- ト�Eクン消費ゼロ設訁E- radioの「採用/応募」�E自動除外（誤送信防止�E�E- your-subject は空斁E��送信�E�EF7チE��プレートリチE��ル防止�E�本斁E��題名】との二重表記防止�E�E
## 日次学習エンジン (skill_learner)

contact-auto は、E��信中に遭遁E��た「未知のフォーム頁E��」を日次で自動学習�EパッチE��用する機�Eを備えてぁE��す、E
### 動作フロー
1. 送信ループ中、`field_recognizer.js` で判定できなかった頁E��は `logs/unmatched_fields/` に蓁E��される、E2. バッチ�E全送信が完亁E��た後、末尾で `skill_learner.js` が�E動起動する、E3. 当日の未マッチログを集計し、一定回数�E�デフォルチE回）以上�E現した頁E��を抽出、E4. ラベル名�E頁E��名から「既存カチE��リ�E�Eompany, meeting, plan 等）」をヒューリスチE��チE��に推定、E5. 推定できたも�Eは、`field_recognizer.js` および `cf7_http_submitter.js` のマッピング辞書に**直接コードを自動追訁E*、E6. こ�E `SKILL.md` の末尾に「日次発見パターンログ」として結果を記録、E7. 推定不�Eだった頁E��は `unknown_fields_YYYY-MM-DD.json` に保存され、手動レビュー征E��となる、E
### 手動チューニング�E�オーナ�E作業�E�ESKILL.md のログに「⚠�E�E要確認」として記載された頁E��は、オーナ�Eが定期皁E��確認し、新しいカチE��リを追加するか、既存�Eルール�E�Eskill_learner.js` 冁E�E `CATEGORY_RULES`�E�を拡張してください、E
## バ�Eジョン履歴

| Ver | Date | Changes |
|-----|------|---------|
| 0.1 | 2026-04-28 | 初版(リサーチ統吁E |
| 0.2 | 2026-04-28 | ハイブリチE��E改確宁E|
| 0.3 | 2026-04-28 | 11カチE��リ統吁Eエビデンスランク+チE��チE0種 |
| 0.4 | 2026-04-29 | select/radio完�E対忁ECF7 multipart修正+チE��チE4種 |
| 0.5 | 2026-04-29 | 日次自動学習エンジン(skill_learner)実裁E|
| 0.6 | 2026-04-30 | 列フォーマット定義追加・スキチE�Eルール明文化�EH列×スキチE�E追加・CF7正規タグ補完仕様確宁E|

## 日次発見パターンログ

> ⚠�E�Eこ�Eセクションは `skill_learner.js` が�E動更新する。重褁E��記�E dedup で防止済み�E�E0.7〜）、E
### 2026-04-30

| フィールド名 | ラベル | 垁E| 推定カチE��リ | 出現数 | 対応状況E|
|---|---|---|---|---|---|
| `予紁E�Eラン` | �E�日プラン | radio | ✁Eplan | 8 | 🔧 自動パチE��渁E|
| `acceptance-537` | プライバシーポリシーに同意する | checkbox | ❁E未推宁E| 5 | ⚠�E�E要確誁E|
| `予紁E��間` |  E| text | ❁E未推宁E| 4 | ⚠�E�E要確誁E|
| `s` | 検索ワーチE/ contact #8 | text | ❁E未推宁E| 2 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `g-recaptcha-response` |  E| textarea | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `checkbox-379[]` | 同意する / 同意する個人惁E��の取り扱ぁE��つぁE��同意して送信する忁E��E/ お問ぁE��わせフォーム | checkbox | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `iin-mei` | 医院吁E| text | ✁Ecompany | 1 | 🔧 自動パチE��渁E|
| `kibou-plan` | ご希望プラン | select | ✁Eplan | 1 | 🔧 自動パチE��渁E|
| `web-kaigi` | ウェブミーチE��ング希望 | checkbox | ✁Emeeting | 1 | 🔧 自動パチE��渁E|
| `fushigi-field` | 謎�EフィールチE| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `seisaku-time` | 制作時朁E| select | ✁Edeadline | 1 | 🔧 自動パチE��渁E|

### 2026-04-29

| フィールド名 | ラベル | 垁E| 推定カチE��リ | 出現数 | 対応状況E|
|---|---|---|---|---|---|
| `s` | 検索ワーチE/ contact #8 | text | ❁E未推宁E| 2 | ⚠�E�E要確誁E|
| `iin-mei` | 医院吁E| text | ✁Ecompany | 1 | 🔧 自動パチE��渁E|
| `kibou-plan` | ご希望プラン | select | ✁Eplan | 1 | 🔧 自動パチE��渁E|
| `web-kaigi` | ウェブミーチE��ング希望 | checkbox | ✁Emeeting | 1 | 🔧 自動パチE��渁E|
| `fushigi-field` | 謎�EフィールチE| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `seisaku-time` | 制作時朁E| select | ✁Edeadline | 1 | 🔧 自動パチE��渁E|

| `s` | 検索ワーチE/ contact #8 | text | ❁E未推宁E| 2 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `g-recaptcha-response` |  E| textarea | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `checkbox-379[]` | 同意する / 同意する個人惁E��の取り扱ぁE��つぁE��同意して送信する忁E��E/ お問ぁE��わせフォーム | checkbox | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `iin-mei` | 医院吁E| text | ✁Ecompany | 1 | 🔧 自動パチE��渁E|
| `kibou-plan` | ご希望プラン | select | ✁Eplan | 1 | 🔧 自動パチE��渁E|
| `web-kaigi` | ウェブミーチE��ング希望 | checkbox | ✁Emeeting | 1 | 🔧 自動パチE��渁E|
| `fushigi-field` | 謎�EフィールチE| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `seisaku-time` | 制作時朁E| select | ✁Edeadline | 1 | 🔧 自動パチE��渁E|

| フィールド名 | ラベル | 垁E| 推定カチE��リ | 出現数 | 対応状況E|
|---|---|---|---|---|---|
| `予紁E�Eラン` | �E�日プラン | radio | ✁Eplan | 8 | 🔧 自動パチE��渁E|
| `予紁E��間` |  E| text | ❁E未推宁E| 4 | ⚠�E�E要確誁E|
| `acceptance-537` | プライバシーポリシーに同意する | checkbox | ❁E未推宁E| 3 | ⚠�E�E要確誁E|
| `s` | 検索ワーチE/ contact #8 | text | ❁E未推宁E| 2 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `g-recaptcha-response` |  E| textarea | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `checkbox-379[]` | 同意する / 同意する個人惁E��の取り扱ぁE��つぁE��同意して送信する忁E��E/ お問ぁE��わせフォーム | checkbox | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `iin-mei` | 医院吁E| text | ✁Ecompany | 1 | 🔧 自動パチE��渁E|
| `kibou-plan` | ご希望プラン | select | ✁Eplan | 1 | 🔧 自動パチE��渁E|
| `web-kaigi` | ウェブミーチE��ング希望 | checkbox | ✁Emeeting | 1 | 🔧 自動パチE��渁E|
| `fushigi-field` | 謎�EフィールチE| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `seisaku-time` | 制作時朁E| select | ✁Edeadline | 1 | 🔧 自動パチE��渁E|

| フィールド名 | ラベル | 垁E| 推定カチE��リ | 出現数 | 対応状況E|
|---|---|---|---|---|---|
| `予紁E�Eラン` | �E�日プラン | radio | ✁Eplan | 8 | 🔧 自動パチE��渁E|
| `予紁E��間` |  E| text | ❁E未推宁E| 4 | ⚠�E�E要確誁E|
| `s` | 検索ワーチE/ contact #8 | text | ❁E未推宁E| 2 | ⚠�E�E要確誁E|
| `acceptance-537` | プライバシーポリシーに同意する | checkbox | ❁E未推宁E| 2 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `g-recaptcha-response` |  E| textarea | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `予紁E��時` |  E| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `checkbox-379[]` | 同意する / 同意する個人惁E��の取り扱ぁE��つぁE��同意して送信する忁E��E/ お問ぁE��わせフォーム | checkbox | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `iin-mei` | 医院吁E| text | ✁Ecompany | 1 | 🔧 自動パチE��渁E|
| `kibou-plan` | ご希望プラン | select | ✁Eplan | 1 | 🔧 自動パチE��渁E|
| `web-kaigi` | ウェブミーチE��ング希望 | checkbox | ✁Emeeting | 1 | 🔧 自動パチE��渁E|
| `fushigi-field` | 謎�EフィールチE| text | ❁E未推宁E| 1 | ⚠�E�E要確誁E|
| `seisaku-time` | 制作時朁E| select | ✁Edeadline | 1 | 🔧 自動パチE��渁E|

| フィールド名 | ラベル | 垁E| 推定カチE��リ | 出現数 | 対応状況E|