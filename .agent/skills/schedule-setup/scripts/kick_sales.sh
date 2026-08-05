#!/bin/bash
#
# kick_sales.sh <job>   — 配布用・汎用kick殻（Mac）。job = prep | send
#
#   prep : ①②③ を回し message列まで用意して停止（★送信ツール非許可＝構造的に送れない）
#   send : ④送信。~/.simesapo-sales/schedule.json の send.mode に従う
#            notify → 未送信件数を通知するだけ（送信ツール非許可）
#            auto   → 実送信（--limit cap・status済/excludedは送らない・bypassは使わない）
#
# 設定の真実の源: ~/.simesapo-sales/schedule.json（setup_schedule.py が書く）
# ★これは雛形。promote時は頭脳/ポリシーをサーバーへ寄せ、殻はトークン接続だけにする。
#
set -uo pipefail

JOB="${1:-prep}"
DRY=0
[[ "${2:-}" == "--dry-run" ]] && DRY=1

CONFIG="${HOME}/.simesapo-sales/schedule.json"
# claude / codex バイナリを環境非依存で自動検出（PATH優先→nodebrew→npm-global の順）。CLAUDE_BIN/CODEX_BIN env で上書き可。
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || true)}"
[[ -z "$CLAUDE_BIN" ]] && for c in "$HOME/.nodebrew/current/bin/claude" "$HOME/.npm-global/bin/claude" "/usr/local/bin/claude" "/opt/homebrew/bin/claude"; do [[ -x "$c" ]] && CLAUDE_BIN="$c" && break; done
CODEX_BIN="${CODEX_BIN:-$(command -v codex || true)}"
[[ -z "$CODEX_BIN" ]] && for c in "$HOME/.nodebrew/current/bin/codex" "$HOME/.npm-global/bin/codex" "/usr/local/bin/codex" "/opt/homebrew/bin/codex"; do [[ -x "$c" ]] && CODEX_BIN="$c" && break; done
LOG="${HOME}/Library/Logs/claude-sales-${JOB}.log"
ERR="${HOME}/Library/Logs/claude-sales-${JOB}-error.log"

ts() { date "+%Y-%m-%d %H:%M:%S"; }
log() { echo "[$(ts)] $*" >> "$LOG"; }
fail() { echo "[$(ts)] ERROR: $*" >> "$ERR"; echo "[$(ts)] FAILED" >> "$LOG"; exit 1; }

[[ -f "$CONFIG" ]] || fail "設定がありません: $CONFIG（setup_schedule.py set を先に）"

# --- 設定読み出し（jq非依存でpythonで抜く）---
read_cfg() { python3 -c "import json,sys;d=json.load(open('$CONFIG'));print(eval('d'+sys.argv[1]))" "$1" 2>/dev/null; }
REPO_ROOT="$(read_cfg "['repo_root']")"
SHEET_KEY="$(read_cfg "['sheet_key']")"
CRITERIA="$(read_cfg "['criteria']")"
SEND_MODE="$(read_cfg "['send']['mode']")"
CAP="$(read_cfg "['send']['cap']")"
PREP_COUNT="$(read_cfg "['prep'].get('count',100)")"
PREP_BUDGET="$(read_cfg "['prep'].get('budget_usd',0)")"   # 0=ドル上限なし（暴走はmax-turnsで止める）
MESSAGE_MODE="$(read_cfg "['prep'].get('message_mode','ai')")"   # ai=③冒頭文生成 / template=004固定文
PREP_PARALLEL="$(read_cfg "['prep'].get('parallel',False)")"   # True=並列リスト取り / False=単一(既定)
PREP_CONCURRENCY="$(read_cfg "['prep'].get('concurrency',4)")"  # 並列で同時に走らせる本数

# --- 使用モデル（★無人実行のコスト直結）---
# 未指定だと claude -p は「ユーザーのグローバル既定モデル」を継承する＝既定が高額モデルの人は
# 毎晩いちばん高い構成で走ってしまう。config で明示できるようにし、実効値をログに必ず残す。
#   config: {"model": "sonnet"} 全ジョブ既定 / {"prep":{"model":...}} {"send":{"model":...}} でジョブ別上書き。
#   空文字（既定）＝従来どおり継承（挙動不変）。
MODEL_GLOBAL="$(read_cfg "['model']")"; [[ "$MODEL_GLOBAL" == "None" ]] && MODEL_GLOBAL=""
MODEL_JOB="$(read_cfg "['${JOB}'].get('model','')")"; [[ "$MODEL_JOB" == "None" ]] && MODEL_JOB=""
MODEL="${MODEL_JOB:-$MODEL_GLOBAL}"
MODEL_FLAG=()
if [[ -n "$MODEL" ]]; then
  MODEL_FLAG=(--model "$MODEL")
  log "model = $MODEL（config指定）"
else
  log "model = 未指定（claude/codex のグローバル既定を継承）。コストを固定したいなら setup_schedule.py set --model sonnet"
fi

[[ -n "$REPO_ROOT" && -d "$REPO_ROOT" ]] || fail "repo_root が不正: $REPO_ROOT"
[[ -n "$SHEET_KEY" ]] || fail "sheet_key 未設定"

# --- ホスト解決（config['host']: auto|claude|codex。auto=claude優先→codex）---
HOST="$(read_cfg "['host']")"; [[ -z "$HOST" || "$HOST" == "None" ]] && HOST="auto"
if [[ "$HOST" == "auto" ]]; then
  if [[ -n "$CLAUDE_BIN" && -x "$CLAUDE_BIN" ]]; then HOST="claude"
  elif [[ -n "$CODEX_BIN" && -x "$CODEX_BIN" ]]; then HOST="codex"
  else fail "claude も codex も見つかりません（どちらかのCLIが必要）"; fi
fi
case "$HOST" in
  claude) [[ -x "$CLAUDE_BIN" ]] || fail "claude binary not found: $CLAUDE_BIN";;
  codex)  [[ -x "$CODEX_BIN" ]] || fail "codex binary not found: $CODEX_BIN";;
  *) fail "未知のhost: $HOST（auto|claude|codex）";;
esac

# --- ロック（ジョブ別・二重起動防止）---
LOCK_DIR="${REPO_ROOT}/ops/scheduler/.lock-${JOB}"
# ★親ディレクトリを先に作る: 配布リポには ops/ が含まれない（配布除外）ため、新規cloneでは
#   ops/scheduler が存在せず mkdir(親を作らない) が失敗して「ロック取得失敗」で即死していた。
#   ロック本体は下の mkdir "$LOCK_DIR"（アトミック＝排他の要）。親作成だけを分離する。
mkdir -p "${REPO_ROOT}/ops/scheduler" 2>/dev/null || true
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  if find "$LOCK_DIR" -maxdepth 0 -mmin +180 2>/dev/null | grep -q .; then
    rm -rf "$LOCK_DIR"; mkdir "$LOCK_DIR" || fail "ロック取得失敗"
  else
    fail "別の実行が進行中（$JOB）"
  fi
fi
trap 'rm -rf "$LOCK_DIR"' EXIT

cd "$REPO_ROOT" || fail "cannot cd $REPO_ROOT"
log "=== kick_sales $JOB start (dry=$DRY, mode=$SEND_MODE) ==="

# gspread/sheets_io を持つ python（001の.venv）。無ければ system python3。reap で使う。
PY_SHEETS="${REPO_ROOT}/.claude/skills/001-list-extract/.venv/bin/python"
[[ -x "$PY_SHEETS" ]] || PY_SHEETS="$(command -v python3)"

# prep後の仕分け: 「手動送信要」の行をシート1→専用タブ「要手動送信_リスト取り段階」へ移送する。
# 収集の成否とは独立の後処理なので、失敗しても prep 全体は止めない（行はシート1に残るだけ＝データ損失なし）。
# DRY のときは prep 本体が --preview なのに合わせ、こちらも --preview（1セルも書かない）。
reap_manual() {
  local extra="" rc
  [[ "${DRY:-0}" == "1" ]] && extra="--preview"
  "$PY_SHEETS" "${REPO_ROOT}/.claude/skills/007-schedule-setup/scripts/prep_reap_manual.py" \
    "$SHEET_KEY" $extra >> "$LOG" 2>> "$ERR"
  rc=$?
  if [[ $rc -eq 0 ]]; then
    log "reap: 手動送信要の行を『要手動送信_リスト取り段階』へ移送（rc=0, dry=${DRY:-0}）"
  else
    log "reap: 移送 rc=$rc（prep本体は成功のまま継続・行はシート1に残置）"
  fi
}

# ---- 単一パス（1本で順に処理）用の門番 ----
# 送ってはいけない先の除外は、この経路では収集AI自身が行っている。安いモデルはこの手順を
# 黙って飛ばすことがあり、実際に営業お断りの会社が混入した（並列側は親が最後に照合して防いだ）。
# そこで「収集前の行数を控え → 収集後に増えた行だけをまとめて1回照合」する門番を置く。
# 照合できなければ増えた行へ status='要確認' を付ける（④自動送信は status 非空を送らない）。
VERIFY_DIR="${REPO_ROOT}/ops/scheduler"
VERIFY_STATE="${VERIFY_DIR}/.verify-prep.json"
VERIFY_SCRIPT="${REPO_ROOT}/.claude/skills/007-schedule-setup/scripts/prep_verify_appended.py"

verify_snapshot() {
  mkdir -p "$VERIFY_DIR" 2>/dev/null || true
  "$PY_SHEETS" "$VERIFY_SCRIPT" snapshot "$SHEET_KEY" --out "$VERIFY_STATE" >> "$LOG" 2>> "$ERR" \
    && log "収集前スナップショットを取得" \
    || log "収集前スナップショット失敗（後段の照合はスキップされる）"
}

verify_appended() {
  [[ -f "$VERIFY_STATE" ]] || { log "検証: スナップショット無し→スキップ"; return 0; }
  local cands="${VERIFY_DIR}/.verify-cands.json" fres="${VERIFY_DIR}/.verify-filter.json" rc
  rm -f "$fres"
  "$PY_SHEETS" "$VERIFY_SCRIPT" export "$SHEET_KEY" --state "$VERIFY_STATE" --out "$cands" \
    >> "$LOG" 2>> "$ERR"; rc=$?
  if [[ $rc -eq 3 ]]; then log "検証: 今回増えた行なし→スキップ"; return 0; fi
  [[ $rc -eq 0 ]] || { log "検証: 増分の書き出しに失敗（スキップ）"; return 0; }

  # 照合は「ファイルを読む→ツールを1回呼ぶ→書く」だけの短い会話。ツールも1つしか許可しない。
  local fp="次を厳密に実行してください（無人・確認不要・これ以外は何もしない）。
1) Read で '${cands}' を読む（会社の配列: company_name/url/phone）。
2) その配列を丸ごと opener-core の list_filter_exclude に records として渡して呼ぶ
   （多い場合は200件ずつに分け、kept と dropped をそれぞれ結合する）。
3) 戻りJSON（kept/dropped/stats を持つオブジェクト）を **そのままの構造で** Write で '${fres}' に保存し、
   『filtered: kept=N dropped=M』の1行だけ出力して終了。加工・要約・並べ替えをしない。"
  "$CLAUDE_BIN" -p "$fp" --allowedTools "Read" "Write" "mcp__opener-core__list_filter_exclude" \
    ${MODEL_FLAG[@]+"${MODEL_FLAG[@]}"} --max-turns 40 --no-session-persistence \
    >> "$LOG" 2>> "$ERR"

  if [[ -s "$fres" ]]; then
    "$PY_SHEETS" "$VERIFY_SCRIPT" apply "$SHEET_KEY" --state "$VERIFY_STATE" \
      --filter-result "$fres" >> "$LOG" 2>> "$ERR" \
      && log "検証: 今回追記分の照合を反映（営業不可は削除・手動送信要にstatus）" \
      || log "検証: 反映に失敗（行はそのまま）"
  else
    "$PY_SHEETS" "$VERIFY_SCRIPT" apply "$SHEET_KEY" --state "$VERIFY_STATE" \
      --unverified-status "要確認" >> "$LOG" 2>> "$ERR" \
      && log "🔴 検証: 照合できず→今回追記分に status='要確認' を付与（自動送信の対象外）" \
      || log "検証: 要確認の付与にも失敗"
  fi
  rm -f "$cands" "$VERIFY_STATE"
}

# 共通の許可ツール（①②③用・送信=playwrightは含めない）
BASE_TOOLS=( "Read" "Write" "Bash(python *)" "Bash(uv *)" "WebFetch" "WebSearch"
  "mcp__opener-core__get_skill_flow" "mcp__opener-core__list_build_queries"
  "mcp__opener-core__list_parse_jobposting" "mcp__opener-core__list_pick_official_url"
  "mcp__opener-core__list_filter_exclude" "mcp__opener-core__contact_detect"
  "mcp__opener-core__get_opener_prompt" )

case "$JOB" in
  prep)
    # ★並列リスト取り: config prep.parallel=true かつ claude host なら委譲。
    #   重い収集は子N本を並列・シートへの書き込みは親が1回に直列化（kick_prep_parallel.sh）。
    #   config 未設定(False)なら下の単一実行パスにそのまま落ちる＝既定挙動は不変。
    if [[ "$PREP_PARALLEL" == "True" && "$HOST" == "claude" ]]; then
      export REPO_ROOT SHEET_KEY CRITERIA PREP_COUNT MESSAGE_MODE HOST CLAUDE_BIN LOG ERR DRY MODEL
      export CONCURRENCY="$PREP_CONCURRENCY"
      bash "${REPO_ROOT}/.claude/skills/007-schedule-setup/scripts/kick_prep_parallel.sh"
      RC=$?
      [[ $RC -eq 0 ]] || fail "prep(parallel) exited $RC"
      reap_manual   # 手動送信要を別タブへ移送（並列経路）
      log "=== kick_sales prep end (parallel rc=0) ==="
      exit 0
    fi
    if [[ "$PREP_PARALLEL" == "True" && "$HOST" != "claude" ]]; then
      log "prep.parallel=true だが host=$HOST（並列は claude 限定）→ 単一実行にフォールバック"
    fi
    # ★実行レシピ(①②→message・送信手前で停止)は秘匿フロー schedule-run（サーバー）に閉じる。
    #   ここは「フローを取得して従え」だけの薄殻＝配布物に手順が出ない。
    ALLOWED=( "${BASE_TOOLS[@]}" )
    [[ $DRY -eq 0 ]] && verify_snapshot
    DRYNOTE=$([[ $DRY -eq 1 ]] && echo "これはドライラン。各工程は --preview のみ・シートへ書き込まず確認して終わること。" || echo "")
    PROMPT="あなたは simesapo-sales-auto-skills です。opener-core の get_skill_flow を {\"skill\":\"schedule-run\"} で呼び、返る手順に厳密に従って実行してください（無人実行・依頼確認は挟まない）。
パラメータ: sheet_key=${SHEET_KEY} / count=${PREP_COUNT} / message_mode=${MESSAGE_MODE} / criteria=${CRITERIA}
${DRYNOTE}
手順が定める安全弁（④送信は絶対にしない・message列まで用意して停止）を厳守し、最後にサマリを1メッセージで標準出力へ。"
    ;;
  send)
    ENGINE="$(read_cfg "['send'].get('engine','tier_a')")"
    CONCURRENCY="$(read_cfg "['send'].get('concurrency',3)")"; [[ "$CONCURRENCY" =~ ^[0-9]+$ ]] || CONCURRENCY=3
    if [[ "$SEND_MODE" == "auto" && $DRY -eq 0 && "$ENGINE" == "tier_b" ]]; then
      # ---- Tier B: AI並列ヘッドレスブラウザ（詳細は薄殻分離：kick_tierb.sh へ委譲）----
      #   送信手順/安全規則は秘匿フロー schedule-run-send（サーバー）に閉じ、ここは環境を渡して起動するだけ。
      export REPO_ROOT SHEET_KEY CAP CONCURRENCY HOST CLAUDE_BIN LOG ERR MODEL
      bash "${REPO_ROOT}/.claude/skills/007-schedule-setup/scripts/kick_tierb.sh"
      RC=$?
      [[ $RC -eq 0 ]] || fail "send(tier_b) exited $RC"
      log "=== kick_sales send end (tier_b rc=0) ==="
      exit 0
    elif [[ "$SEND_MODE" == "auto" && $DRY -eq 0 ]]; then
      # ★決定論の無人送信: AIエージェントに委ねず python を「同期・前景」で直接実行する。
      #   run_on_sheet.py → run_send.py が HTTP POST先行＋パターンマッチ(Stage1.5・noAI)で確実に送信し、
      #   AIブラウザ/reCAPTCHA/困難は 🟡assist_queue / 🔴manual_handoff へ振り分けて終了（人待ちハングなし）。
      #   ヘッドレスAIエージェント(claude -p)は送信をバックグラウンド化してターンを終える不具合があり0件送信になるため使わない。
      #   excluded / 手動送信要 / 営業禁止 / フォーム無 は run_on_sheet 側が既にスキップ。--force は付けない。
      PYBIN="${REPO_ROOT}/.claude/skills/005-form-send/.venv/bin/python"
      [[ -x "$PYBIN" ]] || PYBIN="$(command -v python3)"
      SEND_SCRIPT="${REPO_ROOT}/.claude/skills/005-form-send/scripts/run_on_sheet.py"
      # ★無人実行はヘッドレス必須（既定は表示モード=headless False。AUTOFORM_HEADLESS=1 で背景化）。
      #   対話の assist_mode.py はこの env を付けずに別途起動するので目視のまま（人がCAPTCHAを解ける）。
      log "send(determinstic python・headless): limit=${CAP} sheet=${SHEET_KEY}"
      AUTOFORM_HEADLESS=1 "$PYBIN" "$SEND_SCRIPT" "$SHEET_KEY" --limit "$CAP" >> "$LOG" 2>> "$ERR"
      RC=$?
      [[ $RC -eq 0 ]] || fail "send(python) exited $RC"
      # status を5バケツ（送信済み/要手動送信/要見直し/送信不可/除外）へ畳む（#49 status区別）。
      "$PYBIN" "${REPO_ROOT}/.claude/skills/005-form-send/scripts/tierb_relabel.py" "$SHEET_KEY" >> "$LOG" 2>> "$ERR" || true
      log "=== kick_sales send end (rc=0) ==="
      exit 0
    else
      # notify（既定）: 送信せず、未送信件数を数えて通知するだけ
      ALLOWED=( "Read" "Bash(python *)" )
      PROMPT="あなたは simesapo-sales-auto-skills です。送信はしないこと（送信ツールは与えていない）。005-form-send の run_on_sheet.py を --preview で回し、シート(キー: ${SHEET_KEY}) の『未送信で送信対象になる行数』を数え、『本日の送信候補は N 件です。中身を確認して手動送信してください』という短い要約だけ標準出力へ出して終了。"
    fi
    ;;
  *) fail "未知のjob: $JOB（prep|send）";;
esac

# 計測モード（テスト時だけ・既定オフ）: KICK_METRICS=1 で claude -p の出力をJSONにし、
# 実際のトークン使用量とコストをログに残す。通常運用では付けない（人間が読めるテキスト要約のまま）。
METRICS_FLAG=()
if [[ -n "${KICK_METRICS:-}" ]]; then
  METRICS_FLAG=(--output-format json)
  log "metrics = on（--output-format json：ログ末尾に usage/total_cost_usd が入る）"
fi

# 計測モード（テスト時だけ・既定オフ）: KICK_METRICS=1 で claude -p の出力をJSONにし、
# 実際のトークン使用量とコストをログに残す。通常運用では付けない（人間が読めるテキスト要約のまま）。
METRICS_FLAG=()
if [[ -n "${KICK_METRICS:-}" ]]; then
  METRICS_FLAG=(--output-format json)
  log "metrics = on（--output-format json：ログ末尾に usage/total_cost_usd が入る）"
fi

# ドル上限: budget_usd>0 のときだけ --max-budget-usd を付ける（0=無制限）。暴走保険は --max-turns。
BUDGET_FLAG=()
if awk "BEGIN{exit !(${PREP_BUDGET:-0}>0)}" 2>/dev/null; then
  BUDGET_FLAG=(--max-budget-usd "$PREP_BUDGET")
  log "budget cap = \$$PREP_BUDGET"
else
  log "budget cap = none (max-turns backstop only)"
fi

if [[ "$HOST" == "claude" ]]; then
  # ※ bash 3.2(macOS標準)＋set -u では空配列の "${arr[@]}" が unbound になるため ${arr[@]+...} で保護
  "$CLAUDE_BIN" -p "$PROMPT" \
    --allowedTools "${ALLOWED[@]}" \
    ${MODEL_FLAG[@]+"${MODEL_FLAG[@]}"} ${METRICS_FLAG[@]+"${METRICS_FLAG[@]}"} \
    --max-turns 600 ${BUDGET_FLAG[@]+"${BUDGET_FLAG[@]}"} --no-session-persistence \
    >> "$LOG" 2>> "$ERR"
  RC=$?
else
  # Codex（無人実行）。承認モードは config['codex_exec_flags']（既定 --full-auto＝無人で承認を挟まない）。
  # ツールは ~/.codex/config.toml の MCP サーバーから供給される＝Claude の --allowedTools のような
  # per-run ツール制限は無い。★prep の「送信ツール非許可＝構造的に送れない」保証は Codex では効かず、
  # プロンプト内の安全弁（④送信は絶対にしない）で担保する。--max-budget-usd 相当も無い。⚠️未実機検証。
  CODEX_FLAGS="$(read_cfg "['codex_exec_flags']")"; [[ -z "$CODEX_FLAGS" || "$CODEX_FLAGS" == "None" ]] && CODEX_FLAGS="--full-auto"
  "$CODEX_BIN" exec $CODEX_FLAGS "$PROMPT" >> "$LOG" 2>> "$ERR"
  RC=$?
fi
[[ $RC -eq 0 ]] || fail "$HOST $JOB run exited $RC"
# prep（単一/AIエージェント経路）成功後:
#   ① 今回追記された行だけを照合して掃除（営業不可を削除・手動送信要にstatus）
#   ② そのうえで手動送信要を別タブへ移送（順序が逆だと今回付けたstatusが移送されない）
if [[ "$JOB" == "prep" ]]; then
  [[ $DRY -eq 0 ]] && verify_appended
  reap_manual
fi
log "=== kick_sales $JOB end (rc=0) ==="
exit 0
