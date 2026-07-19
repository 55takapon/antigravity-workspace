# iteration-3 独立QA

## 状態

- 担当: 候補実装、旧版生成、旧版採点に関与していない独立QA
- 静的QA: 完了
- 旧版対候補のcritical・回帰比較: 完了
- 本番、client本番、iteration-1、iteration-2、snapshot、candidate、eval出力は変更していない

## 読み込んだ範囲

- candidate-skillの全8ファイル
- candidate-clientのprofile.mdとlog.md
- auditの2ファイル
- designの3ファイル
- 34件のeval_metadata.json全文
- skill-checkerのSKILL.mdと63項目チェックリスト全文

## 静的QA結果

| 検査 | 判定 | 根拠 |
|:---|:---|:---|
| A36本文・posted保持 | pass | candidate-clientの#36ブロックは本番logの#36ブロックと476文字で完全一致。posted、2026-07-14、確定返信本文を改変していない |
| A36の現役模倣除外 | pass | approved-repliesはhistorical、good-outputはhistorical / non-model、profileはhistoricalとしている |
| Excel候補30件の昇格 | pass | 全件candidate / pending-user-selection、approved昇格0件。候補全文はcandidate-skillへ収録していない |
| 京都駅付き締め | pass | profileとlogでpending-user-reapproval。再承認までは生成しない |
| quality-boundaries新設候補 | pass | candidate内だけに存在し、ファイル自体をpending-user-selectionと明記。全文候補ではなくphrase-level境界だけを持つ |
| 22理由タグ | pass | feedback-loopの明示リストは22件。状態7種と失敗タグを分離している |
| 4スタイル回帰 | pass | 現役ロジック、通常出力、feedback、clientに4スタイルとstyle-mismatchなし。ヒットはchangelogの過去履歴だけ |
| NG検索分類 | pass | 作文調4締め、間接謝罪、時間・勇気、空の真摯はconfirmed-ngまたは禁止説明。具体的状況への感謝はlimited-use。A36内の真摯はhistorical / non-model |
| ローカル参照 | pass | candidate-skill内のMarkdownリンク切れ0、最大ネスト1、scriptsなし |
| A35の投稿状態 | pass | candidate-client log、本番log、approved-replies、good-outputの全てでposted、2026-07-14に整合した。返信本文と適用状態は変更されていない |
| 評価メタデータ構造 | pass | 34件、eval_id 1〜34が一意、eval_nameも一意。assertion 136件、critical 36件 |
| ★4本文なしの実動作評価 | pass | 正式34ケースは維持し、独立QAで補助1ケースを生成・採点した。感謝と改善姿勢の2文、推測・謝罪・販促CTA・SEOなしで4/4 pass、critical 0 |

## 修正・再確認

1. A35の投稿状態
   - 初回検査でcandidate-client log・本番logと共通examplesの不一致を検出した。
   - 修正後、approved-replies.mdとgood-output.mdもposted、2026-07-14になったことを再確認した。
   - 返信本文やactive-conditional判定に変更はない。

2. ★4本文なしの補助実動作テスト
   - 入力: 星4、本文なし、未返信。profileは「評価への十分な感謝＋より満足いただけるよう努める姿勢」の2文を指定し、体験・原因・不満・謝罪、販促CTA、SEO、地域名、店舗名を禁止。
   - 候補出力: 「ご評価をお寄せいただき、ありがとうございます。今後も、よりご満足いただけるよう努めてまいります。」
   - 採点: 十分な感謝、改善姿勢、根拠のない補充なし、販促・内部説明なしの4 assertionを全てpass。critical 0。

## 旧版対候補比較

| 項目 | 結果 |
|:---|:---|
| 正式評価ケース | 34件、assertion 136件 |
| 旧版 | 111/136、81.618% |
| 候補版 | 136/136、100.000% |
| critical failure | 旧版4件、候補版0件 |
| assertion回帰 | 0件 |
| ケース別回帰 | 0件 |
| rubric次元別悪化 | 16次元中0件。改善10次元、同点6次元 |
| 4スタイル出力回帰 | 0件。現役ヒットなし、changelogの廃止履歴だけ |
| client固有情報の共通混入 | 0件。鰻の神楽、京都店、京都駅、京都アバンティ、まぶし鰻・うな重の現役ヒットなし |
| 未承認候補の誤昇格 | 0件。Excel候補30件はcandidate / pending-user-selectionのまま |
| 自動適用gate | allowed=true、regression=false、collapse=false |
| 最終合否 | pass。重大エラー0、旧版からの悪化なし |
