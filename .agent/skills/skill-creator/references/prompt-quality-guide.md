# プロンプト品質ガイド

プロンプト、テンプレート、文章作成手順をスキルの成果物にする時の品質基準。
この資料は、公式資料で確認できるプロンプト設計の共通点を、スキル作成向けに短くまとめたもの。

## 根拠にする一次情報

- OpenAI Prompt engineering: https://developers.openai.com/api/docs/guides/prompt-engineering
- Anthropic Prompt engineering overview: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
- Anthropic Prompting best practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Anthropic Define success criteria and build evaluations: https://platform.claude.com/docs/en/test-and-evaluate/develop-tests
- OpenAI Codex Skills: https://developers.openai.com/codex/skills

## プロ品質の最低条件

プロンプト本文には、次を必ず入れる。

| 項目 | 書く内容 |
|:---|:---|
| 何をするか | 作業者が実行する具体的なタスク |
| 使う材料 | 入力、参照資料、実例、生データ、確認済みのプロ事例 |
| 見る観点 | 何を採用し、何を捨てるかの判断基準 |
| 作業手順 | 順番が重要な作業を、番号付きまたは箇条書きで書く |
| 出力形式 | 見出し、表、箇条書き、ファイル名などの完成形 |
| 確認方法 | 出力後に何を見て合格にするか |
| 不合格時の対応 | 材料不足、品質不足、根拠不足の時にどう止めるか |

## 書いてはいけないもの

- 曖昧な指示だけで終わる文。
- 作業者が補完しないと実行できない空欄。
- 未定稿表記、穴埋め指示、三点リーダーを残した本文。
- 出典や本文を確認していないプロ事例。
- 検証者が比較検証でやる作業。
- 今回の会話だけに向けた注意や叱責。

## 実例を使う時の扱い

- ユーザー提供例、生データ、公式資料、公開されている実例、ローカル実ファイルのどれを使ったかを分ける。
- プロ事例と呼ぶ場合は、実物を確認し、参照元と使った部分を分かるようにする。
- 実物を確認できない場合は、プロ事例として扱わない。
- 実例がない文章・投稿・文体・マーケティング系では、作り物の完成例を置かず、出力の型だけを示す。

## Markdownで書く理由

スキルの成果物として置くプロンプトは、人間が読んで修正しやすく、Codexが必要部分を読みやすいことが重要。
そのため、ユーザーが明示しない限り、山括弧タグ、JSONだけ、YAMLだけの形式を標準にしない。

ただし、参照したプロ事例がタグ形式でも、構造をそのままコピーしない。意味だけを読み取り、Markdown見出しに置き換える。
