# iteration-3 回帰結果

## 結論

36ケースの候補版は 144/144 assertions、critical failure 0件。旧版は 110/144、critical failure 12件。生成caseのassertion回帰は0件。suite-level static gateはG1=pass、G2=pass、G3=passで、総合判定はpass。

## 静的gate

- G1 lexical: pass（NG語句hit 0件）
- G2 apology matrix: pass（no-apology fail 0件、required-apology fail 0件）
- G3 runtime separation: pass

## 計測値の注意

この評価環境ではtoken数と所要時間を取得できず、各 `timing.json` は欠測としている。benchmarkの0.0は実測値ではない。
