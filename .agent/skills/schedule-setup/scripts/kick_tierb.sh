#!/bin/bash
#
# kick_tierb.sh — Tier B（AI並列ヘッドレスブラウザ）無人送信の実行部（kick_sales.sh から委譲）。
#
#   ★2フェーズ（スキル本来の階層設計を守る）:
#     Phase 1 = Tier A 決定論送信（run_on_sheet.py＝HTTP POST先行＋パターンマッチ Stage1.5）。
#               ほぼ0トークンで送れる社はここで確定。送れなかった社は tier_b_queue へ出る。
#     Phase 2 = Tier B（AIブラウザ）。Phase1 の残余（tier_b_queue）だけを、CONCURRENCY 本の
#               サブエージェントが各自 mcp__playwright{i} で並列送信する。送信手順/安全規則は
#               秘匿フロー schedule-run-send（サーバー）に閉じ、この殻は環境を整えて起動するだけ。
#
#   ★0件バグ回避: ブラウザMCPを前景で叩く＝サブエージェント完了を -p が待つ。
#   ★書き戻し: venv python の絶対パスを allowlist に入れる（python無し/python3のみ環境の承認ブロック回避）。
#              Phase2 は Tier A が failed にした行を送り直すため --overwrite-failed で上書きする。
#   ★claude host 限定（MCPを --mcp-config で per-run に渡すため。codex は非対応）。
#
# kick_sales.sh から export される: REPO_ROOT SHEET_KEY CAP CONCURRENCY HOST CLAUDE_BIN LOG ERR
#
set -uo pipefail

ts() { date "+%Y-%m-%d %H:%M:%S"; }
log() { echo "[$(ts)] $*" >> "${LOG:-/dev/stderr}"; }
die() { echo "[$(ts)] ERROR(tierb): $*" >> "${ERR:-/dev/stderr}"; exit 1; }

[[ "${HOST:-}" == "claude" ]] || die "tier_b は claude host 限定（現在 host=${HOST:-?}）"
[[ -n "${REPO_ROOT:-}" && -d "$REPO_ROOT" ]] || die "REPO_ROOT 不正"
[[ -n "${SHEET_KEY:-}" ]] || die "SHEET_KEY 未設定"
[[ -x "${CLAUDE_BIN:-}" ]] || die "claude binary not found"
# 使用モデル（kick_sales.sh が config から解決して export）。空＝claude の既定モデルを継承。
MODEL_FLAG=()
[[ -n "${MODEL:-}" ]] && MODEL_FLAG=(--model "$MODEL")
[[ "${CONCURRENCY:-}" =~ ^[0-9]+$ ]] || CONCURRENCY=3
CAP="${CAP:-10}"

PYBIN="${REPO_ROOT}/.claude/skills/005-form-send/.venv/bin/python"
[[ -x "$PYBIN" ]] || PYBIN="$(command -v python3)"
FS_DIR="${REPO_ROOT}/.claude/skills/005-form-send"
SCRIPTS="${FS_DIR}/scripts"
LOGDIR="${FS_DIR}/logs"
SENDER="${REPO_ROOT}/shared/sender_info.json"

# ラン末尾に status を5バケツ（送信済み/要手動送信/要見直し/送信不可/除外）へ畳む（#49 status区別）。
relabel() { "$PYBIN" "$SCRIPTS/tierb_relabel.py" "$SHEET_KEY" >> "$LOG" 2>> "$ERR" || true; }

# ===== Phase 1: Tier A（決定論・HTTP POST＋パターンマッチ）=====
Q_BEFORE="$(ls -t "$LOGDIR"/tier_b_queue_*.jsonl 2>/dev/null | head -1)"
log "phase1(Tier A・determinstic・headless): limit=${CAP} sheet=${SHEET_KEY}"
AUTOFORM_HEADLESS=1 "$PYBIN" "$SCRIPTS/run_on_sheet.py" "$SHEET_KEY" --limit "$CAP" >> "$LOG" 2>> "$ERR"
RC=$?
[[ $RC -eq 0 ]] || die "phase1(Tier A) exited $RC"

# Phase1 が新しく出した tier_b_queue（＝Tier A で送れなかった残余）を特定する。
Q_AFTER="$(ls -t "$LOGDIR"/tier_b_queue_*.jsonl 2>/dev/null | head -1)"
if [[ -z "$Q_AFTER" || "$Q_AFTER" == "$Q_BEFORE" || ! -s "$Q_AFTER" ]]; then
  log "Tier A で完了（Tier B 残余なし）。tier_b は起動しない。"
  relabel
  log "tier_b send done (rc=0・phase1のみ)"
  exit 0
fi
QUEUE="$Q_AFTER"
log "phase1 残余 → phase2(Tier B) 対象キュー: $QUEUE"

# ===== Phase 2: Tier B（AI並列ブラウザ・残余のみ）=====
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

# 残余を CONCURRENCY 本へ disjoint 分割（正規化contact_url重複排除つき）
"$PYBIN" "$SCRIPTS/tierb_shards.py" "$SHEET_KEY" "$CAP" "$CONCURRENCY" "$WORKDIR/shards" \
  --from-queue "$QUEUE" >> "$LOG" 2>> "$ERR" || die "shard生成失敗"

# 全シャードが空なら Tier B は不要（残余が対応づけ不能等）
TOTAL="$(cat "$WORKDIR"/shards/worker*.json 2>/dev/null | grep -c '"row"' || true)"
if [[ "${TOTAL:-0}" -eq 0 ]]; then
  log "phase2 対象0件（残余をシート行に対応づけできず）。tier_b は起動しない。"
  relabel
  log "tier_b send done (rc=0・phase1のみ)"
  exit 0
fi

# opener-core（フロー取得）＋ playwright1..N（独立ヘッドレス）の mcp-config
"$PYBIN" "$SCRIPTS/tierb_mcpconfig.py" "$CONCURRENCY" "$WORKDIR/mcp.json" >> "$LOG" 2>> "$ERR"
MCPRC=$?
case "$MCPRC" in
  0) ;;
  # ★rc=4 は「npx が無くブラウザを1台も起動できない」＝Tier B は1社も送れない。ここで必ず止める。
  #   以前はここを素通りし、何もできないまま「完了」とログに書いていた（2026-08-19 モニター報告）。
  4) die "npx が見つからず tier_b のブラウザを起動できない（詳細は $ERR）。Node.js の導入か置き場所の確認が必要";;
  3) die "opener-core が未登録＝送信手順を取得できない（詳細は $ERR）";;
  *) die "mcp-config 生成失敗 (rc=$MCPRC)";;
esac

# ===== 書き戻しコマンドを「空白を含まない固定パス」の背後に隠す（★空白入りリポジトリ対策）=====
# repo_root に空白があると Bash(<絶対パス> *) の許可ルールが成立しない。AIは空白を含むパスを
# 正しくクォートして書くため、クォート無しのルールと前方一致しないからだ（2026-08-19 実機で確認）。
# 結果、書き戻しが全件拒否される。固定パスの薄いラッパーを噛ませて、許可ルールから空白を消す。
WB_DIR="${HOME}/.simesapo-sales/bin"
mkdir -p "$WB_DIR" 2>/dev/null || true
WB="${WB_DIR}/tierb_writeback"
case "$WB" in
  *" "*) die "書き戻しコマンドのパスに空白が含まれる（$WB）。ホームディレクトリ名に空白があると許可ルールを作れない";;
esac
# ★1社ごとの書き戻しを、この行数で数える。Tier B の「成果ゼロ」を機械的に検出するための唯一の証跡。
WB_LOG="${WORKDIR}/writeback.log"
: > "$WB_LOG"
cat > "$WB" <<EOF
#!/bin/bash
# 自動生成（kick_tierb.sh）。空白を含むリポジトリパスを、許可ルールが通る固定パスの背後に隠す。
printf '%s\n' "\$*" >> "$WB_LOG" 2>/dev/null
exec "$PYBIN" "$SCRIPTS/tierb_writeback.py" "\$@"
EOF
chmod +x "$WB"

# allowlist: フロー取得 + サブエージェント + Read/Glob(シャード探索) + 書き戻し + playwright1..N
# ★Glob / ls / TodoWrite を入れておく理由: 無いとオーケストレーターがシャード一覧を数えようとして
#   拒否され、そこで手が止まる。-p モードでは承認を求める相手がいないので、拒否＝即座に手詰まり。
ALLOWED=( "mcp__opener-core__get_skill_flow" "Task" "Agent" "Read" "Glob" "TodoWrite"
          "Bash($WB *)" "Bash(ls *)" "Bash($PYBIN *)" "Bash(python3 *)" )
for i in $(seq 1 "$CONCURRENCY"); do ALLOWED+=( "mcp__playwright${i}" ); done

export CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=1800000
log "phase2(Tier B・並列${CONCURRENCY}・headless): 残余${TOTAL}件"

# 手順本体は秘匿フロー schedule-run-send（サーバー）。ここは「フローを取得して従え」だけの薄殻。
PROMPT="あなたは simesapo-sales-auto-skills の無人並列送信オーケストレーター（Tier B・Tier A残余担当）です。opener-core の get_skill_flow を {\"skill\":\"schedule-run-send\"} で呼び、返る手順に厳密に従って実行してください（無人・依頼確認は挟まない）。
パラメータ:
- sheet_key=${SHEET_KEY}
- concurrency=${CONCURRENCY}（サブエージェント数＝専用ブラウザ mcp__playwright1..${CONCURRENCY}）
- shard_dir=${WORKDIR}/shards（worker{i}.json が担当リスト＝Tier A が送れなかった残余。worker i は mcp__playwright{i} だけを使う）
- writeback_cmd=\"${WB}\"（1社ごとに: <writeback_cmd> ${SHEET_KEY} <row> \"<company>\" <status> playwright_mcp <reason_code> --overwrite-failed）
- sender_info=${SENDER}
理由はコード（no_solicitation/captcha/form_not_found 等）で渡すこと（日本語化は writeback 側で行う）。安全弁（営業お断り/CAPTCHA はスキップ・最終確定ページ＋送信後コンソール確認で成功判定・本文改変禁止・シャード外へ送らない）を厳守し、最後に worker 別サマリを標準出力へ。"

# ★--output-format json で回す。テキスト出力のままだと「1つも実行できなかった」ことが
#   どこにも残らない（claude -p はツール全拒否でも rc=0 を返す）。本文と拒否は claude_result.py が出す。
RESJSON="${WORKDIR}/phase2_result.json"
"$CLAUDE_BIN" -p "$PROMPT" \
  --mcp-config "$WORKDIR/mcp.json" --strict-mcp-config \
  --allowedTools "${ALLOWED[@]}" \
  ${MODEL_FLAG[@]+"${MODEL_FLAG[@]}"} \
  --max-turns 1000 --no-session-persistence \
  --output-format json > "$RESJSON" 2>> "$ERR"
RC=$?
# 本文をログへ／拒否があれば全件を ERR へ（rc=5 は「拒否あり」で、それ自体では止めない）
"$PYBIN" "${REPO_ROOT}/.claude/skills/007-schedule-setup/scripts/claude_result.py" \
  "$RESJSON" --label tier_b >> "$LOG" 2>> "$ERR" || true
[[ $RC -eq 0 ]] || die "phase2 claude -p (tier_b) exited $RC"

# ===== ★成果ゼロの門番（rc=0 の嘘を潰す）=====
# 送るべき残余があったのに1社も記録していない＝ブラウザが起動しない/全ツール拒否 等で
# 何もできなかった、ということ。ここで必ず落とす。「完了」と書いてはいけない。
# ※grep -c は空ファイルで「0」を出しつつ終了コード1を返す＝`|| echo 0` と併用すると "0\n0" になり
#   算術比較が壊れる。wc -l は空でも rc=0 なのでこちらを使う。
WB_DONE="$(wc -l < "$WB_LOG" 2>/dev/null | tr -d ' ')"
if [[ "${WB_DONE:-0}" -eq 0 ]]; then
  die "tier_b が1社も記録できていない（対象${TOTAL}件・書き戻し0件）。ブラウザ起動失敗かツール拒否の疑い。$ERR の [tier_b] 行を確認すること"
fi
[[ "$WB_DONE" -lt "$TOTAL" ]] && log "⚠️ tier_b: 対象${TOTAL}件に対し記録は${WB_DONE}件（差分は未処理の疑い）"

relabel
log "tier_b send done (rc=0・phase1+phase2・記録${WB_DONE}/${TOTAL}件)"
exit 0
