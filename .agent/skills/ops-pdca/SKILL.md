---
name: ops-pdca
description: contact-auto の日次運用PDCAサイクル。「送信→集計→分析→パッチ→検証→SKILL反映」の一気通貫フローを定義。daily-report の CHECK-1/CHECK-2 と contact-auto の学習エンジンを橋渡しする。/ops-pdca で起動。
---

> ⚠️ **作業開始前に必ず knowledge/chat_ng_registry/artifacts/NG_RULES.md を読み、Pre-flight Check を実行すること。**


# ops-pdca

> **目的**: contact-auto を毎日使いながら「同じ失敗を二度としない」仕組みを回す。

## PDCAサイクル（毎日の流れ）

```
┌─────────────────────────────────────────────┐
│  P (Plan): 本日の送信バッチを決定             │
│  → 対象シート・行範囲・プロファイルを確認      │
│  → known_errors.json で既知エラードメインを除外 │
└──────────┬──────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  D (Do): contact_auto.js 実行                │
│  → CF7 HTTP / Playwright ハイブリッド送信     │
│  → logs/cf7_evidence/ にエビデンス蓄積        │
│  → logs/unmatched_fields/ に未知フィールド蓄積 │
└──────────┬──────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  C (Check): 自動集計＋分析                    │
│  → cf7_daily_report.js で日次レポート生成     │
│  → skill_learner.js で未知フィールド学習      │
│  → known_errors.json を自動更新              │
│  → daily-report の CHECK-1/CHECK-2 で確認    │
└──────────┬──────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  A (Act): SKILL.md に確定知識として反映       │
│  → 新パターン → field_recognizer.js に追加   │
│  → 既知エラー → known_errors.json に登録     │
│  → 再発防止策 → SKILL.md に追記              │
│  → Git コミット＋プッシュ                     │
└─────────────────────────────────────────────┘
```

## 実行コマンド一覧

```bash
# 1. 送信実行
node contact_auto.js --sheets <ID> --sheet-name <名前> --rows <範囲>

# 2. 日次集計レポート生成
node cf7_daily_report.js

# 3. 既知エラーDBチェック（送信前に自動実行される）
# → contact_auto.js 内で known_errors.json を参照

# 4. スキル学習（送信後に自動実行される）
# → skill_learner.js が自動起動
```

## 3つの自動防御メカニズム

### 1. known_errors.json（既知エラーDB）

同じドメインで同じエラーが **2回以上** 発生したら自動登録。
3回目以降は送信をスキップし、手動調査待ちにする。

```
scratch/contact-auto/config/known_errors.json
```

| フィールド | 説明 |
|---|---|
| domain | エラーが発生したドメイン |
| error_type | validation_failed / spam / timeout 等 |
| first_seen | 初回発生日 |
| count | 累計発生回数 |
| auto_skip | true: 自動スキップ対象 |
| resolved | true: 修正済み（手動でtrueにする） |

### 2. skill_learner.js（dedup付き自動学習）

- 未知フィールドを自動分類＋コードパッチ
- SKILL.md への**重複追記を防止**（v0.7〜dedup実装済み）
- 同一フィールド名セットなら更新スキップ

### 3. cf7_daily_report.js（日次集計）

- テスト用ドメイン（localhost / jet-produce.com）を自動除外
- 成功率・エラー分布・ドメイン別成績をMarkdownレポートで出力
- `reports/cf7_report_YYYY-MM-DD.md` に保存

## ループ防止の5原則

| # | 原則 | 実装 |
|---|---|---|
| 1 | **同じエラーは2回まで** | known_errors.json で3回目からスキップ |
| 2 | **同じログは1回だけ** | skill_learner.js の dedup で重複追記防止 |
| 3 | **テストと本番を混ぜない** | cf7_daily_report.js の EXCLUDE_DOMAINS |
| 4 | **知識はSKILL.mdに集約** | ログの垂れ流し禁止。確定事項のみ記録 |
| 5 | **毎日 daily-report で確認** | CHECK-1/CHECK-2 で漏れを検知 |

## daily-report との連携

| daily-report のセクション | ops-pdca での役割 |
|---|---|
| CHECK-1（トラブル→スキル反映） | Act: SKILL.mdに反映されたか確認 |
| CHECK-2（調べ直し再発防止） | Check: 同じ調査を繰り返していないか |
| CHECK-3（前回ピックアップ） | Plan: 前日の未解決事項を本日の計画に |
| INCIDENT | Check: 新規エラーをknown_errors.jsonに登録したか |

## NGパターン

- ❌ エラーが出ても known_errors.json に登録せず翌日また失敗する
- ❌ skill_learner が同じログを何度もSKILL.mdに追記する
- ❌ テスト送信の結果を本番レポートに混ぜる
- ❌ 「調べ直し」が発生してもスキルに書かない
- ❌ SKILL.md のログセクションが100行を超えても放置する（古いログは references/ に移動）

## ファイル構成

```
.agent/skills/ops-pdca/
  SKILL.md                   このファイル

scratch/contact-auto/
  contact_auto.js            メインCLI
  cf7_daily_report.js        日次集計レポート
  skill_learner.js           自動学習エンジン
  config/
    known_errors.json         既知エラーDB
  reports/
    cf7_report_YYYY-MM-DD.md  日次レポート
```

## 変更履歴

- 2026-04-30: 初版作成（PDCAサイクル定義・ループ防止5原則・known_errors連携）
