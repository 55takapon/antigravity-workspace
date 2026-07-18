# gbp-review-reply Phase 1 実態監査

## 監査結論

- 正本は `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply` の1系統。
- `C:\Users\hangy\.codex\skills\gbp-review-reply\SKILL.md` は正本を絶対パスで指すポインタ。通常ディレクトリで、シンボリックリンクではない。
- 対象正本、対象クライアント、管理スキルのGit差分は空。対象ファイルの未コミット競合はない。
- リポジトリ全体では無関係の `scratch/survey-app/unaginokagura-resevation` が未追跡。今回変更しない。
- `gbp-review-reply-v3`、`v3-staging`、専用 `deployment`、`VERSION`、`MANIFEST` は `.agent` と `.codex\skills` の双方で見つからなかった。
- 既存workspaceは履歴資料であり、本番正本ではない。既存スナップショットは変更しない。
- 対象クライアントに `gbp-review\profile.md` と `gbp-review\log.md` は存在しない。

## Pre-flight Check

- 参照: `C:\Users\hangy\.gemini\antigravity\knowledge\chat_ng_registry\artifacts\NG_RULES.md`
- 該当: A-02、A-03、A-04、F-01、F-05、F-09、F-10、F-11
- 既存SKILL.mdの変更はユーザーが本依頼で明示承認済み。削除・移動・無関係変更は行わない。

## 正本・ポインタ・履歴コピー

| 区分 | パス | 実態 | 今回の扱い |
|:---|:---|:---|:---|
| 正本 | `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply` | 7ファイルの通常ディレクトリ | gate後の本番適用候補 |
| ポインタ | `C:\Users\hangy\.codex\skills\gbp-review-reply\SKILL.md` | 正本パスを示す1ファイル | 変更しない |
| 履歴workspace | `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply-workspace` | 旧統合時のsnapshotとcheck-report | 保持し、新iterationだけ追加 |
| Codex旧workspace | `C:\Users\hangy\.codex\skills\gbp-review-reply-workspace` | 旧snapshotとeval | 変更しない |

隠しファイル、reparse point、参照切れは対象5ルート内にない。正本・管理スキル・ポインタはUTF-8 valid、BOMなし。クライアント12ファイルもUTF-8 validで、`knowledge.md`、`posts\2026_h2_post_plan.md`、`posts\2026-05_posts.md`、`posts\2026-06_posts.md`のみBOMあり。

## 正本ファイル台帳

| ファイル | bytes | 更新日時 JST | SHA-256 |
|:---|---:|:---|:---|
| `SKILL.md` | 10731 | 2026-07-18 10:26:04 | `DD5FFBA654300E7042EB90B7766B6CE0D0A095EEB30CCA4C0FCE57A0F52E0848` |
| `references\reply-rules.md` | 23676 | 2026-07-18 10:47:50 | `EB37AB4DFC4FC9C1916365E674525F810EF32236074BD5DED7940583F40A713A` |
| `references\evidence.md` | 12723 | 2026-07-03 09:53:28 | `CB22113B9D128F9E5668F659F4815F73A2AE495AB2BA3DA405C3EBA98641A0B3` |
| `references\feedback-loop.md` | 5313 | 2026-07-03 09:52:07 | `EDB5F21B38A1FDF8D08160BC0B2F66744A5EA0E65AFBFD722CE5BC66C400342C` |
| `references\changelog.md` | 2539 | 2026-07-03 09:52:22 | `7BE78489ED295546933D759A10FF7F5865A329E18249F55157287AB7A4AF5490` |
| `examples\good-output.md` | 7657 | 2026-07-03 09:54:28 | `3BA5F7D360162C1A536C96C2C16BA3BC48D6C886D5C95F6F0B40D3D030F5A6C5` |
| `examples\approved-replies.md` | 22528 | 2026-07-03 09:53:47 | `616D17AA6ABC6D14EDBE7CC50D6938AA95151FB37A395DC3C103A92964C28F93` |

## クライアントファイル台帳

| ファイル | bytes | 更新日時 JST | SHA-256 |
|:---|---:|:---|:---|
| `knowledge.md` | 24108 | 2026-07-05 10:11:27 | `572469B478B6AF31F63982AAB834BD8FF44066F18BCAB86343686B6CBCDA60DE` |
| `menu_ja_en.md` | 12060 | 2026-06-06 08:30:51 | `343AD7CAF06C67C99832C3402CBAF7C74D801191E049C81C680131541388D96D` |
| `posts\2026-05_posts.md` | 8937 | 2026-06-04 05:08:21 | `7511BEC54E9B16AE459A927598F631385B4F0D80C80661CC3D56024F232F5589` |
| `posts\2026-06_posts.md` | 23161 | 2026-06-06 07:17:05 | `1134D6CC8B1ED34C9131837A966EA67E4753C20399FE731BB8E482D253097270` |
| `posts\2026-07_posts.md` | 27751 | 2026-07-06 14:43:26 | `6906270F85C7822F4039BF2E15DF53A265338EEA558CA47E4DFDE5D73B9E2EA7` |
| `posts\2026-08_posts.md` | 22865 | 2026-07-06 14:26:59 | `AB506F99CDD215571DBCC972BEDEB294843D9319C3B5350FE5AA00F676A2CF89` |
| `posts\2026-09_posts.md` | 22657 | 2026-07-06 14:27:01 | `147CE66BF771DDD9FB0AFD5FAB797E71481DF88D7BD9C3AF6FA501B9CBE6EB66` |
| `posts\2026-10_posts.md` | 20010 | 2026-07-06 14:27:04 | `24EBF2A666495A7BC0D4BF02E68C9F6DC0257C958F919F6083BD8801DF828BC6` |
| `posts\2026-11_posts.md` | 20321 | 2026-07-06 14:27:07 | `3730E5B3F70A1ED5E93DD2C2330B7F9590BF01BB92098C13BE4751BBFF04CBBA` |
| `posts\2026-12_posts.md` | 19783 | 2026-07-06 14:27:10 | `05BE91CCCAA9F5F95C0AF8BD7EAF8C0E5E4C616DEF03325DAFA3156C2DD32F58` |
| `posts\2026_h2_post_plan.md` | 8439 | 2026-06-08 14:36:51 | `7677FAD2CC87FD68C3B0FCD025C250B4208FF6300298AD3CF977781A4A88A5EE` |
| `review-replies\2026-05_review_replies.md` | 32894 | 2026-07-17 10:58:08 | `80D5C5A7D20FF9D29FF9EBE3FCD4C826857708340631B68705B6319F10B982CE` |

## 4スタイル参照の分類

### 現在の実行ロジック

- `SKILL.md:3-7,10-12,30-46,55-62,76`
- `references\reply-rules.md:14-32`
- `references\feedback-loop.md:20-28,43-53,60-67`

### 現在の例文・テンプレート

- `examples\good-output.md:14-20,39-46,78-86,108-116,137-145`

### 過去履歴

- `references\changelog.md:3-13`

履歴は保持し、廃止した事実を新規履歴として追記する。

## 矛盾マトリクス

| 論点 | 現行の衝突 | 影響 |
|:---|:---|:---|
| 4スタイル | 全件で4型必須だが、星だけは判定対象外、低評価は型より受け止め優先 | 同時遵守不能、余計な外部表示 |
| 星だけ高評価 | 「感謝だけ」と「今後の姿勢」「60〜140字」「SEO・CTA入り承認例」が共存 | 体験・感情・販促の水増し |
| 固定構造 | 感謝・具体点・今後の姿勢を固定しつつ、定型3文にしないとする | 空虚文・機能重複 |
| CTA | 1つだけ／軽く添える規則はあるが、0を選ぶ既定がない | 催促感、低評価への営業混入 |
| SEO | 希望時だけとしながら、希望確認を必須入力化し、星だけSEO例を現役化 | 返信より販促優先 |
| 事実性 | 事実追加禁止に対し、麻酔方法、鰻の仕上げ、星だけ来店を補う現役例がある | unsupported inference |
| 重複管理 | 直前5件と必ず言葉を変え、全案集の3割超で強制類語化 | 類語ガチャ、下書き混入 |
| フィードバック | 5件・60%・同タグ3回で共通skill-update提案 | 単一クライアントへの過適合 |
| 修正 | 差分記録はあるが、元口コミから全文再構成・全検査する規則がない | patch regression |

## 責任分離

| 層 | 置く情報 | 置かない情報 |
|:---|:---|:---|
| 共通スキル | 事実性、強度維持、推測禁止、公開リスク、情報量、CTA/SEO既定OFF、全文再構成、最終稿だけの分析、昇格条件 | 店名、地域名、固定フッター、重点メニュー、特定クライアントの好み |
| 共通スキルの業種節 | 医療・福祉、飲食・宿泊、美容・施術、法律・税務・金融・士業、BtoB、一般店舗の公開境界 | 特定事業者の文体やCTA |
| クライアント `profile.md` | 正式名、返信者、トーン、長さ傾向、CTA/SEO、外国語、窓口、knowledge参照節、再審査済み例 | 投稿用SEO、固定フッター、競合分析の自動流用 |
| クライアント `log.md` | 原文、初稿、最終稿、状態、日付、差分、理由、E/C/I/U、頻度対象 | 4スタイル、下書きを含む定型句集計 |

## クライアント資料の境界

### 条件付きで参照可能

- `knowledge.md:29-48`: 正式名称・業種・基本情報。必要な事実確認時だけ。
- `knowledge.md:52-150`: 口コミが具体的なメニューへ触れた場合だけ。
- `knowledge.md:10-17`: 公式ブランド表現。口コミと直接関係し、profileが許可する場合だけ。

### 自動読込禁止

- 投稿ルール・重点訴求 `knowledge.md:19-25`
- 販促上の強み `:180-206`
- 競合分析 `:210-244`
- 口コミ獲得施策・数値目標 `:248-284`
- SEOキーワード `:288-373`
- 固定フッター `:376-386`
- GBPビジネス説明文 `:390-396`
- GBP投稿用禁止事項 `:400-410`

## 旧返信資料の状態

- 36件の原文、複数案、参考訳、採用表示、ユーザー修正版、修正履歴、返信済みトラッカーが1ファイルに混在。
- #1〜8は採用表示あり・返信日なし、#9〜10は本文とトラッカーが衝突、#11〜19は確定表示・返信日なし、#20〜35はトラッカー日付あり、#36だけ明示的に返信済み。
- 星だけSEO/CTA、一言口コミの水増し、曖昧な「量が多かった」の肯定化、空虚文、同伴形態指定CTAを含む旧承認例がある。
- 元資料は監査証跡として保持し、`posted` または根拠付き `final_approved` だけを新ログの頻度対象候補にする。

## 変更対象

共通スキルのgate合格後に、次の7ファイルだけを本番適用候補とする。

1. `SKILL.md`
2. `references\reply-rules.md`
3. `references\evidence.md`
4. `references\feedback-loop.md`
5. `references\changelog.md`
6. `examples\good-output.md`
7. `examples\approved-replies.md`

クライアント側は共通スキル合格後の別変更単位で、`gbp-review\profile.md` と `gbp-review\log.md` の新規作成候補だけを扱う。既存12ファイルは変更しない。

## 非変更対象

- `.codex\skills\gbp-review-reply\SKILL.md`
- 既存workspaceのsnapshotと旧check-report
- `references\changelog.md` の既存履歴本文
- クライアント既存12ファイル
- `skill-management\SKILL.md`。一覧の古い「スタイル4型判定」は別のskill-update案件として報告だけ行う。
- 無関係の未追跡・未コミットファイル

