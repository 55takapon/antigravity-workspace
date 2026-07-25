# proposal-writing skill-checker report

- 対象: `C:\Users\hangy\.gemini\antigravity\.agent\skills\proposal-writing`
- チェック回数: 1
- チェックリスト項目数: 63
- 結果: pass 59 / fail 0 / n/a 4
- `SKILL.md`: raw 2,634字 / 改行除外2,548字 / 概算637トークン
- description: 140字

| カテゴリ | # | 項目 | 判定 | 根拠 |
|:--|:--|:--|:--|:--|
| C1 | 1 | YAML frontmatter | pass | `name` と `description` がある |
| C1 | 2 | name形式 | pass | `proposal-writing` は小文字英数字+ハイフン |
| C1 | 3 | description長と内容 | pass | 140字で目的、発火語、除外範囲を含む |
| C1 | 4 | SKILL.md本体のトークン数 | pass | 概算637トークンで2,000以下 |
| C1 | 5 | 時間依存情報 | pass | 変更履歴は `references/changelog.md` に分離 |
| C2 | 1 | 概要 | pass | 目的を冒頭で説明 |
| C2 | 2 | ワークフロー形式 | pass | 4ステップと完了条件がある |
| C2 | 3 | 具体例 | pass | `examples/good-output.md` に2例あり、完成提案文の良い例ではない |
| C2 | 4 | エッジケース | pass | 4件以上の表がある |
| C2 | 5 | 禁止事項 | pass | 禁止事項セクションあり |
| C2 | 6 | 冗長性排除 | pass | 詳細は references に分離 |
| C2 | 7 | 選択肢制限 | pass | 対象、構造、CTAを固定 |
| C2 | 8 | 用語一貫性 | pass | Web制作会社向けGBP協業提案で統一 |
| C2 | 9 | 義務表現 | pass | 「必ず」「してはならない」を使用 |
| C2 | 10 | ツール使用明示 | n/a | 実行時ツール利用を前提にしていない |
| C2 | 11 | Cron互換性 | pass | payload手順の埋め込みなし |
| C2 | 12 | 材料確認 | pass | 確認済み事実と未確認材料を分離 |
| C2 | 13 | 会話混入防止 | pass | 今回の叱責や作業メモは混入なし |
| C2 | 14 | 見出し品質 | pass | 見出しは意味が通る |
| C2 | 15 | Markdown品質 | pass | 自然なMarkdownで未完成タグなし |
| C2 | 16 | 実行可能性 | pass | 作業手順、出力形式、確認方法が読める |
| C3 | 1 | 日本語テキスト | pass | 全体が日本語 |
| C3 | 2 | 素人向け表現 | pass | 非エンジニアにも理解可能 |
| C3 | 3 | パスのハードコード禁止 | pass | SKILL.md内は相対参照 |
| C3 | 4 | フォルダ名非依存 | pass | references/examples の相対参照 |
| C3 | 5 | scripts品質 | n/a | scriptsなし |
| C4 | 1 | description必須要素 | pass | 目的、発火条件、トリガー語、成果物あり |
| C4 | 2 | 具体性 | pass | Web制作会社、GBP、A/B等が具体 |
| C4 | 3 | トリガー語 | pass | 「提案文を作って」「A/B案」等あり |
| C4 | 4 | 曖昧性排除 | pass | 除外範囲も明記 |
| C5 | 1 | 仕様準拠チェック | pass | C1を確認済み |
| C5 | 2 | 内容品質チェック | pass | C2を確認済み |
| C5 | 3 | 実動作テスト | pass | 2ケースの with_skill 出力で7/7 assertion pass |
| C5 | 4 | 異常系テスト | pass | 店舗型実績未確認のWeb制作会社向けを停止しないケースを確認 |
| C5 | 5 | 修正ループ | pass | 旧版failから更新後passを比較 |
| C6 | 1 | 公式推奨構造 | pass | SKILL.md + references + examples |
| C6 | 2 | ネスト制限 | pass | 対象スキル本体は1階層以内 |
| C6 | 3 | 依存宣言 | n/a | 依存パッケージなし |
| C6 | 4 | 本体内容 | pass | SKILL.mdは入口手順中心 |
| C6 | 5 | 具体例の分離 | pass | examplesに分離 |
| C6 | 6 | 参照ナビゲーション | pass | 工程内で references を読む指示あり |
| C6 | 7 | 分離省略条件 | pass | referencesを省略していない |
| C6 | 8 | 複雑作業の分離 | pass | 対象、モード、A/Bをreferences分離 |
| C6 | 9 | references粒度 | pass | 各referenceに目的、判断、確認方法がある |
| C7 | 1 | 義務表現 | pass | 必須ステップに義務表現あり |
| C7 | 2 | ゲート条件 | pass | 各ステップに進行禁止条件あり |
| C7 | 3 | 自己完了確認 | pass | 最終チェックリストあり |
| S | S1 | トークン数 | pass | 概算637トークン |
| S | S2 | 情報密度 | pass | ドメイン固有詳細はreferencesに分離 |
| S | S3 | 具体例の分離 | pass | examplesに分離 |
| S | S4 | 参照ナビゲーション | pass | 必要時に読む形で明示 |
| S | S5 | 具体例の品質 | pass | 作り物の完成提案文を承認例として置いていない |
| S | S6 | 本体の簡潔さ | pass | 本体は手順、エッジケース、禁止事項、自己確認中心 |
| S | S7 | 会話混入防止 | pass | 今回だけの注意を作業メモとして混ぜていない |
| S | S8 | references省略判定 | pass | 判断ルールがあるためreferencesあり |
| S | S9 | 作り物の具体例防止 | pass | 完成提案文の良い例は置いていない |
| S | S10 | 見出しの分かりやすさ | pass | 見出しは自然 |
| S | S11 | Markdown品質 | pass | 自然なMarkdown |
| S | S12 | 材料確認 | pass | 確認済み事実と未確認事実を分離 |
| S | S13 | 検証作業混入防止 | pass | 評価ケースや作業メモはworkspace側に分離 |
| S | S14 | 実行可能性 | pass | 作業手順と不合格時対応がある |
| S | S15 | 不自然な日本語見出し | pass | 禁止見出しなし |
| S | S16 | 成功法則の根拠 | n/a | 成功法則やA/B勝者断定を扱っていない |

## 重点確認

- `quality-gate.md`: なし
- `proposal-writing-qa`: なし
- Webマーケティング会社、広告代理店向けファイル: なし
- 旧 `sales-copywriting` 依存: なし。言及は非互換説明と禁止事項のみ
- 未確認閲覧表現: `貴社サイトで` / `制作実績を拝見` は対象スキル本体に残存なし
