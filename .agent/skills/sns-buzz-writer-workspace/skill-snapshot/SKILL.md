---
name: sns-buzz-writer
description: >-
  入力テキスト（体験談・ノウハウ・文字起こし素材等）からX（旧Twitter）長文・Threads・
  Instagramキャプションのバズ狙い投稿文を作成する。管理者が進行を仕切り、執筆と辛口品質
  チェックは別々のサブエージェントに分業させ、X版のユーザー承認後にThreads/IG版を並列作成
  する承認ゲート式ワークフロー。「SNS投稿を作って」「Xの投稿文にして」「バズる文章にして」
  「この話をSNSに」と言われたら必ずこのスキルを使うこと。成果物は clients 配下のアカウント別
  sns-posts フォルダに x.md / threads.md / instagram.md / qa-report.md として保存する。
  Googleマップ（GBP）投稿の作成には使わない（gbp-meo-post-core を使う）。
---

# sns-buzz-writer

入力テキスト1本から、X（長文）→ ユーザー承認 → Threads・Instagram の順に投稿文を作る。
実行者（管理者）は進行管理・報告・承認ゲートに徹し、**執筆と品質採点は必ずサブエージェントに分業させる**こと。

## ステップ1: 入力整理

必要資料: [references/01_orchestration.md](references/01_orchestration.md) の工程1をこの工程で必ず読む。

- [ ] 素材テキスト・目的・ターゲット・アカウントを「入力カード」に整理した
- [ ] アカウント素材（sns-profile.md / jetproduce の knowledge.md / knowledge-taka-jet の台帳）を確認した
- [ ] 一次情報（本人の体験・数字・エピソード）が素材に含まれることを確認した

#### 完了条件
- 入力カードが全項目埋まっていること。一次情報ゼロ・目的不明の場合は執筆に進まず、質問をまとめてユーザーに出すこと
- この完了条件を満たすまで、次のステップに進んではならない

## ステップ2: X長文の作成（writerサブエージェント）

必要資料: サブエージェントへの指示文は [references/01_orchestration.md](references/01_orchestration.md) の工程2を必ず使う。writerには [references/x-writing-rules.md](references/x-writing-rules.md) と [references/copywriting-frameworks.md](references/copywriting-frameworks.md) を必ず読ませる。

- [ ] writerサブエージェントを起動し、本命案1本＋代替フック案2本を作成させた
- [ ] 管理者自身は本文を書いていない

#### 完了条件
- 本命案・代替フック案・使用した型と選定理由・想定文字数が揃っていること

## ステップ3: 辛口品質チェック（QAサブエージェント・省略禁止）

必要資料: QAには [references/qa-criteria.md](references/qa-criteria.md) を必ず読ませ、その採点表形式で報告させる。

- [ ] writerとは別のQAサブエージェントが7軸採点を実行した
- [ ] 不合格の場合はwriterへ差し戻して改稿→再QA（最大3回。3回不合格ならユーザーへ報告）

#### 完了条件
- QA合格（総合56/70以上・安全性10/10・5点以下の軸なし）のレポートがあること
- この完了条件を満たすまで、次のステップに進んではならない

## ステップ4: ユーザー承認ゲート（スキップ不可）

必要資料: 報告形式は [references/01_orchestration.md](references/01_orchestration.md) の工程4に従う。

- [ ] 本命案・代替フック案・QA採点表をユーザーに提示し、確認を依頼した
- [ ] 修正指示があれば writer に反映させ、再QA→再報告した

#### 完了条件
- ユーザーの明示的なOKが出ていること。**OKが出るまでThreads/Instagram作成に進んではならない**

## ステップ5: Threads・Instagram版の並列作成

必要資料: 各writerに [references/threads-writing-rules.md](references/threads-writing-rules.md) / [references/instagram-writing-rules.md](references/instagram-writing-rules.md) と [references/copywriting-frameworks.md](references/copywriting-frameworks.md) を必ず読ませる。

- [ ] 承認済みX版を素材として、Threads用・Instagram用のwriterサブエージェントを並列起動した
- [ ] コピペ・語尾変更だけのリライトになっていないことを各writerに自己照合させた

## ステップ6: 最終品質チェックと保存・報告（省略禁止）

- [ ] Threads版・IG版それぞれにQAサブエージェントの7軸採点を実行した（不合格は差し戻し最大3回）
- [ ] 成果物を保存規則（[references/01_orchestration.md](references/01_orchestration.md) 工程5）どおり `clients\{アカウント}\sns-posts\` 配下へ保存した
- [ ] 3プラットフォームの本文全文・QA採点表・保存先パスをユーザーに報告した

## エッジケース

| 状況 | 対応 |
|:-----|:-----|
| 素材に一次情報が全くない | 執筆に進まず質問する（examples/good-output.md の異常系参照） |
| サブエージェント機能が使えない環境 | 役割（writer/QA）を明示的に宣言して切り替え、同一応答内で執筆と採点を混ぜない |
| QA3回不合格 | 根本原因・試した改稿・選択肢を添えてユーザーへ報告し指示を仰ぐ |
| X以外だけ欲しい（例:Threadsのみ） | ステップ2〜4を該当プラットフォームで実施。承認ゲートは省略しない |
| 素材が長すぎる（文字起こし全文等） | 入力カードには全文を保持しつつ、writerへは使用箇所の指定を添える |
| クライアント店舗の宣伝投稿を頼まれた | 自社発信用スキルのため、固有実績の扱いをユーザーに確認してから進める |

## 禁止事項

- 管理者が投稿文を執筆・添削してはならない（writerサブエージェントの担当）
- 管理者が品質採点をしてはならない（QAサブエージェントの担当）
- QAチェックとユーザー承認ゲートをスキップして先の工程へ進んではならない
- 一次情報のない一般論だけの投稿を生成してはならない
- 旧sns/スキルの固定エンゲージメント係数（リプライ150倍等）を根拠に使ってはならない（現行アルゴリズムで廃止済み。詳細は references/x-writing-rules.md）
- 成果物をスキルフォルダ内に保存してはならない
- 効果の保証・根拠のない数値断言・エンゲージメントベイトを含む文を通過させてはならない

## 自己完了確認（完了報告の前に必ず実施）

- [ ] ステップ1〜6をすべて実行した（未実施があれば完了報告してはならない）
- [ ] 執筆・採点がすべてサブエージェント（または明示的な役割分離）で行われた
- [ ] ユーザー承認ゲートを通過した記録がある
- [ ] 保存先パスと全本文をユーザーに報告した
