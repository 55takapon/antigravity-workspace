# iteration-4 現行ルール移行表

目的: 禁止中心の設計を、`最小安全核 + profile/業種境界 + 該当良好全文例 + 最終事実検査`へ再編する。ここでは削除を実行せず、現行ルールの行き先と削除前条件を決める。

## 分類

- **安全核として維持**: 全クライアント共通で、違反時に重大事故となる最小限のルール。
- **profile・業種へ移管**: 文体、歓迎、謝罪、業種固有の公開範囲など、共通ハード禁止にしないもの。
- **良好例で代替**: 抽象命令より、入力・全文・理由・不適用条件で示すもの。
- **重複撤廃**: 別の安全核・例・profileで担保でき、実行時の反復を減らすもの。
- **保留**: ユーザー確定境界、証跡、または判断材料不足のため、勝手に削除・移管しないもの。

## 絶対安全6群

| ID | 維持する安全核 | 主な現行根拠 |
|:---|:---|:---|
| K1 | 口コミにない事実・感情・効果を作らず、原文より評価・感情の強度を上げない | `SKILL.md:70-71`; `reply-rules.md:80-83` |
| K2 | 個人情報、診療、相談、契約情報を拡張しない | `SKILL.md:73`; `reply-rules.md:89,181-211` |
| K3 | 未確認の原因・改善・対応を断定しない | `SKILL.md:70`; `reply-rules.md:80,146-165,215` |
| K4 | 反論、責任転嫁、評価変更・見返り要求をしない | `SKILL.md:72`; `reply-rules.md:90-91` |
| K5 | profile未許可の販促・SEOを足さない | `SKILL.md:74-75`; `reply-rules.md:111-124` |
| K6 | 返信済み状態と公開リスクを無視しない | `SKILL.md:17-25,51-55`; `reply-rules.md:31-33,213-218` |

この6群は削除対象ではない。候補版では散在する文を6群へ集約し、評価ケースで維持する。

## A. SKILL.md

| ID | 現行箇所 | 現行要旨 | 分類 | 理由 | 代替例 / 評価ケース予定 | 削除・移管前条件 |
|:---|:---|:---|:---|:---|:---|:---|
| S01 | `SKILL.md:12` | 販促より事実性・安全性、責任分離 | 安全核として維持 | スキル目的の最上位原則 | K1〜K6全ケース | なし。短文化のみ可 |
| S02 | `SKILL.md:16-20` | 入力、profile、log、knowledge、返信済み確認 | 安全核として維持 | K5・K6の入口 | EV-REPLIED、EV-KNOWLEDGE | profile探索と返信済み分岐が評価で通ること |
| S03 | `SKILL.md:22-26` | 明記事実、強度、禁止推測、公開リスクを内部整理 | 安全核として維持 | K1・K2・K6の事前判定 | EV-AMBIGUOUS、EV-HIGH-RISK | 装飾分類へ置換しない |
| S04 | `SKILL.md:28-32` | 基本構造、星別2文、歓迎、L1〜L4、謝罪・真摯の細則 | 良好例で代替 | 1段落へ高評価・低評価の多数判断が密集し、抽象衝突を生む | EX-STAR5-NO-TEXT、EX-POS-SHORT、EX-LOW-L1〜L4 | 各分岐にactive例2件以上と回帰ケースがあること。K1〜K6は残す |
| S05 | `SKILL.md:30` | ★5本文ありは歓迎原則、★4は歓迎または姿勢 | profile・業種へ移管 | 業種・クライアント・温度で自然な終止が異なる | EX-FOOD-POS、EX-MEDICAL-POS | 飲食と高リスク業種を別例で確認 |
| S06 | `SKILL.md:30,64` | 低評価severity、謝罪、具体行動の詳細 | 良好例で代替 | severity自体は有用だが、語句規制より全文例が実務的 | EX-LOW-MINOR、EX-LOW-CONFIRMED、EX-LOW-DISPUTED | 未確認事実・架空改善が0件であること |
| S07 | `SKILL.md:34-38` | 事実・感情・CTA・低評価語句等を全文検査 | 重複撤廃 | K1〜K6と`reply-rules`に重複。実行時に禁止語を過度に想起させる | 最終K1〜K6チェック | 6群チェックへ圧縮し、既存critical回帰0 |
| S08 | `SKILL.md:36,63` | 同一感情文・同一骨格の連続を避ける | 良好例で代替 | 「違う文章を作る」ことが目的化しやすい | EX-BATCH-3 | 自然な標準締めの重複を合格にできること |
| S09 | `SKILL.md:37` | 通常は最終返信案だけを出す | 安全核として維持 | 公開用成果物の実用性に直結 | EV-OUTPUT-ONLY | 低評価注意メモ例も別枠で確認 |
| S10 | `SKILL.md:40-44,66` | 修正時は全文再構成・再検査 | 安全核として維持 | patch回帰防止の工程ルール | EV-REVISION-REGRESSION | 局所パッチ回帰ケース合格 |
| S11 | `SKILL.md:41-43` | 確定結果だけlogへ記録 | 安全核として維持 | 採用・投稿済みの捏造防止 | EV-LOG-STATE | 生成工程から記録工程を分離 |
| S12 | `SKILL.md:46-55` | 星だけ、返信済み、高リスク、★4、低評価、外国語 | 良好例で代替 | エッジケース表が生成細則の再掲になっている | 各カテゴリactive例とEV群 | 各行の代替例または安全ケースが存在すること |
| S13 | `SKILL.md:57-66` | 7項目の自己完了確認 | 重複撤廃 | 工程4・禁止事項・reply-rulesチェックと三重化 | K1〜K6＋output check | skill-checkerでcritical漏れ0を確認 |
| S14 | `SKILL.md:70-75` | 事実、強度、反論、privacy、knowledge、販促禁止 | 安全核として維持 | K1〜K5に該当 | EV-FACT、EV-PRIVACY、EV-CTA | 6群へ統合して意味を狭めない |
| S15 | `SKILL.md:76` | 単一クライアントだけで共通変更しない | 安全核として維持 | ガバナンス上の過適合防止 | EV-PROMOTION-SCOPE | feedback-loopのE/C/I/Uと一箇所へ集約可 |

## B. references/reply-rules.md

| ID | 現行箇所 | 現行要旨 | 分類 | 理由 | 代替例 / 評価ケース予定 | 削除・移管前条件 |
|:---|:---|:---|:---|:---|:---|:---|
| R01 | `reply-rules.md:5-15` | 目的と7段の優先順位 | 安全核として維持 | K1〜K6の優先順位を定める | 全criticalケース | 6群と矛盾しない短い順序へ整理 |
| R02 | `reply-rules.md:17` | 公開例をコピーせず、通常生成で全文例を読まない | 良好例で代替 | 今回の設計転換と直接衝突。具体例がruntimeへ届かない | EX-ROUTER | 該当カテゴリだけ最大2〜3例を読む軽量ルーターができること |
| R03 | `reply-rules.md:19-33` | 9項目の内部整理 | 重複撤廃 | 必要だがSKILL工程2と重複 | K1〜K6 router inputs | 本文、評価帯、事実、risk、profile、stateを欠かさない |
| R04 | `reply-rules.md:35` | 店側感情を条件付き使用 | profile・業種へ移管 | 文体・温度・「スタッフ一同」はclient差が大きい | EX-VOICE-WARM / EX-VOICE-DRY | 共通では事実捏造だけK1として残す |
| R05 | `reply-rules.md:37-59` | 基本3要素と星・長さ別の作り方 | 良好例で代替 | 実務で必要なのは全文のつながり。固定2文も抽象命令化している | EX-STAR4/5、EX-POS、EX-MIXED | 各入力群のactive例2件以上 |
| R06 | `reply-rules.md:61` | 星と本文の不一致、曖昧語を決めつけない | 安全核として維持 | K1の重要境界 | EV-AMBIGUOUS-QUANTITY | 正負変換が0件 |
| R07 | `reply-rules.md:63-65` | 自然さ優先と飲食の標準歓迎 | profile・業種へ移管 | 飲食では有用だが全業種共通ではない | EX-FOOD-CLOSING | 飲食active例とprofile制御を用意 |
| R08 | `reply-rules.md:67-74` | 作文調4締めと冷淡終止 | 保留 | ユーザー確定NG。設計転換だけで勝手に消せない | QB03〜QB07、EV-NATURAL-CLOSING | ユーザーが例中心への統合方法を個別承認するまで保持 |
| R09 | `reply-rules.md:80-85` | 事実・強度・内心・曖昧変換・販促漏入・星だけ補充 | 安全核として維持 | K1・K5のcritical | EV-FACT/INTENSITY/STAR-ONLY | 意味を落とさずK1/K5へ圧縮 |
| R10 | `reply-rules.md:86,92-94` | 空虚文、機能重複、感情終止、バッチ骨格反復 | 良好例で代替 | 品質嗜好をハードエラーにすると無難で硬い文へ寄る | EX-COMPLETE、EX-BATCH-3 | 自然さ採点が現行以上、critical 0 |
| R11 | `reply-rules.md:87-88` | 再来店約束・指定、コメントなし言及 | 良好例で代替 | 危険は販促と捏造でK1/K5に残る。自然な歓迎との差は例が明確 | EX-WELCOME / EX-STAR-ONLY | 催促と歓迎の対比例があること |
| R12 | `reply-rules.md:89-91` | privacy、反論、評価変更・見返り | 安全核として維持 | K2・K4のcritical | EV-PRIVACY、EV-RETALIATION | なし |
| R13 | `reply-rules.md:95,220-222` | 修正時の全文再構成 | 安全核として維持 | 工程事故の防止 | EV-REVISION-REGRESSION | SKILLと一箇所へ集約可 |
| R14 | `reply-rules.md:97-113` | profile項目、knowledge境界、profileなし既定 | profile・業種へ移管 | 共通skillは読込契約だけ持ち、voice項目はprofileへ置く | EV-PROFILE-OFF、EV-KNOWLEDGE | profile schemaとfallback例が完成 |
| R15 | `reply-rules.md:115-124` | CTA、歓迎、地域文脈、SEO | profile・業種へ移管 | 自然な歓迎まで共通禁止の影響を受けやすい | EX-FOOD-WELCOME、EV-REGIONAL-OFF | K5を残し、client許可と業種例を用意 |
| R16 | `reply-rules.md:126-131` | 直近5件、感情文・骨格重複、標準締め重複可 | 良好例で代替 | 頻度管理を文章生成の中心にしない | EX-BATCH-3 | `posted/final_approved`限定はfeedback運用に残す |
| R17 | `reply-rules.md:133-142` | L1〜L4 severity matrix | 良好例で代替 | リスク分岐は必要だが、ラベル自体より場面別全文が有効 | EX-LOW-L1〜L4 | 同一入力で過少/過剰対応がなく、架空行動0 |
| R18 | `reply-rules.md:144-155` | 謝罪条件、NG謝罪語、使用例 | 保留 | ユーザー確定した重要境界。例中心化で無断撤廃しない | QB08/QB09、EX-LOW-CONFIRMED | 個別承認後に良好/NG対比例へ移せる。K3は維持 |
| R19 | `reply-rules.md:156-165` | 「真摯」を固定せず、具体行動と複数pattern | 良好例で代替 | 4文型を並べるより、場面と全文で示す | EX-LOW-ACTION-1〜3 | 実行可能性確認をK3として残す |
| R20 | `reply-rules.md:167-171` | 低評価の感謝、limited-use、時間・勇気NG | 保留 | ユーザー確定済みの良好/NG境界 | QB11〜QB15、EX-LOW-GRATITUDE | ユーザーが全文例への統合を確認するまで保持 |
| R21 | `reply-rules.md:173-175` | 対応内容で第三者の安心を形成 | 良好例で代替 | 「安心形成」は抽象的。良い低評価全文で学ばせる | EX-LOW-PUBLIC-READ | 自己宣伝なしで対応が具体的な例を承認 |
| R22 | `reply-rules.md:177-186` | 医療・福祉のprivacyと効果 | 安全核として維持 | K2の高リスクcritical | EV-MEDICAL-PRIVACY | 外国語/星だけも含む回帰合格 |
| R23 | `reply-rules.md:187-211` | 飲食、美容、士業、BtoB、小売の詳細 | profile・業種へ移管 | 共通runtimeへ全業種細則を常時載せる必要がない | 業種別active例、EV-INDUSTRY | 該当業種だけ選択参照できること。K1/K2は共通に残す |
| R24 | `reply-rules.md:213-218` | 低評価、返信済み、外国語 | profile・業種へ移管 | 返信済みはK6、外国語と窓口はprofile差 | EV-REPLIED、EX-FOREIGN | state gateは共通に残す |
| R25 | `reply-rules.md:224-239` | 14項目の投稿前チェック | 重複撤廃 | SKILL工程4、自己確認、ハードエラーと重複 | K1〜K6＋output check | 現行critical case回帰0 |
| R26 | `reply-rules.md:241-254` | 公式情報一覧と最新確認 | 安全核として維持 | 高リスク判断の根拠 | EV-POLICY-CURRENT | 詳細はevidenceへ一本化可 |

## C. feedback-loop / evidence

| ID | 現行箇所 | 現行要旨 | 分類 | 理由 | 代替例 / 評価ケース予定 | 削除・移管前条件 |
|:---|:---|:---|:---|:---|:---|:---|
| F01 | `feedback-loop.md:16-53` | 確定時だけlog記録、状態と形式 | 安全核として維持 | 投稿済み・承認事実の捏造防止 | EV-LOG-STATE | 生成runtimeとは分離 |
| F02 | `feedback-loop.md:55-86` | 22理由タグと低評価pattern | 重複撤廃 | 生成規則を失敗タグで再記述している | 最小原因タグ＋例ID | 既存ログのタグ互換表を作り、履歴を改変しない |
| F03 | `feedback-loop.md:88-102` | phrase-level 7状態 | 安全核として維持 | `candidate`等を無断で`active`へ昇格させない承認ガバナンスであり、良好例本文では代替できない。状態定義と遷移は例レジストリで維持し、通常生成runtimeからだけ外す | EX-STATE-ROUTER | active/candidate/historicalの状態定義・承認者・遷移条件を保持し、通常生成がactive以外を参照しないこと |
| F04 | `feedback-loop.md:104-115` | E/C/I/U昇格 | 安全核として維持 | 過適合防止のガバナンス | EV-PROMOTION-SCOPE | なし |
| F05 | `feedback-loop.md:117-127` | critical 0を採用率より優先 | 安全核として維持 | 安全核の回帰防止 | 全critical suite | 自然さ評価と別軸にする |
| F06 | `feedback-loop.md:129-135` | 実承認だけをapprovedへ登録 | 安全核として維持 | 作り物の承認例を防ぐ | EV-CANDIDATE-NOT-APPROVED | 外部記事由来はscenario/candidateと明示 |
| F07 | `feedback-loop.md:137-141` | profile初期化・項目 | profile・業種へ移管 | client固有の管理契約 | EV-PROFILE-SCOPE | 共通本文へclient情報0 |
| F08 | `feedback-loop.md:143-153` | 全再検査と確認方法 | 重複撤廃 | SKILLとreply-rulesの再掲 | K1〜K6 | feedback記録の検査だけ残す |
| E01 | `evidence.md:1-15` | 出典階層と適用限界 | 安全核として維持 | 外部例と公式根拠の混同防止 | EV-SOURCE-LEVEL | 通常生成では必要節だけ参照 |
| E02 | `evidence.md:19-39` | 19材料カード | 保留 | 履歴・根拠台帳であり、今回の生成設計だけで削除不可 | 出典監査 | runtimeルーターからは外せるが本文削除は別判断 |
| E03 | `evidence.md:41-47` | ユーザー確認済み良好/NG境界 | 保留 | ユーザー確定事項。勝手に再解釈しない | QB01〜QB19 | 個別の移行承認が必要 |
| E04 | `evidence.md:49-95` | 材料の扱い、高/中/低/星だけ、AI差別化 | 重複撤廃 | reply-rulesと大幅重複 | K1〜K6＋active例 | 出典台帳から実行規則を分離 |
| E05 | `evidence.md:97-101` | 返信タイミング目安 | 保留 | 今回の文章生成再設計とは別論点 | EV-TIMING（必要なら） | 根拠の現在性確認後に別判断 |
| E06 | `evidence.md:103-125` | 確認方法、不合格対応、除外材料 | 重複撤廃 | K1〜K6とsource-levelへ統合可能 | EV-SOURCE/CRITICAL | evidenceの証拠責務は残す |

## D. examples / changelog

| ID | 現行箇所 | 現行要旨 | 分類 | 理由 | 代替例 / 評価ケース予定 | 削除・移管前条件 |
|:---|:---|:---|:---|:---|:---|:---|
| X02 | `good-output.md:1-5,128-134` | 出力形式と参照条件 | 安全核として維持 | 最終文だけ出す要件と例の出典管理 | EV-OUTPUT-ONLY | 軽量ルーターへ分離可 |
| X03 | `good-output.md:7-88` | A35、U-R04、U-R05 | 良好例で代替 | iteration-4のactive例資産として再分類できる | EX-POS-DETAILED / EX-POS-SHORT | A35は設計上`active-conditional`を推奨するが、本番変更前に統括・ユーザー確認を得る。U-R04/U-R05の承認範囲を維持 |
| X04 | `approved-replies.md:16` と `good-output.md:14` | A35が`active`と`active-conditional`で不一致 | 保留 | profileのvoiceと事業者感情の条件があるため設計上は`active-conditional`が整合的。ただし投稿済み事実と状態変更は別であり、統括・ユーザー確認が必要 | EV-STATE-A35 | 本番反映前に`active-conditional`への統一を統括・ユーザーが確認するまで移動・変更しない |
| X05 | `good-output.md:90-126`; `approved-replies.md:19` | A36はposted historical / non-model | 安全核として維持 | 投稿済み証跡を保持し、模倣させない | EV-A36-NONMODEL | 本文改変・active化をしない |
| X06 | `approved-replies.md:20-33,35-366` | 旧承認13件のhistorical/deprecated全文 | 保留 | 履歴証跡。通常runtimeへは不要だが削除禁止 | archive-only gate | 通常ルーターから0件参照、履歴本文保持 |
| X07 | `changelog.md:1-42` | iteration履歴と廃止履歴 | 安全核として維持 | 過去判断の監査証跡 | changelog append-only check | 既存履歴を削除・改変しない |

## E. quality-boundaries QB01〜QB19 個別移行

phraseの履歴証跡は削除しない。以下の「移行」はcandidateの通常runtimeでの扱いを指し、原台帳の改変・削除を意味しない。

| ID | 現行状態・要旨 | 分類 | iteration-4での移行先 / 保持理由 | 削除・runtime解除条件 |
|:---|:---|:---|:---|:---|
| QB01 | confirmed-good: 飲食の標準歓迎 | profile・業種へ移管 | 飲食のactive全文例と業種ルーターへ移す。自然な標準句として保持 | 飲食例2件以上で歓迎と催促を判別し、ユーザー承認後に共通phrase必読を解除 |
| QB02 | limited-use: 高温度時の「心より」 | profile・業種へ移管 | 飲食profileと高温度の詳細口コミ例で条件を示す | 高温度/通常温度の対比例が承認されるまで現行境界を保持 |
| QB03 | confirmed-ng: 「お迎えできる機会」 | 保留 | ユーザー確定NGの監査証跡として保持 | ユーザーがNG全文対比例への統合を明示承認した時だけruntime必読を解除 |
| QB04 | confirmed-ng: 「お越しいただける日」 | 保留 | 同上。不自然な「日」の境界 | 同上 |
| QB05 | confirmed-ng: 「食事を楽しむ機会」 | 保留 | 同上。抽象名詞化・冗長さの境界 | 同上 |
| QB06 | confirmed-ng: 「お迎えできる日」 | 保留 | 同上。不自然な差別化表現の境界 | 同上 |
| QB07 | confirmed-ng: 受領報告だけで終える | 良好例で代替 | 高評価の完結したactive全文例とNG→改善対比へ移す | 星のみ/短文/詳細の完結例が承認され、既存case 6が回帰0 |
| QB08 | confirmed-ng: 定型謝罪3種 | 保留 | ユーザー確定NG。低評価全文例が揃っても自動削除しない | 謝罪あり/なしの複数例を個別承認し、ユーザーがruntime移行を明示承認 |
| QB09 | confirmed-good: 対象を示すお詫び3種 | 良好例で代替 | 明確・確認済みの不備を扱う低評価全文例へ移す | 謝罪対象・確認状況・強度の異なる例が承認され、case 8〜16で過剰/過少0 |
| QB10 | confirmed-ng: 「真摯」の固定・単独終止 | 良好例で代替 | 具体論点と実行可能行動を含む低評価例へ移す | 空の誠意と具体対応の対比が承認され、case 18が回帰0 |
| QB11 | confirmed-good: 「貴重なご意見」 | 良好例で代替 | L2/L3相当の全文例で自然な位置と役割を示す | 謝罪の有無が異なる2例以上を承認 |
| QB12 | limited-use: 「率直なご意見」 | 良好例で代替 | 率直さが文脈に合う例と、使わない例を対にする | case 24相当とactive例の承認後 |
| QB13 | limited-use: 追加経緯への「具体的な状況」 | profile・業種へ移管 | 通常GBPではなく個別フォロー後のE/C条件としてprofile側へ置く | case 21/22の区別が保たれ、profileに確認導線が定義された時 |
| QB14 | confirmed-ng: 「貴重なお時間」等 | 保留 | ユーザー確定NG。時間を案件固有に演出しない証跡 | ユーザーがNG対比例への移行を明示承認するまで保持 |
| QB15 | confirmed-ng: 「勇気をもって」 | 保留 | ユーザー確定NG。心理代弁を防ぐ証跡 | 同上 |
| QB16 | limited-use: 責任者・研修・改善済み等 | 安全核として維持 | K3の「未確認の改善・対応を断定しない」へ統合 | K3本文とcase 16/低評価群で架空対応0を確認後、phrase表のruntime必読だけ解除可 |
| QB17 | confirmed-good: 論点と行動が一致する4pattern | 良好例で代替 | 各patternを単独テンプレにせず、対応する低評価全文例へ移す | 異なる論点のactive例3件以上を承認し、機械反復がないこと |
| QB18 | confirmed-ng: 「ご不快な思い」等 | 保留 | ユーザー確定NG。口コミにない感情・状態補充を防ぐ | ユーザーがK1とNG対比例だけで担保可能と確認するまで保持 |
| QB19 | confirmed-ng: 余分な利用者/店側感情 | 保留 | U-R04/U-R05で削除確定した境界 | U-R04/U-R05を含むpositive例群で回帰0かつユーザーがruntime移行を承認 |

## F. EX / EV crosswalk

本表以前の`EX-*` / `EV-*`は設計上の仮名であり、正式な評価IDではない。新しい略号をそのまま増殖させず、次の3区分へ統合する。

### 1. 既存34評価へ対応（新規追加なし）

| 旧仮名群 | 正式な既存case ID | 対応内容 |
|:---|:---|:---|
| `EX-STAR5-NO-TEXT`, `EX-STAR-ONLY` | 1, 15 | 星5本文なし、星1本文なし |
| `EX-POS-SHORT`, `EX-POS`, `EX-POS-DETAILED`, `EX-COMPLETE` | 2, 3, 6 | 一言・詳細高評価、冷淡終止防止 |
| `EX-BATCH-3` | 4 | 標準歓迎の自然な反復 |
| `EX-FOOD-CLOSING`, `EX-FOOD-WELCOME`, `EX-WELCOME`, `EV-NATURAL-CLOSING` | 5, 7 | 不自然な歓迎、地域文脈のprofile許可 |
| `EX-LOW-L1〜L4`, `EX-LOW-MINOR`, `EX-LOW-CONFIRMED`, `EX-LOW-DISPUTED`, `EX-LOW-ACTION-1〜3`, `EX-LOW-GRATITUDE`, `EX-LOW-PUBLIC-READ` | 8〜16, 17〜24 | severity、謝罪、具体行動、感謝、公開上の受け止め |
| `EV-AMBIGUOUS`, `EV-AMBIGUOUS-QUANTITY` | 12 | 味・量等の主観評価を強めない |
| `EV-HIGH-RISK`, `EV-PRIVACY`, `EV-MEDICAL-PRIVACY`, `EV-INDUSTRY` | 25〜29 | 医療・士業・外国語の高リスク |
| `EX-FOREIGN` | 29 | 外国語低評価 |
| `EV-REPLIED` | 30 | 返信済みの重複返信防止 |
| `EV-KNOWLEDGE`, `EV-PROFILE-OFF`, `EV-REGIONAL-OFF`, `EV-CTA` | 7, 31 | 地域文脈とknowledge販促漏入 |
| `EV-CANDIDATE-NOT-APPROVED`, `EV-SOURCE-LEVEL` | 32 | 外部/Excel候補の自動approved化防止 |
| `EV-A36-NONMODEL` | 33 | A36を現役模倣元にしない |
| `EX-STATE-ROUTER`, `EV-STATE-A35` | 34 | phrase/full-example状態の選択。A35の最終状態は別途統括・ユーザー確認 |
| `EV-FACT`, `EV-FACT/INTENSITY/STAR-ONLY`, `EV-OUTPUT-ONLY` | 1〜34の共通assertion / suite gate | 全生成出力の事実忠実性・強度・最終文のみを横断検査 |

### 2. 新規評価が必要な差分（正式追加は別承認）

新規は次の6件を上限候補とする。既存34件との重複確認後、評価設計担当とユーザーの別承認を経るまで`evals.json`へ追加しない。目安12〜14件以下という上限をさらに下回る。

| 仮ID | 統合する旧仮名 | 新規で必要な理由 |
|:---|:---|:---|
| N01 | `EX-ROUTER` | 該当カテゴリだけを選び、active例の参照が最大3件であることは既存34件にない |
| N02 | `EX-MIXED` | 良い点と軽い不満が混在する入力の焦点選択が既存34件にない |
| N03 | `EV-REVISION-REGRESSION` | 修正指示後に元口コミから全文再構成する動作が既存34件にない |
| N04 | `EV-RETALIATION` | 口コミ削除・星変更・見返り要求を明示的に拒む生成ケースが既存34件にない |
| N05 | `EX-MEDICAL-POS` | 肯定的な医療口コミで診療関係・効果を反復しないケースが既存の低評価高リスク群にない |
| N06 | `EV-PROMOTION-SCOPE`, `EV-PROFILE-SCOPE`, `EV-LOG-STATE` | E/C/I/U昇格、client混入、採用状態捏造を一つの状態管理ケースで検査する |

`EV-POLICY-CURRENT`と`EV-TIMING`は文章生成の新規ケースにしない。公式情報の現在性監査または別運用課題として扱う。

### 3. 例の承認で担保（評価IDを増やさない）

| 旧仮名 | 扱い |
|:---|:---|
| `EX-VOICE-WARM`, `EX-VOICE-DRY` | profile別active例の承認で担保。共通評価を増やさない |
| `EX-FOOD-POS` | 既存case 2/3と飲食active例の承認で担保 |
| `EX-LOW-*`の文章バリエーション | 既存case 8〜24へ同じ正解文を固定せず、複数active例の適用条件で担保 |
| `changelog append-only check` | skill-checkerの静的確認で担保 |
| `EV-SOURCE/CRITICAL` | K1〜K6のsuite gateとsource台帳の静的QAで担保 |

## まとめ

分類結果（行単位の移行項目）:

| 分類 | 件数 |
|:---|---:|
| 安全核として維持 | 25 |
| profile・業種へ移管 | 11 |
| 良好例で代替 | 19 |
| 重複撤廃 | 8 |
| 保留 | 17 |
| 合計 | 80 |

設計上の要点:

1. K1〜K6は候補版でも削除しない。
2. 文数、締め、店側感情、謝罪の細かな言い回し、重複回避は、共通ハード禁止からprofile・業種・良好全文例へ移す。
3. `SKILL.md`、`reply-rules.md`、`evidence.md`、自己チェックに重複する検査はK1〜K6へ圧縮する。
4. ユーザー確定NG語はQBごとの個別表に従い、勝手に削除しない。良好例へ移す項目も原台帳の証跡は保持する。
5. `approved-replies.md` の履歴本文とchangelogは保持するが、通常runtimeから参照しない。
6. A35は設計上`active-conditional`を推奨するが、本番変更前に統括・ユーザー確認が必要である。
7. 具体例を増やすだけでは不十分で、入力カテゴリからactive例を最大2〜3件だけ選ぶ軽量ルーターが必要である。
8. 新規評価候補はN01〜N06の6件に抑え、正式追加は評価設計担当とユーザーの別承認後に行う。
9. phrase-level 7状態は承認ガバナンスとして例レジストリに残し、通常生成runtimeからだけ外す。状態遷移と無断昇格防止は撤廃しない。
