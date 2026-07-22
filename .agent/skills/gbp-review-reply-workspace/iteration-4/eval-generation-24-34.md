# iteration-4 評価生成記録（ID24〜34）

## 今回補完した残欠

- ID33 `a36-not-active-model`: `with_skill/timing.json` を計測不能形式で追加
- ID34 `phrase-state-correct-selection`: snapshot4を適用した `old_skill/outputs/response.md` と、iteration-4 candidateを適用した `with_skill/outputs/response.md` を新規生成
- ID34: old/with両方の `timing.json` を計測不能形式で追加
- gradingは作成していない

ID34は、案内不足と長い待ちへの直接謝罪、案内方法と待ち時間の確認・見直し、confirmed-goodの「貴重なご意見」で完結させた。confirmed-ngの「貴重なお時間を割いて」「勇気をもって」と、追加経緯がない場合のlimited-use「具体的な状況をお知らせくださり」は使用していない。

## ID24〜33の既存ファイル監査

下表は、iteration-3と4のmetadata SHA-256、iteration-4 oldとiteration-3 with、iteration-4 withとoldのファイルSHA-256を比較した事実だけを記す。「一致」は内容が同一であることを示すだけで、生成手段は推測しない。

| ID | ケース | metadata v3/v4 | old response / v3 with | old timing / v3 with | with response / old | with timing / old |
|---:|---|---|---|---|---|---|
| 24 | allow-candid-opinion-contextually | 一致 | 不一致 | 不一致 | 一致 | 一致 |
| 25 | clinic-fee-explanation-high-risk | 不一致 | 一致 | 不一致 | 不一致 | 不一致 |
| 26 | clinic-sensitive-treatment-review | 不一致 | 一致 | 不一致 | 不一致 | 不一致 |
| 27 | professional-service-fee-contract-risk | 一致 | 不一致 | 不一致 | 不一致 | 不一致 |
| 28 | professional-service-case-outcome-risk | 一致 | 不一致 | 不一致 | 不一致 | 一致 |
| 29 | foreign-language-low-rating | 一致 | 不一致 | 不一致 | 一致 | 一致 |
| 30 | already-replied-skip-duplicate | 一致 | 不一致 | 不一致 | 一致 | 一致 |
| 31 | knowledge-promotion-leak-blocked | 一致 | 不一致 | 不一致 | 不一致 | 一致 |
| 32 | workbook-candidates-not-auto-approved | 不一致 | 不一致 | 不一致 | 不一致 | 不一致 |
| 33 | a36-not-active-model | 一致 | 不一致 | 不一致 | 不一致 | 不一致 |

ID24〜33には「metadata一致かつold response/timingの双方がiteration-3 withと一致」のケースはない。したがって、iteration-3からの完全な機械再利用をファイル一式から確認できるケースは0件。ID25・26はresponseのみ一致するがmetadataとtimingが一致しないため、完全再利用とは記録しない。

## manifest全件検証

- manifest: 34ケース
- 検証組数: 68（34ケース×old/with）
- `outputs/response.md` 欠落: 0
- `timing.json` 欠落: 0
- timing JSON解析・必須 `measurement_status` エラー: 0
- timing数値は計測できないものについて `null` とし、計測値を捏造していない
