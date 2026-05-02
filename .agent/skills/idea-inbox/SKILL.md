---
name: idea-inbox
version: 2.0.0
description: >
  アイデア・思いつき・メモをクリエイティブ源泉として蓄積・整理するスキル。
  daily-report とは完全分離。実施前提ではなく「忘れないための置き場」として運用する。
  デフォルトはサイレント保存モード。「応答して」を含む場合のみフル応答する。
triggers:
  - "idea:"
  - "アイデア:"
  - "アイデア追加"
  - "思いついた"
  - "メモ："
  - "メモ:"
  - "idea-review"
  - "アイデアまとめ"
  - "応答して"
---

> ⚠️ **作業開始前に必ず knowledge/chat_ng_registry/artifacts/NG_RULES.md を読み、Pre-flight Check を実行すること。**

# 💡 idea-inbox スキル

## 目的

- アイデア・思いつき・気づきを **Discord から随時投入** し、`ideas/inbox/` に蓄積する
- **daily-report とは完全分離**。実施済みタスクとは関係なく保存する
- 毎日 **22:00 JST に自動まとめ**（`ideas/digest/YYYYMMDD_digest.md` を生成）
- 必要なときに「アイデア出して」と声かけすれば参照する

---

## 🔀 モード判定（最優先ルール）

メッセージを受け取ったら、**まず以下の判定を行うこと**：

| 条件 | モード | 挙動 |
|---|---|---|
| メッセージに `応答して` を含む | **応答モード** | 通常のフル応答。Discord に詳細を返す |
| `アイデアまとめ` / `idea-review` / `アイデア出して` | **応答モード** | digest 生成 or 一覧表示して Discord に返す |
| 上記以外（通常メモ） | **サイレントモード** | inbox に保存 + `✅` だけ返す |

> ⚠️ **サイレントモードでは詳細なレポートを Discord に返さないこと。**  
> 毎回通知が来るのはノイズになるため、`✅` のみで完結させる。

---

## トリガーパターン

以下いずれかの入力でこのスキルが起動する：

| 入力例（Discord） | モード | 動作 |
|---|---|---|
| `idea: LP案を全面リニューアルしたい` | サイレント | inbox に保存、✅ のみ返す |
| `アイデア: コーチング動画を短尺で出す` | サイレント | inbox に保存、✅ のみ返す |
| `思いついた：〇〇` | サイレント | inbox に保存、✅ のみ返す |
| `メモ：〇〇` / `メモ: 〇〇` | サイレント | inbox に保存、✅ のみ返す |
| `〇〇 応答して` | 応答 | inbox に保存 + Discord にフル応答 |
| `アイデアまとめ` / `idea-review` | 応答 | digest を手動生成して返却 |
| `アイデア出して` / `アイデア見せて` | 応答 | inbox + digest を一覧表示 |

---

## Task: アイデア保存（save）

### 保存ファイルフォーマット

保存先: `C:\Users\hangy\.gemini\antigravity\ideas\inbox\YYYYMMDD_HHMMSS.md`

```markdown
---
date: YYYY-MM-DD HH:MM JST
source: discord
tags: []
---

# [アイデアのタイトル（先頭30文字程度）]

[入力された内容をそのまま記録]
```

### 保存手順

1. 現在時刻（JST）を取得して `YYYYMMDD_HHMMSS` 形式でファイル名を決定
2. 入力テキストから先頭30文字程度でタイトルを自動生成
3. `ideas/inbox/` に保存（`write_to_file` — 承認不要）
4. **モード判定に従って Discord へ返す**

**サイレントモードの場合（デフォルト）:**
```
✅
```
*それ以外は一切返さない。詳細レポート禁止。*

**応答モードの場合（「応答して」を含む）:**
```
✅ アイデアを保存しました
📁 ideas/inbox/YYYYMMDD_HHMMSS.md
💡 「[タイトル]」
（inbox合計: N件）
```

---

## Task: 自動まとめ（daily-digest）

> cron: `0 22 * * *` / timezone: `Etc/GMT-9`

### まとめ生成手順

1. `ideas/inbox/` 内の **当日分（日付が今日のもの）** を全件読み込む
2. **過去7日分の未まとめファイル**も対象に含める（取りこぼし防止）
3. `ideas/digest/YYYYMMDD_digest.md` に以下フォーマットで書き出す
4. Discord に完了通知を送る

### digest フォーマット

```markdown
---
date: YYYY-MM-DD
inbox_count: N
period: YYYY-MM-DD〜YYYY-MM-DD
---

# 💡 アイデアダイジェスト — YYYY-MM-DD

## 本日の投入アイデア（N件）

### 1. [タイトル]
> 投入: HH:MM
[内容]

### 2. [タイトル]
...

## 過去7日間の未まとめアイデア（N件）

（あれば同形式で列挙）

---
*次回まとめ: 翌日22:00 JST*
```

5. Discordへの通知メッセージ例：
```
📋 アイデアダイジェスト生成完了
本日: N件 / 累計未整理: M件
💡 トップアイデア: 「[今日の最初のアイデア]」
👉 ideas/digest/YYYYMMDD_digest.md
```

---

## Task: アイデア一覧表示（list）

「アイデア出して」「アイデア見せて」と言われたとき：

1. `ideas/inbox/` の全ファイルを日付降順で一覧化
2. `ideas/digest/` の最新digestを参照
3. Discord に以下形式で返す：

```markdown
## 💡 アイデア一覧（inbox: N件）

**直近7日間:**
- [日付] [タイトル]
- [日付] [タイトル]
...

**もっと古いアイデア:** M件
（「古いアイデアも出して」で全件表示）
```

---

## cron 登録方法

Discord で以下を実行：

```
/schedules
```

新規スケジュール追加 → 以下を設定：

| 項目 | 値 |
|---|---|
| cron | `0 22 * * *` |
| timezone | `Etc/GMT-9` |
| prompt | `idea-review` |

---

## ファイルパス一覧

| 用途 | パス |
|---|---|
| inboxフォルダ | `C:\Users\hangy\.gemini\antigravity\ideas\inbox\` |
| digestフォルダ | `C:\Users\hangy\.gemini\antigravity\ideas\digest\` |
| README | `C:\Users\hangy\.gemini\antigravity\ideas\README.md` |

---

## 制約・ルール

- **daily-report には一切書かない**（完全分離）
- **実施前提でカテゴリ分けしない**（ただの置き場として運用）
- **アイデアを削除しない**（inbox は追記のみ、削除禁止）
- **呼ばれたときだけ出力する**（自動でdaily-reportに混入させない）
- **サイレントモードでは `✅` 以外 Discord に返さない**（通知ノイズ防止）
- **「応答して」があるときだけフル応答する**（明示的な応答要求のみ）
- **inbox への書き込みは必ずワークスペース内パスを使う**（承認不要のため）
