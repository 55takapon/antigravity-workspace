# iteration-3 回帰結果

## 結論

候補版は34ケース・136 assertionsをすべて満たした。旧版の111/136（81.618%）から136/136（100%）へ改善し、critical failureは4件から0件になった。旧版で合格していたassertionの候補版での不合格は0件、16観点rubricのdimension単位の低下も0件だった。

## 厳格ゲート

| 判定 | 結果 | 根拠 |
|:---|:---:|:---|
| 候補版critical failure 0 | pass | 0件 |
| assertion回帰 0 | pass | old pass → candidate fail は0件 |
| rubric dimension低下 0 | pass | 34ケース×16観点で低下0 |
| 正式aggregateのケース別回帰 | pass | `regression_detected: false` |
| 出力崩壊なし | pass | `output_collapse_detected: false`、両configとも出力34件 |
| formal gate | allowed | `references` / `examples` / `structure` |

## 集計

| 指標 | 旧版 | 候補版 | 差分 |
|:---|---:|---:|---:|
| ケース | 34 | 34 | 0 |
| assertions合格 | 111 / 136 | 136 / 136 | +25 |
| pass率 | 81.618% | 100% | +18.382pt |
| critical failure | 4 | 0 | -4 |

旧版のcritical failureはcase 18、19、21、33。候補版では4件とも解消した。ケース別の全数値は [evals/case-index.md](evals/case-index.md) に記録する。

## 計測値の注意

この評価環境ではtoken数と所要時間を取得できず、各 `timing.json` は `measurement_status: unavailable_in_subagent_interface`、`total_tokens: null`、`total_duration_seconds: null` としている。`benchmark.json` のtoken・durationの `0.0` は集計スクリプトが欠測値へ適用したfallbackであり、実測0ではない。したがって速度・token効率の改善根拠には使用しない。

