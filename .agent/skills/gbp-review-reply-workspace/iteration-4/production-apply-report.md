# iteration-4 本番適用報告

## 適用先・戻し先

- 本番: `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply`
- candidate: `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply-workspace\iteration-4\candidate-skill\gbp-review-reply`
- 適用前backup: `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply-workspace\iteration-4\production-backup-before-apply-20260722-201157\gbp-review-reply`
- backup manifest: `C:\Users\hangy\.gemini\antigravity\.agent\skills\gbp-review-reply-workspace\iteration-4\production-backup-before-apply-20260722-201157\sha256-manifest.txt`

## 適用前安全確認

- 本番ファイル数: 8
- iteration-4 snapshotファイル数: 8
- 相対path不足・余分: 0
- SHA-256差分: 0
- 上記一致を確認後にbackupを作成した。
- backupファイル数: 8
- backup manifest件数: 8

## 同期した明示14ファイル

既存8ファイルを更新:

1. `SKILL.md`
2. `references/reply-rules.md`
3. `references/evidence.md`
4. `references/feedback-loop.md`
5. `references/changelog.md`
6. `examples/approved-replies.md`
7. `examples/good-output.md`
8. `examples/quality-boundaries.md`

新規6ファイルを追加:

1. `examples/case-index.md`
2. `examples/star-only.md`
3. `examples/positive-short.md`
4. `examples/positive-detailed.md`
5. `examples/mixed-low-rating.md`
6. `examples/high-risk-special.md`

削除・移動は行っていない。`examples/cases`ディレクトリも作成していない。本番以外のcandidate、snapshot、eval、clientsは変更していない。

## 本番とcandidateの最終比較

- 本番ファイル数: 14
- candidateファイル数: 14
- 相対path不足: 0
- 相対path余分: 0
- SHA-256差分: 0

| SHA-256 | 相対path |
|:---|:---|
| `fa611ffdd7ae407f1f4dd286fb5dad97eb76ebaabe56ff090ef4b87c94692f79` | `SKILL.md` |
| `b63645128b87844cac91e15d34853fd14431b1b9d52dfcac95bdb62f2a57405b` | `references/reply-rules.md` |
| `c60cdb0ed179d48e83b6af8ce839fc968a729ebad6c879f1c9f643b79d64767e` | `references/evidence.md` |
| `8e9191ad24cc29292c39083496aa55da4431cfd8de2f678da3b819a5b0f6cb9e` | `references/feedback-loop.md` |
| `583f8b1157bf81fbd03a1ac5e9c0ad1e562243ab838856dd265f13114a38e8c1` | `references/changelog.md` |
| `499e0262754bfba962800c6c75018f77f7d123b72c20116325aceb323b9c922e` | `examples/approved-replies.md` |
| `91419cd79db509fab44145edd8d95d7bc89f3f3f7870c22eab4179bbdad93616` | `examples/case-index.md` |
| `da49685e1997a48e998c1f29f73113fb6d674e3aa81eee57aaad42b8f5af5996` | `examples/good-output.md` |
| `17cbccf6678d822f0267b849067c012f39a143e874c44ff978c382eccba6e6e3` | `examples/quality-boundaries.md` |
| `b849271b31ed5ece615210cdb235d70a18ad883fbc68d46c0b61ec99b3f2cec3` | `examples/star-only.md` |
| `e83714b265455cae0a8118049e88fe868ba8e7be51ac349f8217d0bd4cd0d92d` | `examples/positive-short.md` |
| `488c6451a544fe9aeee992c2d016021f8048113357efa0a70d9fe276f83d61d2` | `examples/positive-detailed.md` |
| `67313ddea8cdd0254928d4f2a3fdfa7f6e51cf59c7e9c762281e5fb7ad88e059` | `examples/mixed-low-rating.md` |
| `973df401208fad5551911f7b71a628719c6118cbc7f6542f550f65170387ca65` | `examples/high-risk-special.md` |

## 本番runtime検査

- runtime全文例: 26件
- 通常router参照候補: 26件
- U-R06: 1件、`confirmed-good`、返信hash `413f7c265a38bc716af7d6e480dd45cb6b57ea93b05d141cbad49bd7f66b30fa`
- W10-HD: 1件、`confirmed-good`、返信hash `f82d85d5df5e7372a322a2d84a542c7a1eaf93d54152aaa8113bccb86e0cec48`
- W11-HO: 1件、`confirmed-good`、返信hash `498873f808df6dc33a6186fc68ddd0d6acebe40ed07b46a1e3708e2d227fee41`
- A35 runtime例: 0件
- A35 historical source: 1件
- A35元返信hash: `239b9aef8d4b3f6a8c8c44b0a7c65a8fc257acdfb1c9bf434e114c83a092e323`
- Markdown相対リンク: 26件中26件解決、切れ0件。最終追加後の全リンク数が26件であり、旧時点の24件から増えた分も解決済み。
- 対象クライアント固有語（鰻の神楽、unaginokagura、京都駅、京都店）: 全本番14ファイルで0件
- runtime・active例への他クライアント固有名混入: 0件
- `clients\<client>`等の3ヒットは共通の参照手順2件とappend-only changelogの旧移設履歴であり、runtime固有情報ではない。

## 復元方法

1. 本番への書込みを止める。
2. backup manifestでbackup 8ファイルのhashを再確認する。
3. backup配下の8ファイルを、同じ相対pathで本番へ上書きする。
4. iteration-4で新規追加した次の6ファイルだけを、絶対path確認後に削除する。
   - `examples/case-index.md`
   - `examples/star-only.md`
   - `examples/positive-short.md`
   - `examples/positive-detailed.md`
   - `examples/mixed-low-rating.md`
   - `examples/high-risk-special.md`
5. 復元後の本番8ファイルとbackup 8ファイルを相対path・SHA-256で比較し、差分0を確認する。

この報告作成時点では復元操作を実行していない。
