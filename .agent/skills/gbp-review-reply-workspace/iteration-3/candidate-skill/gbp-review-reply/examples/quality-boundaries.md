# 品質境界台帳 — iteration-3 candidate

このファイルはphrase-levelの品質境界を、承認済み全文台帳から分離して管理するiteration-3候補である。Excel候補30件のうち2026-07-19にユーザーが選定した6件は全文を [good-output.md](good-output.md) に置き、本ファイルでは選定状態と境界だけを管理する。残り24件の未選定全文は収録しない。

## 状態

- `confirmed-good`: 条件内で使用できることをユーザー指示で確認
- `confirmed-ng`: 指定条件では使用しないことを確認
- `limited-use`: 限定文脈と確認条件でのみ使用可
- `candidate`: 評価・選定前
- `historical`: 履歴であり現役模倣元ではない
- `superseded-intermediate`: 後の判断で置換された中間案
- `pending-user-selection`: ユーザー選択まで現役化しない

全文例では次の状態も使う。

- `active`: 現行ルールで再審査済み。記載条件内で品質境界として参照できる。
- `active-conditional`: 事実確認、実行主体、業種、深刻度、profile等の記載条件を全て満たす時だけ参照できる。

## phrase-level境界

| ID | 状態 | phrase / 機能 | 使用条件 | 理由 | scope | 確認日・根拠 | Before → After |
|:---|:---|:---|:---|:---|:---:|:---|:---|
| QB01 | confirmed-good | またのご来店をお待ちしております。 | 飲食の肯定的な口コミで自然な歓迎が適切 | 明確で接客上自然。頻度だけで言い換えない | I | 2026-07-19 user instruction / Excel NG良好事例 | 機会・日を待つ締め → 標準来店締め |
| QB02 | limited-use | またのご来店を心よりお待ちしております。 | 温度の高い詳細な高評価 | 「心より」は歓迎温度を上げるため全件使用しない | I | 2026-07-19 user instruction / Excel H03 | 標準締め → 高温度時だけ心より |
| QB03 | confirmed-ng | またお迎えできる機会を、心よりお待ちしております。 | 使用しない | 抽象名詞化した作文調 | I | 2026-07-19 user instruction / Excel H01 | 同左 → QB01 |
| QB04 | confirmed-ng | またお越しいただける日を、心よりお待ちしております。 | 使用しない | 表現差のための不自然な「日」 | I | 2026-07-19 user instruction / Excel H02 | 同左 → QB01 |
| QB05 | confirmed-ng | またお食事を楽しんでいただける機会を、心よりお待ちしております。 | 使用しない | 冗長で接客会話から離れる | I | 2026-07-19 user instruction / Excel NG良好事例 | 同左 → QB01 |
| QB06 | confirmed-ng | またお迎えできる日を、心よりお待ちしております。 | 使用しない | 表現差のための不自然な「日」 | I | 2026-07-19 user instruction / Excel H04 | 同左 → QB01 |
| QB07 | confirmed-ng | 拝見しました。／確認しました。／触れてくださいました。／ありがたく拝見しました。で終える | 肯定的な返信の最終機能にしない | 受領報告だけで冷淡に終わる | U | 2026-07-19 user instruction / Excel H05-H06 | 受領終止 → 感謝・反応・姿勢・歓迎へ接続 |
| QB08 | confirmed-ng | 申し訳なく思っております。 | 確認済みの明確な不備への謝罪に使わない | 話者の内心説明で直接謝罪を弱める | U | 2026-07-19 user instruction / Excel H07 | 間接謝罪 → severityに合う直接謝罪 |
| QB09 | confirmed-good | 申し訳ございません。／誠に申し訳ございませんでした。／心よりお詫び申し上げます。 | 確認済み事実とL1〜L3の深刻度に合わせる | 直接謝罪。強度と事実認定を混同しない | U | 2026-07-19 user instruction / Excel NG良好事例 | 間接謝罪 → 条件付き直接謝罪 |
| QB10 | confirmed-ng | 真摯に受け止めております。だけで終える | 単独使用しない | 対象と行動がなく空の誠意になる | U | 2026-07-19 user instruction / Excel H11 | 真摯のみ → 見直す対象 + 確認・改善行動 |
| QB11 | confirmed-good | 貴重なご意見をお寄せくださり、ありがとうございました。 | L2〜L3等、改善につながる低評価・要望の標準候補 | 意見そのものへ敬意と感謝を返す | U | 2026-07-19 user instruction / Excel H16 | 情報受領中心 → 意見への感謝 |
| QB12 | limited-use | 率直なご意見をお寄せくださり、ありがとうございました。 | 率直な指摘で文脈に合う時 | 全件標準にはせず温度を合わせる | U | 2026-07-19 user instruction / Excel H14 | 一般感謝 → 率直さが明記された時だけ |
| QB13 | limited-use | 具体的な状況をお知らせくださり、ありがとうございました。 | 個別確認で追加経緯を提供してもらった時 | 通常GBPでは情報受領中心に聞こえる | E/C | 2026-07-19 user instruction / Excel H12-H16 | 通常締めの中間案 → 追加経緯時だけ |
| QB14 | confirmed-ng | 貴重なお時間を割いて／大切なお時間を使って | 公開返信に使わない | 全口コミ共通の時間を案件固有に演出する | U | 2026-07-19 user instruction / Excel H12 | 時間への感謝 → 意見への感謝 |
| QB15 | confirmed-ng | 勇気をもってご指摘くださり | 公開返信に使わない | 投稿者の心理を代弁する | U | 2026-07-19 user instruction / Excel H14 | 心理の物語化 → 確認できる指摘への感謝 |
| QB16 | limited-use | 責任者・共有先・窓口・研修・点検・改善済み事実 | 実在と実行意向を確認できた時だけ | 架空の責任・対応を防ぐ | U/I/C | 2026-07-19 user instruction / Excel 低評価設計 | 固定挿入 → 確認済み材料だけ |

## Excel候補30件の全文選定境界

| ID | 状態 | 代表境界 | 必須確認 | 全文・詳細 |
|:---|:---|:---|:---|:---|
| R03 | active | 詳細高評価・温度高め | 口コミの具体点、profileの感情表現と「心より」許可 | [good-output.md](good-output.md) |
| C01 | active-conditional | 医療等の星5本文なし・privacy-first | 来院・治療・通院を追認しない。profileが一般姿勢の第二文を許可 | [good-output.md](good-output.md) |
| R08 | active-conditional | 飲食L3・重大オペレーション | 口コミ記載事実、共有先、見直し行動と実行意向 | [good-output.md](good-output.md) |
| R10 | active-conditional | 改善済み事実 | 全席禁煙の現状、範囲、変更時期 | [good-output.md](good-output.md) |
| C07 | active-conditional | 医療L2・待ち時間 | 待ち時間と説明不足、予約運用・説明方法の確認行動 | [good-output.md](good-output.md) |
| P08 | active-conditional | 士業L4・守秘 | 実在窓口、実行主体、経緯確認・対応意向 | [good-output.md](good-output.md) |

選定理由は、2系統選定の共通評価を軸に、条件付き例を業種と深刻度の代表として採用したため。選定6件は投稿済みを意味しない。残り24件は `candidate` / `pending-user-selection` の監査履歴を保持し、全文を現役例へ昇格しない。

## 履歴境界

- H12の「具体的な状況をお知らせくださり」を通常GBP締めにする案は `superseded-intermediate`。
- 同じphraseでも、個別確認で追加経緯を受けた時はQB13の `limited-use` として別条件で扱う。
- A36は全文の投稿済み履歴であり、本台帳へphrase承認として移さない。
- Excel候補30件は選定前に全件 `candidate` かつ `pending-user-selection` だった。この監査履歴は改変しない。
- 2026-07-19のユーザー方針により6件を現役模範へ昇格し、24件は非昇格のままとした。
