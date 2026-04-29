# small-company-research Design Rationale

## Purpose

`small-company-research` は、小規模企業の「提案候補リスト」を作るためのスキルである。

このスキルの目的は、営業先を即時に確定することではなく、提案対象になりそうな企業を収集し、後からスプレッドシートやCSV上で絞り込める形に構造化することにある。

そのため、収集段階では早く落としすぎない。抽出できた情報、抽出できなかった情報、判定できた情報、判定できなかった情報を分けて保存する。

## Target Assumptions

主な対象は、以下のような小規模企業である。

- Web制作会社
- Webマーケティング会社
- 士業・コンサルティング会社
- 店舗・地域ビジネス向けコンサルティング会社
- 今後キーワードや抽出条件を変えて横展開する小規模事業者

当初は企業情報収集全般として考えたため、上場企業、EDINET、国税庁法人番号、Gビズインフォなども候補に入った。

しかし、最終的な用途は大企業調査ではなく、小規模企業の提案候補リスト作成である。したがって、上場企業向けの開示情報や政府系法人データを中心にした設計は目的に合わないと判断した。

## Desired Output

このスキルで作りたいリストは、次のような情報を持つ。

```text
company_name
official_url
normalized_domain
duplicate_status
duplicate_reason
source_portal_url
profile_page_url
representative_name
capital_text
capital_amount_jpy
employee_text
employee_count
business_description
service_description
matched_keywords
negative_keywords
keyword_status
contact_form_url
contact_status
source_urls
retrieved_at
```

重要なのは、条件に合うかどうかをスキル内で強く決めきることではない。

例えば、資本金や従業員数が抽出できない企業でも、小規模企業として有望なケースはある。そこで、抽出できなかったものは `not_found` や `unknown` として残し、リスト側で後から判断できるようにする。

## Why This Is A Proposal Candidate List

このリストは「営業候補リスト」ではなく「提案候補リスト」である。

営業候補リストという言い方だと、すぐに営業行為を行う対象に見える。しかし実際には、まず候補企業を集め、企業規模、事業内容、サービス内容、問い合わせ導線を見て、提案余地があるかを判断するための前段階リストである。

そのため、このスキルではフォーム送信や営業実行は扱わない。問い合わせフォームURLは抽出するが、送信はしない。

## Research And Evaluation Process

### 1. Large-company research was rejected

最初は、企業名、代表者、従業員数、資本金、サービス内容などを網羅的に取得する方法として、EDINET、国税庁法人番号、Gビズインフォ、有料企業データベースなどを検討した。

しかし、対象が小規模のWeb制作会社やWebマーケティング会社であることが明確になったため、上場企業や大企業向けのデータ取得は主軸から外した。

EDINETは上場企業や有価証券報告書提出企業には強いが、小規模Web制作会社の抽出には向いていない。

### 2. Government registries were deprioritized

国税庁法人番号データやGビズインフォは、法人の名寄せや公的な確認には役立つ。

ただし、今回の用途では必須ではないと判断した。

理由は以下。

- 目的は法的な法人確認ではなく、提案候補の発見と構造化である
- 小規模企業では、公式サイトの会社概要ページのほうが代表者、資本金、従業員数、サービス内容に近い
- 法人番号やGビズ補完を入れると処理が重くなる
- 既存リストとの重複回避は、法人番号よりも公式サイトのドメイン一致で十分なケースが多い

したがって、`small-company-research` では国税庁法人番号やGビズインフォを標準処理には入れない。

必要な場合だけ、別途オプションとして追加する方針にする。

### 3. Portal sites are useful as seed sources

Web制作会社であれば、Web幹事のようなポータルサイト、比較サイト、カテゴリ記事、検索結果は候補企業を見つける入口として有効である。

ただし、ポータルサイトを最終的な情報ソースにしない。

ポータルサイトは以下の用途に限定する。

- 企業候補を見つける
- 業種カテゴリのヒントを得る
- 公式サイトURLの候補を得る
- 比較記事やディレクトリから候補母集団を作る

代表者、資本金、従業員数、問い合わせフォームURLなどの詳細情報は、できるだけ各社の公式サイトから抽出する。

ポータルサイトには利用規約上の制約がある場合があるため、大量収集や二次利用には注意する。

### 4. Official websites are the primary data source

小規模企業では、公式サイトの会社概要ページが最も実務的な情報源になる。

主に見るべきページは以下。

```text
/
/company
/about
/profile
/outline
/corporate
/company-profile
/company/outline
/contact
/inquiry
```

日本語リンクでは以下を優先する。

```text
会社概要
企業情報
会社案内
About
Company
Profile
Outline
お問い合わせ
無料相談
見積もり
資料請求
```

ブログ、実績記事、ニュース一覧、採用記事などは、初期抽出では深く追わない。

## Duplicate Avoidance Strategy

既に大量の既存リストがある場合、最も費用対効果が高い重複回避は、公式サイトのドメイン一致である。

複雑な会社名名寄せよりも、まずは `normalized_domain` を使う。

例:

```text
https://www.example.co.jp/
http://example.co.jp/company/
https://example.co.jp/contact?ref=portal
```

これらはすべて次のように正規化する。

```text
example.co.jp
```

重複判定は最低限これでよい。

```text
duplicate_status:
  new
  duplicate
  unknown

duplicate_reason:
  domain_match
  no_official_url
  none
```

会社名一致や代表者一致による名寄せは、誤判定が増えるため初期版では入れない。

## Extraction Philosophy

このスキルは「落とすスキル」ではなく「抽出して状態を付けるスキル」である。

収集時点で資本金1000万円未満や従業員20人未満を強く判定しすぎると、良い候補を落とす可能性がある。

そのため、次のようなステータスを持たせる。

```text
capital_status:
  extracted
  not_found
  ambiguous
  not_checked

employee_status:
  extracted
  not_found
  ambiguous
  not_checked

keyword_status:
  matched
  not_matched
  unknown

contact_status:
  found
  not_found
  uncertain
```

資本金や従業員数の最終フィルタリングは、出力後のリスト側で行う。

## Keyword Matching

業種判定は、会社概要やサービス内容に含まれるキーワードを根拠として保存する。

ただし、キーワード一致だけで最終判定しない。

例えばWeb制作会社向けなら、以下のようなキーワードを使う。

```text
ホームページ制作
Webサイト制作
サイト制作
コーポレートサイト
LP制作
WordPress
CMS
ECサイト
Shopify
Webデザイン
```

Webマーケティング会社向けなら、以下のようなキーワードを使う。

```text
Webマーケティング
SEO
MEO
広告運用
リスティング広告
SNS運用
コンテンツマーケティング
GA4
LPO
```

キーワードセットは `references/vertical-profiles.md` に分離し、業種ごとに差し替えられるようにした。

## AI Usage Policy

AIは最初から使わない。

まずはスクレイピング、DOM解析、正規表現、リンク探索で取れるものを取る。

AIを使うのは以下のような場合だけ。

- 公式サイト候補が複数あり、判定が難しい
- 会社概要の表記が崩れている
- 従業員数や資本金の表記が文章中に埋もれている
- 事業内容やサービス内容の分類に判断が必要
- 重要項目が取得できず、補完検索が必要

ページ全文をAIに渡さない。会社概要周辺、サービス説明周辺、問い合わせリンク周辺など、短いテキストに切り出してから渡す。

この方針により、トークン消費を抑え、再現性を高める。

## Why One Core Skill

最終的に、Web制作会社専用スキルではなく、`small-company-research` というコアスキルにした。

理由は以下。

- 重複判定は業種に関係なく共通
- 公式サイト解決も業種に関係なく共通
- 会社概要抽出も業種に関係なく共通
- 問い合わせフォームURL抽出も業種に関係なく共通
- 変わるのは主にキーワード、除外語、見るべき業種カテゴリである

したがって、業種ごとにスキルを分けるより、コアスキルを1つ作り、業種別条件を参照ファイルで分離する方が保守しやすい。

今後Webマーケティング会社、士業コンサル、店舗コンサルなどに横展開する場合も、コア処理を直せば全体に反映できる。

## Final Design Decision

このスキルは以下の考え方で作成した。

```text
Portal and search sources:
  candidate discovery only

Official websites:
  primary source for company profile and contact data

Government registries:
  skipped by default

Duplicate avoidance:
  normalized official domain

Filtering:
  defer to spreadsheet or downstream list review

AI:
  fallback for missing, ambiguous, or classification-heavy cases

Skill structure:
  one reusable core skill plus vertical keyword profiles
```

この設計により、初期実装は軽く保ちつつ、業種別の横展開や後からの共通アップデートに対応できる。

