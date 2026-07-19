# iteration-3 理由タグ体系

## 1. 目的

修正理由を根本原因で追跡し、同義タグの増殖を防ぐ。1件につき0〜3タグを原則とし、症状より原因を優先する。タグは失敗理由であり、良好属性やphrase-level状態を混ぜない。

## 2. MECE分類

### 事実・根拠

| タグ | 定義 | 含む | 含まない |
|:---|:---|:---|:---|
| `semantic-inflation` | 原文の評価・感情・深刻度を強めた | 「良い」を「最高」、「満足」を「大満足」へ上げる | 新事実の追加は `unsupported-inference` |
| `unsupported-inference` | 口コミ・profile・確認済み事実にない内容を推測した | 内心、原因、満足、担当、対応済み、安心、勇気の推測 | 内部背景の公開語化は `internal-context-leak` を優先 |
| `source-conflict` | 口コミ、profile、knowledge、履歴、共通ルールの優先順位を誤った | knowledgeの販促情報を口コミより優先、古い例を現役扱い | 単なる新ブランド語は `brand-novelty` |

### 焦点・構造・日本語

| タグ | 定義 | 含む | 含まない |
|:---|:---|:---|:---|
| `focus-selection` | 主要論点を落とすか、重要度の低い点へ偏った | 混合評価の不満を落とす、詳細を全列挙する | 長さだけの問題は `length-mismatch` |
| `empty-sentence` | 感謝、反応、対応、必要案内の役割がない | 最低文字数を埋める決意文、意味の重複 | 低評価の空の真摯は `empty-sincerity` |
| `construction-repetition` | 同一返信内で同じ動詞・機能を重ねた | 感謝を2回、同義の感情文を重ねる | 複数返信間は `structural-repetition` |
| `structural-repetition` | 同時バッチまたは直近finalで同一骨格を機械反復した | 全件が感謝→嬉しい→締めで中段も同形 | 標準歓迎締めだけの自然な連続使用 |
| `length-mismatch` | 口コミの情報量と返信長が不釣り合い | 星だけへの長文、重大低評価への説明過多 | 必要な2文を短いだけで不合格にしない |
| `unnatural-variation` | 差別化だけを目的に不自然な言い換えをした | 「お迎えできる機会」「お越しいただける日」 | 自然な語彙差、profile固有voice |

### 関係性・締め

| タグ | 定義 | 含む | 含まない |
|:---|:---|:---|:---|
| `cta-pressure` | 投稿者へ販促、約束化、用途・同行者指定を加えた | 次回商品、予約、割引、「宣言どおり」、家族指定 | 一般的な接客上の歓迎締め |
| `brand-novelty` | 口コミと無関係なブランド・販促表現を足した | 店のこだわり、SEO、重点商品、地域訴求 | sourceの優先誤りが主因なら `source-conflict` |
| `closing-mismatch` | 締めの機能、業種、評価帯、温度が不適切 | 高評価の冷淡終止、低評価への歓迎、高リスクでの再相談、未許可地域締め | 感謝対象の誤りは `gratitude-mismatch` |
| `gratitude-mismatch` | 感謝がない、浅い、対象がずれた、情報受領中心になった | 低評価で感謝なし、通常締めの「具体的な状況を…」、定型受領だけ | 時間・勇気の背景漏入は `internal-context-leak` を優先 |

### 低評価の責任対応

| タグ | 定義 | 含む | 含まない |
|:---|:---|:---|:---|
| `apology-mismatch` | 謝罪の直接性または強度が事実・severityに合わない | 明確な不備で「申し訳なく思う」、重大不備への軽い謝罪、L4で過失を認めすぎる | 謝罪後の行動不足は `action-vagueness` |
| `empty-sincerity` | 「真摯に受け止める」等の誠意語が対象・行動なしで終わる | 真摯のみ、重く受け止めるのみ | 一般の役割なし文は `empty-sentence` |
| `action-vagueness` | 確認・改善の対象または行動が不明、あるいは実行可能性がない | 「改善に活かす」「努める」だけ、未確認の責任者・研修 | 公開全体の安心不足だけなら `public-reassurance-gap` |
| `public-reassurance-gap` | 個別要素を直しても、第三者に軽視・反論・責任回避・実行不能に見える | 論点を矮小化、自己弁護中心、何を直すか全体として伝わらない | 単独の曖昧行動は `action-vagueness` を優先 |

### 安全・voice・工程

| タグ | 定義 | 含む | 含まない |
|:---|:---|:---|:---|
| `privacy-risk` | 個人情報、診療、相談、契約関係を公開上拡張した | 投稿者が書いた診療内容の事業者側確認、案件関係の追認 | 規約・効果保証のみは `policy-risk` |
| `policy-risk` | 規約、法規、効果保証、評価操作等のリスク | 星変更・削除・見返り要求、効果保証 | 個人情報拡張は `privacy-risk` |
| `voice-mismatch` | 敬語、語彙、記号、文数、温度がprofileと不一致 | client NG表現、過剰な感嘆符、業態不自然語 | 共通日本語の不自然さは `unnatural-variation` |
| `internal-context-leak` | 内部で持つ背景理解を公開文へ直書きした | 「貴重なお時間を割いて」「勇気をもって」「心苦しい中」 | 口コミ主の内心を別途推測した場合は `unsupported-inference` も検討 |
| `patch-regression` | 局所修正で別箇所を悪化・再発させた | 指摘語だけ直し、事実逸脱や締め不整合を残す | 初稿の単独エラー |

上記の明示リストは合計22タグである。指示書内の要約数とは1件ずれるため、数を合わせる目的でタグを削除・統合せず、ユーザーが列挙した22語を正本とする。

## 3. Excel側タグの統合

| Excel側のタグ・属性 | 統合先 | 判断条件 |
|:---|:---|:---|
| `apology-underweight` | `apology-mismatch` | 謝罪の直接性・強度不足 |
| `severity-mismatch` | `apology-mismatch` | severityに対し強すぎる場合も同じタグ |
| `accountability-gap` | `action-vagueness` | 対象・行動・実行主体が曖昧 |
| `accountability-gap` | `public-reassurance-gap` | 個別行動はあるが、公開全体で責任回避に見える場合 |
| `public-trust-gap` / `public-reassurance` | `public-reassurance-gap` | 自己宣伝でなく対応内容の不足を記録 |
| `gratitude-gap` | `gratitude-mismatch` | 感謝欠落 |
| `generic-gratitude` | `gratitude-mismatch` | 文脈と感謝対象のずれ |
| `relevance-gap` | `gratitude-mismatch` | 意見より一般的投稿行為だけへ感謝 |
| `information-centric` | `gratitude-mismatch` | 情報受領が前面に出る通常GBP締め |
| `gratitude-temperature` | `gratitude-mismatch` | 感謝の温度不足・過剰 |
| `respectful-gratitude` | good属性 | 失敗タグへ入れない |
| `natural-closing` / `warm-closing` | good属性 | 失敗タグへ入れない |
| `acceptable` / `wording-choice` | good属性または注記 | 失敗タグへ入れない |
| `emotional-overreach` | `unsupported-inference` | 投稿者の心理・感情を推測した場合 |
| `emotional-overreach` | `internal-context-leak` | 内部理解を「勇気」等で公開した場合 |
| `verbose-closing` | `unnatural-variation` | バリエーション目的の冗長な締め |
| `brand-mismatch` | `voice-mismatch` | client/業態voiceとの不一致 |
| `brand-mismatch` | `brand-novelty` | 口コミと無関係なブランド演出追加 |
| `rule-induced-error` | 根本原因タグ | `unnatural-variation` 等を記録し、原因欄に旧ルール誘発と書く |
| `frequency-overfit` | `structural-repetition` または `unnatural-variation` | 強制類語化による結果で分類する |
| `purpose-clarification` | `public-reassurance-gap` | 失敗原因が第三者向け対応目的の欠落の場合 |

## 4. 選択順序

1. criticalに関わる `privacy-risk`、`policy-risk`、`unsupported-inference`、`semantic-inflation` を先に確認する。
2. 低評価では `apology-mismatch`、`empty-sincerity`、`action-vagueness` を確認する。
3. 公開文全体に残る不安が個別タグで説明できない場合だけ `public-reassurance-gap` を付ける。
4. 感謝と締めは `gratitude-mismatch` と `closing-mismatch` を分ける。
5. 同一返信内は `construction-repetition`、複数返信間は `structural-repetition` を使う。
6. 内部背景の直書きは `internal-context-leak`、独立した内心推測は `unsupported-inference` を使う。
7. 最大3タグに収め、同じ症状を複数タグで重複記録しない。

## 5. 境界例

| 事象 | 主タグ | 必要時の副タグ | 説明 |
|:---|:---|:---|:---|
| 「良かった」を「最高の体験」へ変換 | `semantic-inflation` | なし | 強度上昇が根本原因 |
| 星だけへ利用メニューを追加 | `unsupported-inference` | `source-conflict` | knowledgeを誤参照した場合だけ副タグ |
| 「お時間を割いて」を返信へ追加 | `internal-context-leak` | `gratitude-mismatch` | 内部の背景説明を公開したことが主因 |
| 明確な長時間待ちへ「申し訳なく思う」 | `apology-mismatch` | なし | 直接性とseverityの不一致 |
| 「真摯に受け止めます」で終了 | `empty-sincerity` | `action-vagueness` | 対象も行動もない場合に副タグを検討 |
| 「改善に活かします」 | `action-vagueness` | `public-reassurance-gap` | 全文でも責任回避に見える場合だけ副タグ |
| 通常低評価を「具体的な状況を…」で締める | `gratitude-mismatch` | なし | 情報受領中心。個別追加説明時はエラーではない |
| 高評価3件で標準歓迎締めだけが同じ | タグなし | なし | 自然な定型句の連続は許容 |
| 高評価3件で全文骨格・中段・感情も同じ | `structural-repetition` | なし | 締めの同一ではなく全体構造が問題 |
| 「お迎えできる機会」を差別化目的で使用 | `unnatural-variation` | `closing-mismatch` | 不自然な言い換えを主因とする |
| 京都駅付き締めを未許可profileで使用 | `closing-mismatch` | `cta-pressure` | regional CTAの催促性も出た場合だけ副タグ |

## 6. 状態とタグを混同しない

### 返信記録状態

```text
draft / rejected / final_approved / posted
```

### phrase-level境界状態

```text
confirmed-good
confirmed-ng
limited-use
candidate
historical
superseded-intermediate
pending-user-selection
```

### 適用範囲

```text
E / C / I / U
```

上記3軸は別々に記録する。例えばA36は返信記録状態が `posted` でも、phrase/full-exampleの現行参照状態は `historical` になり得る。H12 Afterは通常締めとして `superseded-intermediate` だが、追加経緯を個別提供された場面では同じphraseを `limited-use` として別条件で参照できる。

## 7. 新設・変更ゲート

- 既存22タグで説明できない時だけ、新タグ候補を出す。
- 新タグは定義、含む例、含まない例、既存タグとの差、E/C/I/Uの再現性を示す。
- 単一クライアントの1〜5件、採用率低下、Excel内の語彙だけでUタグを増やさない。
- Uへの定着は、複数業種の旧版比較、critical 0、回帰0、独立QAを必要とする。
- `respectful-gratitude` 等の良好属性は、失敗タグ台帳ではなくquality boundaryへ記録する。
