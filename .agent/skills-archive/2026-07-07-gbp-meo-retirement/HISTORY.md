# 2026-07-07 GBP/MEOスキル大整理 — 方針と実施履歴

実施日: 2026-07-07
実施者: Claude Code（ユーザー承認のもと実行）
対象: `C:\Users\hangy\.gemini\antigravity\.agent\skills\` 配下の旧GBP/MEOスキル13本

---

## 1. 経緯と方針決定

### 発端
ユーザーから「初期に作った業種別GBP/MEOスキル13本が最新のスキル規則（skill-creator / skill-management / skill-update）に準じていない。実用レベルでなければ廃止でも良いのでは」との相談。プロエンジニア視点・プロマーケター視点での辛口レビューを実施した。

### レビューで確認した問題点

**エンジニア視点**
- frontmatterの `name` が日本語＋全角パイプ（規則: 小文字英数字＋ハイフン、フォルダ名と一致）。準拠は gbp-meo-core と gbp-meo-post-core のみ
- SKILL.md本体が420〜842行（推定5,000〜10,000トークン）で上限2,000トークンの3〜5倍。references/・examples/分離ゼロ（12本）
- 工程・完了条件・ゲート条件・スキップ防止パターンが皆無。「実行手順のスキル」ではなく「コンサル資料」
- real-estate / restaurant / retail / service の4本はファイル先頭にBOMがあり、frontmatter自体が認識されない恐れ
- 業種別9本は運用フロー（gbp-diagnostic / gbp-review-reply / gbp-monthly-report / gbp-meo-post-core）のどこからも参照されていない孤児
- 同一テンプレの9重コピーで矛盾が発生（例: coreのR3は塾=月2件投稿、educationの月次チェックは投稿8件以上）
- gbp-meo-core に約90ファイルのクライアント成果物（reports/）が混入。自身が本文で禁止している「skills/配下へのクライアントデータ保存」に自己違反

**マーケター視点**
- 「関連性32%」「電話数2.1倍」等の数値・成功事例に出典がなく、生成AI由来の架空事例の疑いが濃い。新基準「プロ事例は実物確認済み・出典必須」で全滅級
- 中身の約7割は「AIが既に知っている」一般論（規則カテゴリ2-7違反）
- beauty / bodywork / real-estate / retail / service の5業種は該当クライアントがゼロで、維持コストに見合わない
- 価値があるのは業種固有の法規制・カテゴリ落とし穴のみ

### 決定した方針（ユーザー承認済み）

| 対象 | 判定 |
|---|---|
| 業種別9本（beauty/bodywork/education/legal/medical/real-estate/restaurant/retail/service） | 法規部分を救出したうえで廃止（アーカイブ退避） |
| post系3本（post-dental-occlusion/post-dental-preventive/post-jetproduce） | 固有ルールをクライアントナレッジへ移管して廃止 |
| gbp-meo-core | 唯一存続。新基準準拠にリファクタ |

---

## 2. 実施事項

### 2.1 法規制テーブルの救出（廃止前の資産保全）

- 新規作成: `skills/gbp-meo-core/references/industry-regulations.md`
- 集約内容: 医療（医療広告GL・ビフォーアフター4点セット・インビザライン薬機法注記）／施術院（整体・整骨・鍼灸の資格/保険/カテゴリ/適用法規の対照表）／士業（司法書士の非弁行為・過料と罰金・抵当権抹消の3リーガルチェック含む）／教育（「学校」系カテゴリによる口コミ停止リスク・合格実績掲載ルール）／美容／飲食／不動産（徒歩80m=1分等）／工務店／小売／全業種共通のGoogleポリシー
- KPIベンチマーク・成功事例等の未検証数値は救出対象から除外（再利用禁止）

### 2.2 post系3本の固有資産移管

| 移管元 | 移管先 | 内容 |
|---|---|---|
| gbp-meo-post-dental-occlusion | `clients/sapporo-occlusion/knowledge.md`（⑱として追記） | 「体」→「身体」表記統一、CTA禁止方針、1000字構成、全角スペース改行、目的文2案、月次制作の型 |
| gbp-meo-post-dental-preventive | `clients/meet-dental/knowledge.md`（追記） | 1000字5部構成、全角スペース改行、目的文2案、CTA基本なし |
| gbp-meo-post-jetproduce | `clients/jetproduce/knowledge.md`（新規作成） | トーン＆マナー、禁止フレーズ（丸投げ・1日1分）、GBP→「Googleマップ」呼称、信憑性ルール、固定フッター190字、30のMEOあるあるテーマ、画像生成ルール（木目禁止・白基調・30代日本人女性・4:3等） |
| gbp-meo-legal セクション12（救出中に発見） | `clients/shibamoto-legal/knowledge.md`（追記） | 芝本司法書士の画像生成ルール・保存先/命名規則・2026-05-08インシデント記録 |

### 2.3 12スキルのアーカイブ退避

- 移動先: `skills-archive/2026-07-07-gbp-meo-retirement/`（skills/の外なのでスキルとしてはロードされない）
- 同フォルダの `README.md` に廃止理由と移管先マップを記載
- 削除ではないため復元可能。ただし復元より新基準準拠での作り直しを推奨

### 2.4 gbp-meo-core のリファクタ

- 旧版スナップショット: `skills/gbp-meo-core-workspace/skill-snapshot/`（SKILL.md＋references/）
- SKILL.md本体を340行→約1,100トークンに減量。descriptionへトリガー条件・委譲先を明記。未検証数値（関連性32%等）・「最終更新」日付を排除。エッジケース表・禁止事項を新基準形式で整備
- 専用スキルへの委譲表を新設（投稿=post-core、レポート=monthly-report、診断=diagnostic、口コミ=review-analysis/reply）
- クライアント成果物の移動:
  - `gbp-meo-core/reports/`（約90ファイル）→ `C:\Users\hangy\gbp-clients\_monthly-reports\`
  - `gbp-meo-core/templates/`（CSV）→ `C:\Users\hangy\gbp-clients\_report-templates\`
- 月次レポート絶対ルールR1〜R7を `skills/gbp-monthly-report/references/report-generation-rules.md` へ移管し、gbp-monthly-report/SKILL.md の工程から必読リンク

### 2.5 スクリプト・参照パスの更新（パイプライン保全）

出力先変更に伴い、以下をすべて `path.join(require('os').homedir(), 'gbp-clients', '_monthly-reports')` ベースに書き換え:

- `gbp-monthly-report/`: batch_report.js / batch_two.js / generate_report_from_sheet.js / generate_monthly_report.js / check_custom_msg.js / check_march_recs.js / debug_html.js / extract_benchmarks.js / extract_competitors.js
- `gbp-report-quality-check/scripts/verify_report.js`
- ドキュメント側: gbp-monthly-report/SKILL.md（コマンド例・出力先）、references/file-naming-and-preflight.md、gbp-meo-core/references/tools-and-appendix.md、calculate_kpis.js内コメント

検証: node実行で新パスの解決と90ファイルの認識を確認済み。

### 2.6 索引・記録の更新

- skill-management/SKILL.md「現在のスキル一覧」から廃止12行を削除、core/post-coreの行を現状に合わせ更新
- skill-management/references/changelog.md に2026-07-07のエントリ追加
- skills/README.md のGBP系テーブル・フォルダツリーを更新
- gbp-meo-core/references/practitioner-checklist.md の業種判定フローを「廃止スキル参照」から「industry-regulations.md参照」へ書き換え
- Claude Codeのメモリ（gbp-meo-skill-ecosystem.md）に本整理の要点を記録

---

## 3. 設計判断の記録（トレードオフ）

**月次レポートの保存先を per-client ではなく共有フォルダにした件**

`gbp-clients\{クライアント名}\` への個別振り分けが本来のルールだが、レポート生成スクリプトは「前月HTMLをスラッグ名で同一フォルダから探す」設計（R5の3段階フォールバック: スクレイピング→registry→前月HTML）に依存している。クライアント別に分けるには extractPrevMessage 等のコード改修とテストが必要で、月次パイプラインを壊すリスクの方が大きいと判断し、`gbp-clients\_monthly-reports\`（共有・`_`プレフィックスでクライアントフォルダと区別）とした。

per-client化する場合は、次回の月次レポート生成タイミングでスクリプト改修とセットで行うこと。

## 4. 未対応事項（今後の課題）

- gbp-meo-core/references/ 内の残存ファイル（ranking-factors.md / execution-details.md / practitioner-checklist.md / geo-optimization.md / tools-and-appendix.md）には未検証数値が残っている。SKILL.md禁止事項7で「出典未確認のままクライアント向け資料へ断言転記禁止」とガード済みだが、内容自体の検証・刈り込みは未実施
- gbp-monthly-report/ 直下に一回性のデバッグスクリプト（export_pdf_*.js / check_*.js / debug_*.js等）が多数残存。整理候補
- 5クライアント分の診断生データ破損問題（gbp-diagnostic-data-corruption）は本整理とは別件で未解決
