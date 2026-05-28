# 参照したプロ事例

このスキルは、以下の公開資料に共通する実験運用を、Hermesのスキル改善に合わせて簡略化したもの。

## 採用した共通パターン

| 共通パターン | このスキルでの扱い | 根拠 |
|:---|:---|:---|
| 成功条件を先に決める | 編集前に主判定、測り方、合格ライン、補助判定、悪化防止を固定する | OpenAI、Anthropic、Microsoft Research |
| 実データで評価する | 実際の入力と実ルートでA案/B案を出す | OpenAI、Anthropic |
| 比較しやすい形で判定する | 文章は横並びで本文を出し、良し悪しを分ける | OpenAI |
| 複雑な変更は分ける | 1回のA/Bで変える点は1つにする | Microsoft Research |
| 勝ち基準と悪化防止を分ける | 良くなった点だけでなく、本人らしさや自然さの悪化を見る | Microsoft Research、OpenAI |
| 主指標と悪化防止を分ける | 主判定を1つにし、悪化防止は別枠で落とす条件にする | Microsoft Research、Statsig、Eppo |
| 事前の分析計画を固定する | 実行前に入力、サンプル、期間、合格ライン、無効条件を決める | Optimizely、Anthropic、OpenAI |
| 閾値を持つ | 合格ラインなしの採点や採点表を無効にする | OpenAI、Anthropic |
| レビュー担当を使う | レビュー担当には実物、基準、根拠データを渡す。材料不足なら本文修正ではなく無効または前工程戻しにする | GOV.UK、DfE、Anthropic |
| 文章品質を見る | 読者に必要なこと、具体的な行動、分かりやすさ、最重要点の前出しを見る | GOV.UK、Mailchimp、Shopify、NN/g |
| 結果を残して次に使う | A/B報告を残し、同じ失敗を繰り返さない | OpenAI |

## ローカル既存スキルから取り込んだ実装

- `skill-update`: 既存スキル改善では、評価ケース、旧版比較、benchmark、修正、再評価を順番に行う。
- `marketing-pro-quality-loop`: 平均的な実務ではなく、強いプロ水準を合格基準に置き、実物ベースで監査する。
- `discord-post-builder` の `prompt-engineering-standard.md`: 成功条件を先に決め、本人投稿、チャンネル実例、悪い例と横並びで比較し、止める状態、直す状態、レビュー提出、最終OKを分ける。
- `discord-post-builder` の `evaluation-scenarios.md`: 代表ケース、素材不足、別チャンネル、ニュース共有など、実運用で崩れやすいケースを先に評価ケース化する。

## 出典

- [OpenAI: Evaluation best practices](https://platform.openai.com/docs/guides/evaluation-best-practices) — evalの目的、データ、指標、比較、継続評価を先に設計する。
- [Anthropic: Define your success criteria](https://docs.anthropic.com/en/docs/test-and-evaluate/define-success) — 成功条件は具体的で測れる形にする。
- [Anthropic: Create strong empirical evaluations](https://docs.anthropic.com/en/docs/test-and-evaluate/develop-tests) — 現実のタスクに近い評価データとテストケースを作る。
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) — 生成担当と評価担当を分ける場合でも、明確な評価基準と実環境の根拠が必要。
- [Microsoft Research: Patterns of Trustworthy Experimentation, Pre-Experiment Stage](https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-pre-experiment-stage) — 仮説と指標を先に決め、複雑な変更は単純な変更へ分ける。
- [Statsig: Configuring Experiments](https://docs.statsig.com/stats-engine) — 仮説、主指標、補助指標などを実験設定として持つ。
- [Statsig: What are guardrail metrics in A/B tests?](https://statsig.com/blog/what-are-guardrail-metrics-in-ab-tests) — 主指標が良くても、別の重要指標が悪化していないかを見る。
- [Eppo: Guardrail cutoffs](https://docs.geteppo.com/data-management/organizing-metrics/guardrails) — 悪化させたくない指標に事前の下限を置く。
- [Optimizely: Configure a Frequentist Fixed Horizon A/B test](https://support.optimizely.com/hc/en-us/articles/39611609646349-Configure-a-Frequentist-Fixed-Horizon-A-B-test) — 開始前にサンプルサイズや期間などの分析計画を固定する。
- [GOV.UK: Reviewing and publishing content](https://www.gov.uk/guidance/how-to-publish-on-gov-uk/reviewing-and-approving-content) — 作成者が提出し、別の人がスタイルとエラーを確認する。
- [DfE: Quality and assurance](https://design.education.gov.uk/content-design/quality-and-assurance) — 2人目確認は最終版を文脈内で見る。事実確認などはその前に済ませる。
- [GOV.UK: User needs](https://www.gov.uk/guidance/content-design/user-needs) — コンテンツはユーザーが何をしたいかから作る。
- [Mailchimp: Writing goals and principles](https://styleguide.mailchimp.com/writing-principles/) — 読者が必要な情報を、分かりやすく役に立つ形で伝える。
- [Shopify Polaris: Content fundamentals](https://polaris-react.shopify.com/content/fundamentals) — 読者が次に何をするかに集中し、必要な言葉だけを残す。
- [NN/g: Inverted Pyramid](https://www.nngroup.com/articles/inverted-pyramid/) — 大事な情報を先に置き、読者が早く要点を取れるようにする。

## Hermes向けの置き換え

一般的なWeb A/Bでは、ユーザーをランダムに分けて数値を見る。Hermesのスキル改善では、同じユーザー入力をA案とB案に通し、成果物の実物を比べる。

そのため、このスキルでは「統計的に勝った」とは言わない。代わりに、以下を必須にする。

- 同じ入力で比べた。
- 同じルートで比べた。
- 変えた点は1つだけ。
- A案とB案の本文を見た。
- 主判定、測り方、合格ラインを編集前に決めた。
- 悪化防止の許容ラインを編集前に決めた。
- 良くなった点と悪くなった点を分けた。
- 根拠が弱い変更は残さない。
