# Codex運用で確認済みの出典

## 目的

Codex、AGENTS.md、スキル、プロンプト、品質改善を扱う時に、実際に確認した出典だけを参照する。
公式仕様、成功事例、評価手順を混ぜずに分ける。
ここにない出典を使う場合は、必ず `evidence-requirements.md` の証拠表へ追加する。
最新仕様、料金、現在の挙動、外部サイトの現状に関わる判断では、この表だけで確定せず、作業時点で本文を再確認する。

このファイルは出典表専用。作業手順は `SKILL.md`、証拠条件は `evidence-requirements.md`、出力形式は `check-memo-format.md` に置く。

## 確認済み出典

| ID | 区分 | 参照元 | 確認日 | 実物として読んだ範囲 | 確認できたこと | 採用する点 | 採用しない点 |
|:---|:---|:---|:---|:---|:---|:---|:---|
| C1 | 成功事例 | OpenAI Harness Engineering: https://openai.com/index/harness-engineering/ | 2026-05-12 | Codex運用記事のAGENTS.md/知識管理/検証ループ部分。短い確認句: "table of contents" | 約100万行、約1,500PR、社内ユーザーありと公開 | `AGENTS.md` は百科事典ではなく入口地図にする。深い資料はrepo内に分ける | 長大なAGENTS.mdへ全部詰める |
| C2 | 成功事例 | OpenAI Agents SDK OSS maintenance: https://developers.openai.com/blog/skills-agents-sdk | 2026-05-12 | OpenAI Agents SDKのAGENTS.md、スキル一覧、必須スキル使用部分。短い確認句: "narrow contract" | 3か月比較でPR数が316から457へ増加と公開 | 条件つきで必須スキルを呼ぶ。スキルは狭い役割、明確な発火条件、具体的な出力にする | すべての場面で長い検証を走らせる |
| C3 | 実ファイル | openai-agents-python AGENTS.md: https://github.com/openai/openai-agents-python/blob/main/AGENTS.md | 2026-05-12 | ルートAGENTS.mdの必須スキル使用と運用ガイド | OpenAI公式repoの実ファイル | 重要ルールを上部に置き、対象パスや変更種別でスキル使用を決める | 英語文面をそのままHermesへ移す |
| C4 | 実ファイル | openai-agents-js AGENTS.md: https://github.com/openai/openai-agents-js/blob/main/AGENTS.md | 2026-05-12 | ルートAGENTS.mdの必須スキル使用、変更履歴確認、レビュー方針 | OpenAI公式repoの実ファイル | パッケージ変更など条件が明確な時だけ追加スキルを要求する | Hermesに存在しないnpm/changeset手順を持ち込む |
| C5 | 実ファイル | OpenAI Agents SDK `code-change-verification` スキル: https://github.com/openai/openai-agents-python/tree/main/.agents/skills/code-change-verification | 2026-05-12 | 実スキル本文。短い確認句: "Confirm completion only when all commands succeed" | OpenAI公式repoの実スキル | 完了条件を明確にし、失敗時は直して再実行する | Hermesの文書変更へ重いコード検証を流用する |
| C6 | 評価事例 | Vercel AGENTS.md評価: https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals | 2026-05-12 | AGENTS.mdの資料索引、スキル発火率、評価結果 | `AGENTS.md`資料索引が100%合格、スキル既定動作は53%と公開 | 発火しないと困る入口情報はAGENTS.mdへ短く置く。詳細は読み取り先へ分ける | スキルだけに任せる |
| C7 | 公式仕様 | Agent Skills Specification: https://agentskills.io/specification | 2026-05-12 | `name`、`description`、progressive disclosure、validation | `name`は親ディレクトリ名と一致し、小文字英数字とハイフンのみ | `name`を機械用にし、表示名は本文やUIメタデータへ分ける | 日本語名をfrontmatterの`name`へ置く |
| C8 | 作成基準 | Agent Skills Best Practices: https://agentskills.io/skill-creation/best-practices | 2026-05-12 | moderate detail、output templates、checklists、validation loops | 出力形式が必要な時はテンプレートが有効と説明 | 出力が揺れる箇所だけ固定テンプレート化する | 全工程を巨大な手順書にする |
| C9 | 評価手順 | Agent Skills Evaluating Skills: https://agentskills.io/skill-creation/evaluating-skills | 2026-05-12 | evals/evals.json、with_skill/without_skill、assertions、grading | 現実的なテスト文と比較実行で品質を確認する | 発火・停止・出力形式の評価ケースを保存する | テストなしで完成扱いにする |
| C10 | 発火調整 | Agent Skills Optimizing Descriptions: https://agentskills.io/skill-creation/optimizing-descriptions | 2026-05-12 | description発火、should-trigger/should-not-trigger、複数回確認 | descriptionが発火の主要情報で、肯定/否定クエリで確認する | 発火すべき依頼と発火しない依頼を分けて評価する | キーワードだけを詰め込んで過適合させる |
