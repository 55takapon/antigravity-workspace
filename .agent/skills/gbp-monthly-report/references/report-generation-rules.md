# 月次レポート生成の絶対ルール（R1〜R7）

旧 gbp-meo-core SKILL.md から2026-07に移管。実際に発生したバグ・インシデントから生まれたルールのため、**違反は即アウト。小手先の修正・思い込みでの実装は厳禁**。レポート生成スクリプトを実行・修正する工程で必ず読むこと。

## R1: 競合ベンチマークはクライアント固有のものを使う

```
❌ NG: DEFAULT_COMPETITORS（全クライアント共通のハードコード）
✅ OK: client_registry.js の CLIENTS[].competitors を必ず使う
```

- `SLUG_TO_CLIENT` を `Object.fromEntries` で作る際は **`competitors`** フィールドを必ず含めること
- 含め忘れると `clientInfo.competitors || []` が空配列になり競合データが消える

## R2: 業種フィールド（industry）を必ず設定する

```
❌ NG: industry: 'インターネットマーケティング' ← 全クライアント固定値
✅ OK: client_registry.js の CLIENTS[].industry を使う
```

- `industry` は `calculate_kpis.js` の投稿頻度閾値判定（`postThresholds`）に直結する
- 業種が間違っていると投稿頻度推奨が全クライアントで同じになる

## R3: 業種別 投稿頻度推奨（calculate_kpis.js）

| 業種 | 閾値 | ラベル |
|------|------|--------|
| 塾・学習 | 月2件 | 月2件（2週に1回） |
| 士業（司法書士・税理士等） | 月4件 | 月4件=週1回 |
| 飲食・美容・歯科・クリニック等 | 月8件 | 月8件=週2回 |
| デフォルト | 月4件 | 月4件=週1回 |

## R4: 同名クライアント（南校・北校）の識別

```
❌ NG: row[0] だけでブロック検出 → 英和塾南校/北校が混在
✅ OK: campus フィールドを client_registry.js に設定し row[0]+row[1] で識別
```

## R5: 前月レポートをベースに作る

月次レポート生成時は必ず前月HTMLから以下を継承・参照する:
- `extractPrevMessage(outputDir, slug, month)` で前月の担当者コメントを取得
- 前月レポートのベンチマーク数値を `fallbackReviewCount/fallbackRating` として registry に保持
- 競合他社名・社数は前月から変えない（勝手に追加・削除しない）

### ベンチマーク（競合データ）の3段階フォールバック構造

```
優先度1: Googleスクレイピング（リアルタイム値）
  ↓ スクレイピング失敗
優先度2: client_registry.js の fallbackReviewCount / fallbackRating
  ↓ registry に未設定（undefined）
優先度3: 前月HTMLレポートのベンチマークテーブルから自動抽出
  ↓ 前月レポートも存在しない
結果: 空欄 → verify_report.js が NG 判定 → 手動介入
```

**なぜ3段階必要か**: Googleのセレクタ（`span.Aq14fc`等）は予告なく変わる。変わった瞬間に全クライアントのベンチマークが一斉に空欄になる。`fallbackReviewCount` も新規クライアントでは未設定。前月HTMLからの自動復旧がないと、全件空欄のまま出力されてしまう。

## R6: 文字コード問題への対処

日本語テキストをコードファイルに埋め込む場合:
```js
// ❌ NG: ツールのreplace_file_contentでUnicode文字を直接書くと文字化けする
// ✅ OK: node -e "..." でJSON.stringify経由でファイルを生成する
const fs = require('fs');
const content = lines.join('\n');  // 日本語はNode内部で正しく保持される
fs.writeFileSync('./client_registry.js', content, 'utf8');
```

## R7: CLIプロンプトの完全一致（担当者メッセージ入力）

インタラクティブ入力時のプロンプト文言は**一言一句変えずに以下を厳守**すること。「sを入力して」と「Enter」の間にスペースを入れない等、勝手な表記揺れを許容しない。

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ ✉️  「担当者より」セクションのメッセージ
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
↳ 先月のメッセージ: 「〇〇〇〇」
  • そのまま使用する場合は Enter
  • 空欄にする場合はsを入力して Enter
  • 新しいメッセージはそのまま入力

〇月分のメッセージ >
```
- 入力が空欄(`''`)で前月メッセージがある場合は「前月メッセージ」をそのまま使用
- 入力が「`s`」の場合は空欄として確定
- 前月メッセージがない場合は以下を表示
  `  • メッセージを入力するか、空欄の場合はsを入力して Enter`
