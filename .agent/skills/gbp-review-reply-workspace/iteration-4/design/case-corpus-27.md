# iteration-4 事例コーパス設計台帳（27ケース）

## 1. 目的と状態

禁止語の網羅ではなく、入力条件に合う良好全文例を少数参照できるようにするための設計台帳である。ユーザーの明示承認前は `approved` や `confirmed-good` へ昇格しない。現在は新規4件がユーザー明示承認済みである。

状態の意味:

- `confirmed-existing`: ユーザー確認済みの既存全文例。本文は既存ファイルを正本とする。
- `confirmed-good`: iteration-4で作成し、ユーザーが明示承認した新規の良好全文例。
- `candidate-rewrite`: 今後ゼロから安全な全文案を作り、ユーザー判断を受ける未確認候補。

ケース状態と資料の扱いは別軸で管理する。外部記事の元返信を `eval-only-source` とする場合でも、同じ入力シナリオからゼロから作る安全な全文例は `candidate-rewrite` を経て、ユーザー明示承認後にだけ `confirmed-good` となる。外部元返信を模倣・転載したり、候補を無断で昇格したりしない。

カテゴリ別の将来格納先は提案であり、iteration-4ではまだ作成しない。

| カテゴリ | 将来の格納先（案） | 主なrouterキー |
|:---|:---|:---|
| `star-only` | `examples/cases/star-only.md` | `text=none`, `rating-band`, `risk` |
| `positive-short` | `examples/cases/positive-short.md` | `text=short`, `sentiment=positive`, `facts-count` |
| `positive-detailed` | `examples/cases/positive-detailed.md` | `text=detailed`, `sentiment=positive`, `industry` |
| `mixed-low-rating` | `examples/cases/mixed-low-rating.md` | `sentiment=mixed-or-negative`, `issue`, `verified-action` |
| `high-risk-special` | `examples/cases/high-risk-special.md` | `risk`, `privacy`, `disputed`, `language`, `reply-state` |

## 2. 既存確認済み3件

| ID | カテゴリ | 入力で確認できる事実・リスク | 期待する返信機能 | 禁止事項 | 状態・根拠 | 将来格納先 / routerキー |
|:---|:---|:---|:---|:---|:---|:---|
| C01-A35 | `positive-detailed` | 飲食。おいしさ、落ち着いた雰囲気、ゆっくり食事できたこと、丁寧な接客が明記。通常リスク | 主要点を最大2テーマへ絞った感謝と、profileに合う自然な歓迎で完結 | 全要素の列挙、客の内心補足、店側感情の水増し | `confirmed-existing`。client record 35、ユーザー修正確定、posted確認済み。本文正本は `good-output.md` | `positive-detailed.md` / `text=detailed; rating=high; industry=food; facts=multi; risk=normal` |
| C02-UR04 | `positive-short` | 飲食。落ち着いた雰囲気と丁寧なスタッフ対応が明記。通常リスク | 2つの具体点への感謝と、標準的な歓迎締め | 「気持ちよく過ごせた」「良い印象」「私どもも嬉しい」等の補足 | `confirmed-existing`。2026-07-19会話でユーザー確定、未投稿の品質例。本文正本は `good-output.md` | `positive-short.md` / `text=short; rating=high; industry=food; facts=ambience+service; risk=normal` |
| C03-UR05 | `positive-short` | 飲食。料理と接客が良かったと明記。通常リスク | 2点への感謝、profileで認めた店づくり姿勢、自然な歓迎 | 客の満足感や店側の喜びを新しく作ること、販促情報の追加 | `confirmed-existing`。2026-07-19会話でユーザー確定、未投稿の品質例。本文正本は `good-output.md` | `positive-short.md` / `text=short; rating=high; industry=food; facts=food+service; risk=normal` |

## 3. WEBRIES記事由来17シナリオ

参照元: WEBRIES「Google口コミ返信の例文集｜高評価・低評価の返し方」<https://webries.co.jp/meo/review-reply>。記事本文はコピーせず、入力状況だけを匿名・要約して使う。記事の返信文はそのまま良好例にしない。

### 3-1. 入力シナリオだけを使い、ゼロから作る9件（承認済み3・候補6）

この9件も外部記事の元返信は参照・模倣しない。匿名化・要約した入力状況だけを使い、安全な全文例をゼロから設計する。

| ID | カテゴリ | 入力で確認できる事実・リスク | 期待する返信機能 | 禁止事項 | 状態・根拠 | 将来格納先 / routerキー |
|:---|:---|:---|:---|:---|:---|:---|
| W01-HF | `positive-detailed` | 飲食。パスタ、店内の雰囲気、再訪意思が肯定的に明記 | 料理と雰囲気への具体的な感謝。相手自身の再訪意思を受けた自然な歓迎 | 未記載の季節メニュー、シェフの感情、追加注文の誘導 | `confirmed-good`。2026-07-21ユーザー明示承認 | `positive-detailed.md` / `text=detailed; rating=high; industry=food; facts=food+ambience+revisit` |
| W02-HB | `positive-detailed` | 美容。希望に合う仕上がりと丁寧なカウンセリングが明記 | 仕上がりとカウンセリングへの感謝。profileに沿う今後の姿勢 | 担当者の内心、次回施術の販売、未確認の提案方針 | `confirmed-good`。2026-07-21ユーザー修正確定 | `positive-detailed.md` / `text=detailed; rating=high; industry=beauty; facts=result+counseling` |
| W03-HS | `positive-detailed` | 飲食。スタッフ対応、料理、友人との時間が肯定的に明記 | 接客と料理を中心に受け、歓迎で完結 | 「大切な時間」への脚色、コース利用の勧誘、スタッフ感情の代弁 | `confirmed-good`。2026-07-21ユーザー明示承認 | `positive-detailed.md` / `text=detailed; rating=high; industry=food; facts=service+food+companion` |
| W04-LW | `mixed-low-rating` | 予約済みだが30分以上待った、再訪否定が明記。原因・改善状況は未確認 | 待ち時間を具体的に受け止め、必要な謝意・お詫び、確認可能な対応だけを示す | 予約枠見直し済み等の架空改善、再来店の要求、原因推測 | `candidate-rewrite`。記事低評価・待ち時間シナリオ | `mixed-low-rating.md` / `sentiment=negative; issue=wait; reservation=yes; action=unverified` |
| W05-LA | `mixed-low-rating` | スタッフ対応が冷たく不快だったとの評価。事実関係・担当者は未確認 | 指摘を軽視せず受け止め、確認・共有等は実行可能性に応じて述べる | 相手の感情をさらに物語化、全員共有の断定、謝罪語の機械挿入 | `candidate-rewrite`。記事低評価・接客態度シナリオ | `mixed-low-rating.md` / `sentiment=negative; issue=staff-attitude; action=unverified` |
| W06-LB | `mixed-low-rating` | 美容。仕上がりが希望と異なり、カウンセリング不足との投稿者評価 | 結果と指摘を受け止め、profileで確認済みの場合だけ非公開の相談手段を示す | 店側の過失確定、無条件のお直し約束、電話・来店の勝手な指定 | `candidate-rewrite`。記事低評価・美容品質シナリオ | `mixed-low-rating.md` / `sentiment=negative; industry=beauty; issue=result+counseling; remedy=profile-gated` |
| W07-LF | `mixed-low-rating` | 飲食。味が薄い、量が少ない、価格に見合わないという主観評価 | 味・量・価格の論点をまとめて受け、意見への感謝と確認姿勢を示す | 味や量の欠陥認定、調理スタッフ共有の断定、再訪営業 | `candidate-rewrite`。記事低評価・料理品質シナリオ | `mixed-low-rating.md` / `sentiment=negative; industry=food; issue=taste+quantity+value` |
| W08-LP | `mixed-low-rating` | 価格が高く、他店より価値が低いとの比較評価。原価・食材情報なし | 価値を感じられなかったという評価を受け、反論せず意見に感謝 | 未提示の食材こだわり、価格の正当化、競合への反論 | `candidate-rewrite`。記事低評価・価格シナリオ | `mixed-low-rating.md` / `sentiment=negative; issue=price-value; comparison=yes; evidence=none` |
| W09-LH | `mixed-low-rating` | 飲食。トイレの汚れと衛生不安が明記。現地確認・改善状況は不明 | 衛生上の指摘を重大に扱い、確認対象と実行可能な次の対応を示す | 清掃不備の事実確定、即時改善済みの捏造、再来店誘導 | `candidate-rewrite`。記事低評価・衛生シナリオ | `mixed-low-rating.md` / `sentiment=negative; issue=hygiene; safety=yes; action=unverified` |

### 3-2. 安全な全文例8件（承認済み5・候補3、外部元返信は評価専用）

| ID | カテゴリ | 入力で確認できる事実・リスク | 期待する返信機能 | 禁止事項 | ケース状態 | 外部元返信の扱い・根拠 | 将来格納先 / routerキー |
|:---|:---|:---|:---|:---|:---|:---|:---|
| W10-HD | `high-risk-special` | 歯科。説明が丁寧、安心、痛みが少なかったという治療関連の評価 | 公開範囲を絞った感謝。治療内容・結果を事業者側から確認しない | 痛みの少ない治療という効果訴求、診療方針の広告化、受診関係の拡張 | `confirmed-good`。2026-07-21ユーザー修正確定 | `eval-only-source`。記事の歯科返信は医療情報と効果表現の回帰検査だけに使用 | `high-risk-special.md` / `rating=high; industry=medical; privacy=clinical; effect-claim=yes` |
| W11-HO | `high-risk-special` | 整骨院。長年の肩こりが一度で軽くなり継続意思があるとの自己申告 | 投稿者の評価への一般的な感謝に限定し、効果を追認しない | 改善効果の確認、施術プランの提案、継続通院の誘導 | `confirmed-good`。2026-07-21ユーザー修正確定 | `eval-only-source`。記事の施術効果返信は効果保証と販促の回帰検査だけに使用 | `high-risk-special.md` / `rating=high; industry=healthcare; effect-claim=strong; revisit=yes` |
| W12-HC | `high-risk-special` | クリニック。受付・看護師が親切、初診でも安心したとの評価 | 公開可能なスタッフ対応への感謝だけを安全に扱う | 受診事実・身体状況の拡張、いつでも来院の勧誘、院内方針の補充 | `confirmed-good`。2026-07-21ユーザー修正確定 | `eval-only-source`。記事のクリニック返信は診療関係とCTAの回帰検査だけに使用 | `high-risk-special.md` / `rating=high; industry=medical; privacy=visit; facts=staff-response` |
| W13-SH | `star-only` | 星4〜5、本文なし。体験・来店・満足の事実は不明 | 高評価への十分な感謝と、profileで許容される自然な締め | 感想の追記依頼、サービス向上材料という利用目的、具体的体験の補充 | `confirmed-good`。2026-07-21ユーザー明示承認 | `eval-only-source`。記事の汎用高評価返信はコメント要求の回帰検査だけに使用 | `star-only.md` / `text=none; rating=high; industry=general; facts=rating-only` |
| W14-SF | `star-only` | 飲食の星4〜5、本文なし。利用・注文メニューは確認不能 | 評価への感謝と、飲食profileに合う歓迎で完結 | お気に召したとの推測、お気に入りメニューの質問、来店事実の断定 | `confirmed-good`。2026-07-21ユーザー明示承認 | `eval-only-source`。記事の飲食向け高評価返信は体験補充の回帰検査だけに使用 | `star-only.md` / `text=none; rating=high; industry=food; facts=rating-only` |
| W15-SC | `star-only` | クリニックの星4〜5、本文なし。受診・診療内容は確認不能 | 高評価への感謝。医療profileと公開安全を優先 | 来院・診療の断定、満足の推測、相談・受診の誘導 | `candidate-rewrite`。安全な全文例をゼロから作る | `eval-only-source`。記事の医療向け高評価返信は診療関係の補充検査だけに使用 | `star-only.md` / `text=none; rating=high; industry=medical; privacy=unknown` |
| W16-SL | `star-only` | 星1〜2、本文なし。不満原因は不明 | 評価を受け止め、必要ならprofileで確認済みの非公開窓口だけを簡潔に示す | 不満があったとの確定、謝罪の自動挿入、意見投稿や電話の催促 | `candidate-rewrite`。安全な全文例をゼロから作る | `eval-only-source`。記事の汎用低評価返信は原因推測と連絡誘導の回帰検査だけに使用 | `star-only.md` / `text=none; rating=low; industry=general; issue=unknown` |
| W17-SO | `star-only` | 整骨院の星1〜2、本文なし。施術利用・期待・不満は確認不能 | 評価だけを受け止め、医療類似業種の安全境界を守る | 来院・施術・期待外れの断定、謝罪の自動挿入、改善要求や電話誘導 | `candidate-rewrite`。安全な全文例をゼロから作る | `eval-only-source`。記事の整骨院向け低評価返信は未確認体験の補充検査だけに使用 | `star-only.md` / `text=none; rating=low; industry=healthcare; privacy=unknown` |

## 4. 不足を補う7ケース

| ID | カテゴリ | 入力で確認できる事実・リスク | 期待する返信機能 | 禁止事項 | 状態・根拠 | 将来格納先 / routerキー |
|:---|:---|:---|:---|:---|:---|:---|
| G01-MX | `mixed-low-rating` | 飲食。料理は高評価だが提供の遅さに軽い不満。肯定・不満が混在 | 良い点への感謝と不満点の受け止めを両立し、片方を消さない | 高評価だけを拾う、低評価扱いで全体を重くする、未確認改善 | `candidate-rewrite`（不足補完）。記事に明示的な混合評価例がない | `mixed-low-rating.md` / `sentiment=mixed; industry=food; positive=food; issue=wait; severity=light` |
| G02-B2B | `high-risk-special` | BtoB専門サービス。説明の分かりやすさと対応を評価するが、相談・契約内容にも言及 | 公開可能な一般的評価にだけ感謝し、取引関係や内容を反復しない | 契約・案件・企業成果の確認、継続契約の誘導、顧客名の使用 | `candidate-rewrite`（不足補完）。記事に士業・BtoBの守秘ケースがない | `high-risk-special.md` / `rating=high; industry=professional-b2b; confidentiality=yes` |
| G03-FL | `high-risk-special` | 外国語の低評価。接客不満は読めるが、ニュアンスの誤読余地がある | 原文言語またはprofile指定言語で、確認できる論点だけに簡潔に応答 | 日本語への勝手な感情強化、文化的推測、機械翻訳結果の事実化 | `candidate-rewrite`（不足補完）。記事に外国語対応例がない | `high-risk-special.md` / `rating=low; language=foreign; issue=service; translation-confidence=limited` |
| G04-DP | `high-risk-special` | 低評価に事実争いがあり、店舗記録と投稿内容が一致しない可能性。公開確認未了 | 相手の受け止めを否定せず、事実認定を保留し、必要なら別途確認メモを出す | 公開反論、投稿者の虚偽認定、未確認の過失承認、削除要求 | `candidate-rewrite`（不足補完）。記事は「反論しない」までで、未確認事実の扱いが不足 | `high-risk-special.md` / `rating=low; disputed=yes; verification=pending; public-risk=high` |
| G05-MP | `high-risk-special` | 医療口コミに症状・診断・処置・経過が含まれる。評価自体は肯定的 | 公開可能な一般的な応対評価へ焦点を移し、診療情報を反復しない | 病名・処置・効果・受診関係の確認、将来結果の保証 | `candidate-rewrite`（不足補完）。記事の医療例より厳しい個人情報ケースが必要 | `high-risk-special.md` / `rating=high; industry=medical; privacy=sensitive; treatment-detail=yes` |
| G06-RP | `high-risk-special` | すでに店舗返信済みで、新しい返信作成依頼と重複している | 新規返信を作らず、返信済みであることと必要な確認だけを短く示す | 二重投稿案、既存返信の無断上書き、別文案の量産 | `candidate-rewrite`（不足補完）。記事に返信済み状態の工程例がない | `high-risk-special.md` / `reply-state=posted; action=skip-duplicate` |
| G07-KL | `positive-detailed` | 高評価口コミは料理だけ。knowledgeには地域名、重点メニュー、固定フッター、SEO語がある | 口コミに書かれた料理への感謝だけを軸に自然に完結 | knowledge由来の地域・別メニュー・販促CTA・SEOの混入 | `candidate-rewrite`（不足補完）。外部記事が推奨するキーワード・店舗方針混入への対抗例 | `positive-detailed.md` / `rating=high; industry=food; facts=food-only; knowledge-promo=blocked` |

## 5. WEBRIES業種別16フレーズの扱い

記事中の短句もそのまま登録しない。下表はシーンと機能を要約したもので、原文の転載ではない。`limited-candidate` はprofile・事実・実行可能性がそろう時だけ将来候補にできる状態、`eval-only-ng` は回帰検査専用である。

### 5-1. limited候補 9件

| ID | 業種・シーン（要約） | 状態 | 許可に必要な条件 | 主な接続ケース |
|:---|:---|:---|:---|:---|
| P01 | 飲食・調理担当が丁寧に調理する姿勢 | `limited-candidate` | profileで調理主体と表現が確認済み。口コミの料理評価に関連する | W01-HF |
| P02 | 飲食・くつろげる空間を大切にする姿勢 | `limited-candidate` | profileで方針確認済み。口コミに雰囲気評価がある | C01-A35, C02-UR04 |
| P03 | 飲食・待ち時間対策として予約運用を見直す | `limited-candidate` | 実施済みまたは実施決定を事業者が確認済み | W04-LW |
| P04 | 美容・希望を聞くカウンセリング方針 | `limited-candidate` | profileで方針確認済み。口コミにカウンセリング評価がある | W02-HB |
| P05 | 美容・仕上がり不満への手直し相談 | `limited-candidate` | 対応可否、条件、確認窓口がprofileで確認済み | W06-LB |
| P06 | 医療・説明を大切にする一般方針 | `limited-candidate` | 公開可能なprofile方針で、個別診療情報を含めない | W10-HD |
| P07 | 医療・予約管理を改善する姿勢 | `limited-candidate` | 実際の確認・改善行動が確定し、個別事情を公開しない | W04-LWの医療版 |
| P08 | 整体等・身体の状態を丁寧に聞く一般姿勢 | `limited-candidate` | profileで方針確認済み。症状や効果を反復しない | W11-HO |
| P09 | 整体等・施術内容の見直しを非公開で相談する案内 | `limited-candidate` | 相談可能性と窓口が確認済み。効果保証や責任確定を伴わない | W17-SOには本文がないため原則不使用。本文あり品質不満時のみ |

### 5-2. eval-only NG 7件

| ID | 業種・シーン（要約） | 状態 | NG理由 | 主な接続ケース |
|:---|:---|:---|:---|:---|
| N01 | 飲食・季節商品を試すよう促す | `eval-only-ng` | 口コミと無関係な販促CTAになりやすい | W01-HF |
| N02 | 美容・担当者が喜んでいると代弁する | `eval-only-ng` | 確認していないスタッフ感情を作る | W02-HB |
| N03 | 美容・別施術を次回提案する | `eval-only-ng` | 口コミ返信へアップセルを混ぜる | W02-HB |
| N04 | 医療・痛みの少ない治療を掲げる | `eval-only-ng` | 効果・優良性の訴求と個別治療の追認につながる | W10-HD |
| N05 | 医療・定期受診の予約を促す | `eval-only-ng` | 公開返信から受診を販促し、診療関係も補強する | W10-HD, W15-SC |
| N06 | 整体等・症状改善を事業者側から確認する | `eval-only-ng` | 医療類似の効果を追認・保証する | W11-HO |
| N07 | 整体等・次回のセルフケア提供を約束する | `eval-only-ng` | 未確認の次回サービスを作り、継続利用を誘導する | W11-HO |

## 6. 件数と次工程のゲート

| 区分 | 件数 |
|:---|---:|
| `confirmed-existing`: 既存の良好全文例 | 3 |
| `confirmed-good`: iteration-4新規・ユーザー明示承認または修正確定 | 8 |
| `candidate-rewrite`: WEBRIES状況由来（入力シナリオだけを要約利用し、外部元返信は非採用） | 6 |
| `candidate-rewrite`: WEBRIES状況由来（外部元返信は評価専用） | 3 |
| `candidate-rewrite`: 不足補完 | 7 |
| 未確認候補小計 | 16 |
| 合計 | 27 |

業種別短句は `limited-candidate` 9件、`eval-only-ng` 7件の計16件である。

次工程では、残る16件の `candidate-rewrite` を3〜5件ずつ全文候補化し、1件ごとにユーザーが `confirmed-good` / `confirmed-ng` / `limited-use` / `hold` を決める。W10〜W17の `eval-only-source` は外部記事の元返信だけに付く資料状態であり、ケース状態ではない。現在の27件は、既存確認済み3件、iteration-4で承認・修正確定済み8件、未確認候補16件で構成される。routerはカテゴリ決定後に最大2〜3件だけを読み、27件全件を毎回読み込まない。
