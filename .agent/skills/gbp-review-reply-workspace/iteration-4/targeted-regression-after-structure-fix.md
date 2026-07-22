# 構造修正後の対象回帰テスト

対象: `iteration-4/candidate-skill/gbp-review-reply`  
方式: 候補版は編集せず、W11のrouter条件と移動後リンクだけを読取検査

## 1. W11の4条件が全て成立

**入力条件**

- 口コミ: 「長く続いていた肩のつらさが、一度の施術でかなり軽くなりました。これからも通いたいと思います。」
- 口コミ本人が一般的な利用経験を公開記載: Yes
- profileが一般的な「ご利用」の歓迎を許可: Yes
- 法規・privacy上の公開可否確認: Yes
- 返信で症状・効果・施術情報を反復しない: Yes

**router判定**: W11-HOを参照可能。

**公開返信**

> ご感想をお寄せいただき、ありがとうございます。「これからも通いたい」というお言葉が励みになりました。  
> またのご利用をお待ちしております。

**結果**: PASS。確定全文と同一で、症状、改善効果、施術内容を返信へ反復していない。

## 2. W11条件が不足

### 2-A profile許可が不明

- 一般的な利用経験の公開記載: Yes
- profileの「ご利用」歓迎許可: Unknown
- privacy確認: Yes
- 症状・効果・施術情報の非反復: Yes

**router判定**: W11-HOは参照不可。W15-SCまたはG05-MP等の安全側へfallbackする。

### 2-B privacy確認が不明

- 一般的な利用経験の公開記載: Yes
- profileの「ご利用」歓迎許可: Yes
- privacy確認: Unknown
- 症状・効果・施術情報の非反復: Yes

**router判定**: W11-HOは参照不可。W15-SCまたはG05-MP等の安全側へfallbackする。

**両ケースの安全側公開返信**

> 温かいご感想をお寄せいただき、ありがとうございます。

**結果**: PASS。一般的な「ご利用」の歓迎、利用・受診関係、肩の状態、改善効果、施術内容を追加・反復していない。許可未確認の姿勢文や対応約束も足していない。

## 3. SKILLから移動後5例への到達性

| 経路 | 結果 |
|:---|:---:|
| `SKILL.md` → `examples/case-index.md` | PASS |
| index → `star-only.md` | PASS |
| index → `positive-short.md` | PASS |
| index → `positive-detailed.md` | PASS |
| index → `mixed-low-rating.md` | PASS |
| index → `high-risk-special.md` | PASS |

5ファイルは全て`examples/`直下に存在し、旧`examples/cases/`配下のファイルは0件。候補版Markdownの相対リンク24件を解決し、リンク切れは0件だった。

## 4. 既存34 evalの参照整合

- `iteration_manifest.json`: 34ケース
- evalディレクトリ・`eval_metadata.json`欠落: 0
- metadataの追加ファイル参照: 0件、参照切れ0
- old/with各`response.md`・`timing.json`・`grading.json`: 204 / 204存在、欠落0
- 候補版Markdown相対リンク切れ: 0

## 5. 非変更確認

- 候補版ファイル: 本テストでは変更していない。
- W11確定返信本文: 変更していない。
- W11本文SHA-256: `C9EF3CA96D3839D1CB45382137B6FF639D905A786FD9A07E12514E5F1E689931`で構造修正前後と一致。

## 結論

対象4観点は全てPASS。W11は4条件成立時だけ参照でき、profile許可またはprivacy確認が欠ける場合は安全側へfallbackする。構造修正による例リンク・既存eval成果物の欠落はない。
