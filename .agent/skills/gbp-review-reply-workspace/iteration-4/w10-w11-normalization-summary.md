# W10 / W11 confirmed-good正規化

## 変更結果

- W10-HDとW11-HOを、特別な`active-conditional`ではなく通常の`confirmed-good`としてrouter参照可能にした。
- profile・privacyの4条件ゲートとW15/G05へのfallback特例を撤廃した。
- 通常の不適用条件として、口コミにない治療・利用関係の追加、および症状・効果・施術内容の反復禁止を維持した。
- W10は、口コミ本人が書いた一般語「治療」の範囲に留め、痛み・効果・具体的処置を拾わず、説明と落ち着いて受けられる環境へ焦点を絞る例として登録した。
- W11は、「かなり軽くなった」「一度の施術」「肩」を拾わず、本人が明記した継続意思と感謝・一般的歓迎へ焦点を絞る例として登録した。

## 同期したファイル

- `candidate-skill/gbp-review-reply/SKILL.md`
- `candidate-skill/gbp-review-reply/references/reply-rules.md`
- `candidate-skill/gbp-review-reply/references/feedback-loop.md`
- `candidate-skill/gbp-review-reply/references/changelog.md`
- `candidate-skill/gbp-review-reply/examples/case-index.md`
- `candidate-skill/gbp-review-reply/examples/high-risk-special.md`
- `candidate-skill/gbp-review-reply/examples/good-output.md`
- `candidate-skill/gbp-review-reply/examples/approved-replies.md`
- `pre-production-report.md`

本番、snapshot、iteration-4の評価入力・出力は変更していない。A35、G06-RP、その他の確定返信本文も変更していない。

## 本文hash検査

| 対象 | 変更前SHA-256 | 変更後SHA-256 | 結果 |
|:---|:---|:---|:---|
| W10-HD返信 | `f82d85d5df5e7372a322a2d84a542c7a1eaf93d54152aaa8113bccb86e0cec48` | `f82d85d5df5e7372a322a2d84a542c7a1eaf93d54152aaa8113bccb86e0cec48` | 一致 |
| W11-HO返信 | `498873f808df6dc33a6186fc68ddd0d6acebe40ed07b46a1e3708e2d227fee41` | `498873f808df6dc33a6186fc68ddd0d6acebe40ed07b46a1e3708e2d227fee41` | 一致 |
| 確定返信26件corpus | `dd49dbd1b879ac7bd1c56aad246e017394dea7dfc584756fea5ad70267eb3bd4` | `dd49dbd1b879ac7bd1c56aad246e017394dea7dfc584756fea5ad70267eb3bd4` | 一致 |

抽出件数は変更前後とも26件、本文差分は0件だった。

## 構造検査

- candidate内Markdownリンク切れ: 0件
- W10/W11の現役状態: `confirmed-good`で同期
- W10/W11の特別な4条件ゲート・fallback: 現役ルールから0件
- changelogの旧4条件記載: 履歴として保持し、直後の追補で`superseded`を明記
- A35の`router-eligible: false`: 維持
- G06-RPの`eval-only-workflow-control`: 維持

## QA境界

この正規化では本文不変・リンク・状態同期まで検査した。既存の34ケース、skill-checker、独立QAの数値は正規化前の実行値であり、正規化後の再実行は独立QA担当が行う。
