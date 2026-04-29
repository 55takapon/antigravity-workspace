---
name: gbp-partner-search
description: GBP/MEO運用の協業パートナーとなりうる企業を業種カテゴリ別に抽出し、提案文を生成するスキル
---

# GBPパートナー企業抽出スキル

Googleビジネスプロフィール（GBP/MEO）運用サービスの**協業パートナーとなりうる企業**を、業種カテゴリ別に体系的に抽出し、カテゴリに応じた提案文を生成する。

## 前提

- **作業ディレクトリ**: `C:\Users\hangy\.gemini\antigravity\scratch\company_search`
- **依存モジュール**: `search_companies.js`（3段階検索 + Playwrightクローリング + Google Sheets書き込み）
- **設定ファイル**: `categories.yaml`（15業種カテゴリ × 検索キーワード定義）
- **提案文テンプレート**: `proposal_templates/` 配下

---

## ワークフロー

### Phase 1: カテゴリ選択

1. `categories.yaml` を読み込む
2. ユーザーに以下を確認:
   - **対象カテゴリ**: カテゴリID（例: `web_production`）または Tier指定（例: `tier1全部`）
   - **対象地域**: 例: `大阪`, `東京`（`defaults.regions` からも選択可能）
3. 複数カテゴリ × 複数地域の場合、実行順序を提示して確認

### Phase 2: config.yaml 生成

選択されたカテゴリと地域から `config.yaml` を自動生成する。

**生成ルール:**

```yaml
search:
  keywords:
    # categories.yaml の keywords から {region} を置換
    - "ホームページ制作 大阪"
    - "Web制作会社 大阪"
    - "Webサイト制作 大阪"
  region: 大阪
  max_results: 50  # categories.yaml の defaults.max_results
filters:
  max_employees: 20  # categories.yaml の target_scale
  hp_check_keywords:
    # categories.yaml の hp_check_keywords をそのまま使用
    - ホームページ制作
    - Webサイト制作
    - Web制作
exclude:
  spreadsheet_id: "1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk"
  sheet_name: "除外リスト"
output:
  spreadsheet_id: "1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk"
  sheet_name: "Web制作HP制作会社_大阪"  # {category_name}_{region}
google_cse:
  enabled: false
  api_key: AIzaSyCJrYuW_XKCk_k3lOMdBU64AKh9tGnWtSg
  cx: 2180f0a6c545843bf
speed:
  page_wait_min: 2000
  page_wait_max: 5000
  crawl_interval_min: 3000
  crawl_interval_max: 8000
```

**config.yaml の生成手順:**
1. `categories.yaml` から対象カテゴリを取得
2. `keywords` の `{region}` を指定地域に置換
3. `hp_check_keywords` をそのままコピー
4. `target_scale` → `filters.max_employees`
5. `sheet_name_template` の `{category_name}`, `{region}` を置換（全角・記号はシート名に使えるのでそのまま）
6. `config.yaml` を上書き保存

### Phase 3: 企業検索の実行

```powershell
# テスト実行（Sheets書き込みなし、最大5件）
node search_companies.js --dry-run --max 5

# 本番実行
node search_companies.js
```

**実行中の確認事項:**
- 除外リストとの照合が正常に動作しているか
- 従業員数フィルタが categories.yaml の `target_scale` で機能しているか
- HP内キーワードチェックが正しいキーワードで実行されているか

### Phase 4: 結果分析

検索結果のGoogle Sheetsを確認し、以下を分析:

1. **カテゴリ適合度**: HPキーワードHIT率が低い場合、検索キーワードの見直しが必要
2. **企業規模分布**: 従業員数の分布を確認し、`target_scale` の妥当性を検証
3. **フォーム検出率**: お問い合わせフォームの検出率が低い場合、フォーム送信の別アプローチが必要
4. **有望リードの特定**:
   - キーワードHIT ○
   - 従業員数 5〜20名（小規模で人手不足 → 協業ニーズ高）
   - フォーム ○

### Phase 5: 提案文生成

1. `proposal_templates/{category_id}.md` が存在すればそれを使用
2. 存在しなければ `proposal_templates/_base.md` を使用
3. Google Sheetsの各企業データから変数を埋め込み:
   - `{company_name}` ← C列（企業名）
   - `{representative}` ← D列（代表者名）
   - `{region}` ← B列（エリア）
   - `{category_name}` ← categories.yaml の `name`
   - `{cooperation_reason}` ← categories.yaml の `cooperation_reason`
   - `{approach_angle}` ← categories.yaml の `approach_angle`

---

## カテゴリ一覧（クイックリファレンス）

### Tier 1: 高確度パートナー
| ID | 名前 | キーワード数 |
|---|---|---|
| `web_production` | Web制作・HP制作会社 | 5 + 3変種 |
| `seo_agency` | SEO/MEO専門会社 | 5 + 2変種 |
| `web_marketing` | Webマーケティング会社 | 5 + 2変種 |
| `ad_agency` | 広告運用代理店 | 5 + 2変種 |
| `store_consulting` | 店舗集客コンサル | 5 + 2変種 |

### Tier 2: 中確度（業種特化）
| ID | 名前 | キーワード数 |
|---|---|---|
| `medical_hp` | 医療・クリニック専門HP会社 | 5 + 3変種 |
| `medical_consulting` | 医療経営コンサル | 5 + 2変種 |
| `tax_startup` | 士業特化サービス | 5 + 2変種 |
| `beauty_support` | 美容業界支援会社 | 5 + 2変種 |
| `real_estate_marketing` | 不動産マーケティング | 5 + 2変種 |

### Tier 3: ニッチ
| ID | 名前 | キーワード数 |
|---|---|---|
| `store_design` | 店舗デザイン・プロデュース | 5 + 2変種 |
| `franchise_support` | フランチャイズ支援 | 5 + 2変種 |
| `food_consulting` | 飲食コンサル | 5 + 2変種 |
| `education_marketing` | 教育・スクール集客 | 5 + 2変種 |
| `it_support` | 中小企業IT支援 | 5 + 2変種 |
| `photo_video` | ビジネス写真・動画制作 | 5 + 2変種 |
| `printing_signage` | 印刷・看板会社 | 5 + 2変種 |

---

## 実行例

### 例1: Web制作会社を大阪で検索

```
ユーザー: 「web_production カテゴリで大阪の企業を検索して」

エージェントの動作:
1. categories.yaml から web_production を取得
2. config.yaml を生成（keywords に大阪を設定）
3. node search_companies.js --dry-run --max 5 でテスト
4. 結果を確認 → 本番実行
5. Sheetsの結果を分析
6. proposal_templates/web_production.md で提案文を生成
```

### 例2: Tier 1 全カテゴリを東京で一括検索

```
ユーザー: 「Tier 1 の全カテゴリを東京で検索して」

エージェントの動作:
1. categories.yaml から tier: 1 のカテゴリを全取得
2. web_production → seo_agency → web_marketing → ad_agency → store_consulting の順で実行
3. 各カテゴリごとに config.yaml を差し替えて search_companies.js を実行
4. 各シートに結果が蓄積される
```

### 例3: 新しいカテゴリを追加したい

```
ユーザー: 「ペット業界の支援会社を追加して」

エージェントの動作:
1. categories.yaml に新カテゴリを追加:
   - id: pet_support
   - keywords: ["ペットサロン 集客", "動物病院 マーケティング", ...]
   - hp_check_keywords: ["ペット", "トリミング", "動物病院", ...]
2. 必要に応じて proposal_templates/pet_support.md を作成
```

---

## ファイル構成

```
company_search/
├── SKILL.md                          # 本ファイル（スキル指示書）
├── categories.yaml                   # 業種カテゴリ × キーワード定義
├── proposal_templates/               # 提案文テンプレート
│   ├── _base.md                      #   共通ベーステンプレート
│   └── web_production.md             #   Web制作会社向け
├── config.yaml                       # 検索実行設定（カテゴリから自動生成）
├── search_companies.js               # メインオーケストレーター
├── searcher.js                       # Web検索モジュール（CSE/DDG/Google直接）
├── crawler.js                        # 企業HPクローラー
└── sheets_writer.js                  # Google Sheets書き込み
```

---

## カテゴリのメンテナンス

### カテゴリ追加時のチェックリスト

- [ ] `categories.yaml` に新カテゴリを追加
- [ ] `keywords` に5個以上のキーワードを設定
- [ ] `hp_check_keywords` に3個以上のチェックワードを設定
- [ ] `cooperation_reason` と `approach_angle` を記述
- [ ] `target_scale`（従業員数上限）を適切に設定
- [ ] 必要に応じて `proposal_templates/{id}.md` を作成

### キーワードの改善方法

1. 検索結果のHIT率を確認
2. HIT率が低い場合:
   - `search_variations` のキーワードを `keywords` に昇格
   - 新しい検索キーワードを追加（実際の検索結果から着想）
3. 無関係な企業が多くHITする場合:
   - `hp_check_keywords` を厳格化
   - `searcher.js` の `EXCLUDED_DOMAINS` に除外ドメインを追加
