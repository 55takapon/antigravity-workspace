# 007-schedule-setup セットアップ手順書

営業パイプラインを**指示なしで定期実行**する（＝毎日決まった時刻に、リスト収集→問い合わせURL→本文作成まで自動で用意する）ための設定手順。
**人間が読んで手で進めても、AI（Claude Code / Codex）に読ませてほぼ自動で終わらせても**よいように書いてある。

> スケジューラのローカル成果物（launchd/schtasks の登録・設定ファイル `~/.simesapo-sales/schedule.json`・kick殻）は
> **オーナー本人に見える形で置く（隠さない）**。送信（005）は既定で含めない＝本文作成まで用意して止まる。

---

## 0. これで何が起きるか（全体像）

定期実行は**2つのジョブ**で構成される。**prep（リスト取り）** と **send（送信）** はスケジュールが別枠で、
prep は送信せず本文まで用意し、send を「送るかどうか・どう送るか」は自分で選ぶ。

```
■ prep ジョブ（毎日・指定時刻。例: 08:00 / 14:00）
   指定時刻になると自動で（あなたの操作ゼロ）:
        ① 営業先リストを新規に集める → ② 各社の問い合わせ先を特定する → ③ 問い合わせ文を用意する
   （③の作り方は選べる: message_mode=ai＝会社ごとに文面を用意 / template＝用意した固定文の宛名を差し替え）
   → 問い合わせ文まで用意して停止。★prep は送信を絶対にしない。

■ send ジョブ（指定時刻。send.mode で挙動が決まる）
   ├ notify（既定・推奨）… 未送信件数を通知するだけ。送信は自分でシートを見て手動。
   └ auto            … 指定時刻に自動送信。方式は send.engine で選ぶ:
        ├ tier_a（既定）… 標準の自動送信。安全・追加準備なし・ほぼコストなし。送信率は控えめ。
        └ tier_b        … 送信率を最大化する自動送信。むずかしいフォームにも届きやすい。
                          そのぶんプラン枠を使う・claude 限定・要ブラウザ準備（詳細は後述）。
        → 送信対象外（除外リスト該当・送信済み等）は送らない。cap件を上限に、埋まった行は次回スキップ（二重送信しない）。
```

> **★prep が「送らない」担保**：Claude Code なら**送信の道具そのものを渡していない**ので、設定ミスがあっても物理的に送信できません。
> Codex はその仕組み上の保証が効かないため、指示側の安全弁で「送信しない」を担保します（⚠️未実機検証）。

- **既定は安全側**：send は notify（通知だけ）で出荷。自動送信したい人だけ `auto`＋engine を明示選択する（後述「④自動送信も定期実行にする人へ」）。

---

## 1. 前提（そろっているか最初に確認）

| 必要なもの | 確認方法 | 無い場合 |
|---|---|---|
| opener-core MCP トークン登録 | Claude Code=`claude mcp list`／Codex=`codex mcp get opener-core` に opener-core が出る | 未登録なら QUICKSTART 準備3（Claude Code=`claude mcp add`／Codex=`~/.codex/config.toml`）で登録（トークンは配布時に受領） |
| サービスアカウント鍵 | `shared/gcp_service_account.json` がある | 無ければ配布物に含まれるものを配置 |
| （template方式のとき）固定営業文 | `shared/message_template.md` に自分の営業文＋`{company_name}` | 無ければ `cp shared/3_message_template.example.md shared/message_template.md` して自分の文面に書き換え |
| ホストCLIが入っている | Claude Code=`claude` / Codex=`codex` が PATH で見つかる（kickが自動検出） | どちらか一方でOK。両方あれば `--host` で選べる（既定 auto＝claude優先→codex） |
| PC（Mac/Windows）が起動・ログイン中 | 発火時刻にPCが起きていること | スリープ中はその回スキップ（launchd / Task Scheduler の仕様） |

SA（サービスアカウント）のメールアドレスはここで確認できる:
```bash
python3 -c "import json;print(json.load(open('shared/gcp_service_account.json'))['client_email'])"
```

---

## 2. 手順（人間向け・順にやるだけ）

### Step 1. 定期実行用の専用シートを用意
本番の運用シートと分ける（列ズレ事故の回避）。**新規シートを作り、SAに編集権限を共有**する。

1. Googleスプレッドシートを新規作成（空でよい）。
2. 1行目に統一スキーマの英語ヘッダを入れる:
   `company_name, url, address, phone, maps_url, contact_url, message, sent_at, status, error_reason, screenshot_path, provider_used`
3. 「共有」→ 上記 SAのメール（`id-skill@...iam.gserviceaccount.com`）を**編集者**で追加。
4. URLからシートキー（`/d/` と `/edit` の間の文字列）を控える。

### Step 2. スケジュールを設定
`setup_schedule.py set` で `~/.simesapo-sales/schedule.json` に保存する（対話ヒアリングで決めた値を渡す）。

```bash
python3 .claude/skills/007-schedule-setup/scripts/setup_schedule.py set \
  --sheet-key   <シートキー> \
  --prep-times  08:00,14:00 \     # 1日1回なら --prep-time 08:00
  --prep-days   daily \           # 平日のみなら weekdays
  --prep-count  20 \              # 1回の収集目標社数
  --prep-message-mode template \  # template=固定文 / ai=会社ごとAI冒頭文
  --prep-budget 0 \               # 0=ドル上限なし（暴走保険は内部の max-turns。Claude Code のみ有効）
  --model       sonnet \          # ★自動実行で使うモデル（省略＝あなたの普段の既定モデルを継承）
  --prep-parallel on \            # リスト取りを並列で回す（省略＝off＝1本ずつ）
  --prep-concurrency 4 \          # 並列の本数（--prep-parallel on のとき）
  --host        auto              # 無人実行のホスト: auto(既定=claude優先→codex) / claude / codex
  # 収集条件を変えるなら: --criteria "求人媒体から今募集中のWeb制作会社を…"
```

> **▼ `--model` は付けておくのを推奨（コスト事故の防止）**
> 省略すると、自動実行は**あなたが普段づかいしている既定モデルをそのまま引き継ぎます**。
> 普段を高性能モデルにしている人は、夜間の自動実行も毎回その構成で走り、費用（プラン枠）が跳ねます。
> ジョブ別に変えたいときは `--prep-model` / `--send-model`（未指定なら `--model` → 既定の順で解決）。
> 実際に使われる値は `setup_schedule.py apply` の出力と**実行ログの先頭行**に必ず出ます。
>
> **選び方の目安**
> - **リスト取り**：探索と決まりきった処理が主。**安いモデルでも回りますが、下の「並列とセット」を必ずお読みください**
> - **送信**：フォームの読み取り判断が要るので、**しっかりしたモデル**（例 `--send-model sonnet`）が確実

> **▼ 並列でリスト取りする（`--prep-parallel on`）**
> 担当を分けて同時に複数走らせます。**既定はoff**（1本ずつ）なので、必要な人だけ有効にしてください。
>
> - **本数の目安は4本前後**。増やすほどPCが忙しくなります
> - **1本あたりの担当を軽くするのがコツ**。「4本×10件」の方が「1本×40件」より安く済みます
>   （1本に持たせすぎると、その1本の作業が長引き、費用が跳ねます）
> - **`--prep-count` は全体の目標件数**です。並列時は本数で割って各担当に配られます
>   （例：`--prep-count 40 --prep-concurrency 4` → 1本あたり10件）
>
> **⚠️ 安いモデルを使うなら並列とセットで**
> 安いモデルは、ときどき指示を守り切れず**空振り**します（調べたのに結果を残さず終わる）。
> **並列のときだけ**、それを検知してより確実なモデルで1回やり直す仕組みが働きます。
> 1本ずつの場合はこの拾い直しが無いため、空振りするとその回の収穫がゼロで終わります。
> → **1本ずつで運用するなら、モデルは指定しないか `sonnet`** が無難です。
>
> **送ってはいけない先の確認は、どちらの場合も必ず入ります。**
> 収集後に**その回に増えた行だけ**をまとめて確認し、送ってはいけない先は削除、手動送信が必要な先には印を
> 付けます。確認そのものができなかった場合は `要確認` の印が付き、**自動送信の対象から外れます**
> （`status` 列にこの印がある行は④が送りません）。

> **▼ Codex で無人実行する人へ**
> - `--host codex` を付けると Codex 固定になります（省略時 `auto` は claude を優先し、無ければ codex）。**Claude Code が入っていない環境なら `auto` のままでOK**（自動で codex が選ばれます）。
> - Codexの承認モードは設定ファイルの `codex_exec_flags`（既定 `--full-auto`＝無人で承認を挟まない）が `codex exec` に渡ります。変えたい場合は `~/.simesapo-sales/schedule.json` の同キーを直接編集。
> - ⚠️ **Codexには `--allowedTools` 相当（per-runのツール制限）が無い**ため、`--prep-budget` のドル上限も効きません。prepの「送信しない」はプロンプトの安全弁で担保されます（§0の注記）。

> **▼ ④自動送信も定期実行にする人へ（send.mode=auto）**
> 送信方式は2つ。既定は安全な `tier_a`。
> - `--send-mode auto --send-engine tier_a`：標準の自動送信。安全・追加準備なし・ほぼコストなし・送信率は控えめ。
> - `--send-mode auto --send-engine tier_b --send-concurrency N`：**送信率を最大化**する自動送信。むずかしいフォームにも届きやすい。
>   **そのぶんプラン枠（トークン）を使う**・**claude 環境限定**・要ブラウザ準備（`N`＝並列数）。
>
> **tier_b を選ぶ人が理解しておく3点：**
> 1. **1日に何件送るか＝cap × 実行回数**。例）cap=10・1日3回なら**最大30件/日**が上限。ただし営業お断り/CAPTCHA/検出失敗は
>    自動でスキップするため、**実際に送れる数はこれより少なめ**（＝上限であって「必ず30件送る」ではない）。件数を増減したいときは `--cap` を変える。
> 2. **並列台数 N はPC依存**。`setup_schedule.py recommend` で推奨/上限を確認（律速はRAM・1台≒0.7GB）。多いほど速いが
>    メモリを食う。低スペックPCは自動で控えめに出る。**tier_b は事前に chromium が必要**：初回だけ `npx playwright install chromium`。
> 3. **結果はシートの `status` 列で「次に何をすればいいか」が分かる（バケツ＋色分け）**：
>    - 🟢 **送信済み**（緑）… 完了。何もしなくてよい。
>    - 🔴 **要目視**（赤）… 送信ボタンは押せたが完了画面を確認できなかった＝**相手に届いているかもしれない**。
>      **手で送る前に確認する**（先方に届いていれば2通目になる＝取り消せない）。確認して未送信だと分かったら `status` を空にすれば次回自動で送る。
>    - ⚪ **要手動送信**（色なし）… リスト取り段階でCAPTCHA等を検知（自動送信は最初から対象外）。自分で送れば取れる。※件数が多いので色は付けない。
>    - 🟠 **要手動送信（試行後）**（オレンジ）… 自動送信を試したが送りきれず、手動が要る分（例：CAPTCHA）。**実際に試した分**なので目立たせる。自分で送れば取れる。
>    - 🟡 **要見直し**（黄）… 設定を直せば次回自動で送れる（本文が長すぎ→短縮版に／問い合わせ先URLが違う→修正）。
>    - ⚫ **送信不可**（灰）… フォーム無・死にサイト・WAF(403)・営業お断り。諦めてよい。
>    - ⚫ **除外**（灰）… 除外リスト該当・重複行（意図的スキップ）。
>    詳しい理由は隣の `error_reason` 列（日本語）。埋まった行は次回スキップ（二重送信しない）。送り直したい行は `status` を空にする。
>    色分けは初回だけ `python .claude/skills/005-form-send/scripts/tierb_colorize.py <シートキー>` で設定（緑=送信済み/**赤=要目視**/オレンジ=試行後/黄=要見直し/灰=諦め・要手動送信は色なし）。
>    ★**赤とオレンジは意味が逆**です。オレンジ＝手で送ってよい／赤＝送る前に確認する。
>
>   - **登録前に必ず preflight**：`setup_schedule.py preflight` が **GO** なら apply、NG なら解消（chromium導入 / opener-core 登録 / host=claude）か `tier_a` に切替。
>   - 重い/コストが気になるときは `--cap` や `--send-concurrency` を下げるか、`--send-engine tier_a`（ほぼ0トークン）や `--send-mode notify`（通知だけ）へ戻せる。
>   - ⚠️ Windows の tier_b は未実機検証。当面 Mac 先行。

### Step 3. スケジューラへ登録（有効化）
```bash
# （tier_b のときは先に）python3 .../setup_schedule.py preflight   # GO を確認
python3 .claude/skills/007-schedule-setup/scripts/setup_schedule.py apply --only prep
```
Mac は launchd、Windows は Task Scheduler へ自動判定で登録される。

### Step 4. 確認
```bash
python3 .claude/skills/007-schedule-setup/scripts/setup_schedule.py verify
```
指定時刻になれば自動で走る。ログは `~/Library/Logs/claude-sales-prep.log`（Windowsは `%LOCALAPPDATA%\simesapo-sales\logs\`）。
※ファイル名は `claude-` 始まりですが、**Codex で実行した場合も同じファイル**に出ます（ホスト名ではなくジョブ名由来）。

### 変更・停止
```bash
# 時刻や件数の変更 → set で上書き → apply で反映
python3 .../setup_schedule.py set --prep-times 09:00 --prep-count 30
python3 .../setup_schedule.py apply --only prep
# 停止（登録解除・設定ファイルは残る）
python3 .../setup_schedule.py remove
```

---

## 3. AI実行手順（Claude Code / Codex がこの節に従えばほぼ自動で完了）

> ユーザーが「営業を定期実行にして」「毎朝リスト取りを自動化して」等と言ったら、この順で進める。
> 途中の【ASK】だけユーザーに聞き、それ以外は自動で実行する。

1. **前提チェック**（§1）: opener-core の登録（Claude Code=`claude mcp list`／Codex=`codex mcp get opener-core`）、`shared/gcp_service_account.json` の有無、
   template方式なら `shared/message_template.md` の有無を確認。欠けていれば具体的な補い方を提示。
2. **【ASK】設定値をまとめて1回ヒアリング**（AskUserQuestion）:
   - 実行時刻（1日1回 or 複数回。例 08:00 / 14:00）
   - 頻度（毎日 daily / 平日 weekdays）
   - 1回の件数（例 20）
   - 本文方式（template=固定文＋会社名 / ai=会社ごとAI冒頭文）
   - 収集条件（既定＝求人媒体から今募集中のWeb制作・Webマーケ会社）
   - ★送信を含めるか（既定=含めない。含めるは方針C＝要別途確認・実地検証）
3. **専用シートの用意**:
   - MCPが使える環境なら `google_drive.create_file`（mimeType=spreadsheet）で新規作成 → シートキー取得。
   - SAメールを取得（§1のコマンド）し、**ユーザーにそのシートをSAへ編集者共有してもらう**（共有付与ツールが無いためここだけ手動・1回）。
   - 共有後、SA経由で1行目に英語12列ヘッダを書き込む（`shared/sheets_io.py` を使うと確実）:
     `open_worksheet(key).update([HEADER], "A1")`
4. **設定保存**: `setup_schedule.py set ...`（ヒアリング結果を反映。§2 Step2）。
5. **登録**: `setup_schedule.py apply --only prep`（送信を含める判断が出た場合のみ send も）。
6. **検証**: `setup_schedule.py verify`。加えて登録内容を直接確認するなら
   **Mac**=`plutil -p ~/Library/LaunchAgents/com.claude.simesapo-sales-prep.plist`（StartCalendarInterval が意図どおりか）／
   **Windows**=`schtasks /Query /TN com.claude.simesapo-sales-prep /V /FO LIST`。
7. **完了報告**: 「いつ・何が走るか」「どう止めるか（remove）」「PCが起きている必要」「コスト＝**普段使っているホストのプラン枠を消費**（Claude Code=Claude Max 等／Codex=Codexプラン）」をユーザーへ明示。
8. （任意）その場で1回試したいなら、時刻を数分後に設定して発火を待つ／即時実行は
   **Mac**=`launchctl kickstart -k gui/$UID/com.claude.simesapo-sales-prep`／**Windows**=`schtasks /Run /TN com.claude.simesapo-sales-prep`。

**AIが守ること**:
- Claude Code は `--permission-mode bypassPermissions` を使わない（kickは allowlist 限定＝prepに送信ツールを渡さない）。Codex は per-run のツール制限が無いため、prep の非送信は kick のプロンプト安全弁で担保（構造的保証は無い＝⚠️未実機検証）。
- 送信（005）を勝手に含めない。含めるのはユーザーが明示した時だけ。
- 自動起動を隠さない（登録内容・停止方法を必ず伝える）。

---

## 4. 落とし穴（既知・重要）

- **PCが寝ていると走らない**：発火時刻に起動・ログイン中であること。毎日確実に、が要件なら中央実行(1台)の方が向く。
- **コスト**：ヘッドレス実行は普段のホスト枠（Claude Code=Claude Max 等／Codex=Codexプラン）を消費する。件数×頻度が多いほど枠を食い、超過課金になり得る。template方式はAI生成が無いぶん ai方式より安い。
- **専用シートの列**：英語ヘッダ（company_name等）で作る。日本語ヘッダの既存運用シートに直接足すと列ズレで新規行が対象外になる事故がある。
- **SA鍵のスコープ**：`spreadsheets` のみ＝**ファイル作成/共有はできない**。新規シート作成はユーザー側（MCP等）で行い、SAへの共有は手動1回。
- **bash 3.2（macOS標準）**：`set -u`＋空配列の `"${arr[@]}"` は unbound エラーになる。kick内では `${arr[@]+"${arr[@]}"}` で保護済み（自作で触るとき注意）。
- **求人の鮮度**：「今募集中」は自社採用ページに求人票がある/採用ページを持つ、が基準。掲載日で厳密に絞らないため古い求人を拾うことがある。
- **Windows は未実機検証**：Task Scheduler / `kick_sales.ps1` 経路は実装済みだが実機テストが済んでいない。Windowsで使う場合は最初の1回を手動（`schtasks /Run`）で確認してから任せること。

---

## 5. 参考ファイル
- `scripts/setup_schedule.py` … 設定CRUD＋OS別登録（apply/remove/verify/set/show）
- `scripts/kick_sales.sh`(Mac) / `kick_sales.ps1`(Windows) … 実際に走る殻（**ホスト claude/codex を解決**＋prep/send・ai/template・送信可否を分岐）
- `references/os_matrix.md` … Mac/Windows のコマンド・スリープ対策・権限
- `~/.simesapo-sales/schedule.json` … 現在の設定（真実の源）
- `docs/design/scheduler_distribution.md` … 設計の全体像（※**開発者向け・配布物には含まれません**。手元に無くても運用に支障なし）
