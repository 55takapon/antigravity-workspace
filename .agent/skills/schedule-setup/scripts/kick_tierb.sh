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
"$PYBIN" "$SCRIPTS/tierb_mcpconfig.py" "$CONCURRENCY" "$WORKDIR/mcp.json" >> "$LOG" 2>> "$ERR" \
  || die "mcp-config 生成失敗（opener-core 未登録?）"

# allowlist: フロー取得 + サブエージェント + Read + 書き戻し(venv python 絶対パス) + playwright1..N
WB="$PYBIN $SCRIPTS/tierb_writeback.py"
ALLOWED=( "mcp__opener-core__get_skill_flow" "Task" "Agent" "Read" "Bash($PYBIN *)" "Bash(python3 *)" )
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

"$CLAUDE_BIN" -p "$PROMPT" \
  --mcp-config "$WORKDIR/mcp.json" --strict-mcp-config \
  --allowedTools "${ALLOWED[@]}" \
  ${MODEL_FLAG[@]+"${MODEL_FLAG[@]}"} \
  --max-turns 1000 --no-session-persistence \
  >> "$LOG" 2>> "$ERR"
RC=$?
[[ $RC -eq 0 ]] || die "phase2 claude -p (tier_b) exited $RC"
relabel
log "tier_b send done (rc=0・phase1+phase2)"
exit 0
