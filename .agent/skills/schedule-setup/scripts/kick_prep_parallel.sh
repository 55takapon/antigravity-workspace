#!/bin/bash
#
# kick_prep_parallel.sh — 並列prep（リスト収集①②）の実行部（kick_sales.sh prep から委譲）。
#
#   設計（送信の kick_tierb.sh のprep版）:
#     親: prep_shards.py で「エリア×業種」を N シャードに割る（日替わりローテーション＝供給拡張）。
#     子: N本の claude -p を背景並列起動。各子は担当1組だけを自分専用CSVに①収集→②contact抽出。
#         ★子はシートを一切触らない（Google Sheets へ書かない・run_on_sheet 系を呼ばない）。
#     親: 全子完了後、prep_merge_append.py が **1回だけ** マージ＋重複除去＋追記（壊れる所を直列化）。
#         最後に 004 merge_on_sheet.py が message をテンプレ差し込み（決定論・AI不要）。
#
#   ★重い所（収集・除外）は並列、壊れる所（同一シートへの書き込み）は直列＝速度を稼ぎつつ事故ゼロ。
#   ★claude host 限定（子が claude -p・opener-core ツールを使うため）。
#
# kick_sales.sh から export される: REPO_ROOT SHEET_KEY CRITERIA PREP_COUNT CONCURRENCY
#                                   MESSAGE_MODE EXCLUDE_TABS HOST CLAUDE_BIN LOG ERR DRY
#
set -uo pipefail

ts() { date "+%Y-%m-%d %H:%M:%S"; }
log() { echo "[$(ts)] $*" >> "${LOG:-/dev/stderr}"; }
die() { echo "[$(ts)] ERROR(prep-par): $*" >> "${ERR:-/dev/stderr}"; exit 1; }

[[ "${HOST:-}" == "claude" ]] || die "並列prepは claude host 限定（現在 host=${HOST:-?}）"
[[ -n "${REPO_ROOT:-}" && -d "$REPO_ROOT" ]] || die "REPO_ROOT 不正"
[[ -n "${SHEET_KEY:-}" ]] || die "SHEET_KEY 未設定"
[[ -x "${CLAUDE_BIN:-}" ]] || die "claude binary not found"
[[ "${CONCURRENCY:-}" =~ ^[0-9]+$ ]] || CONCURRENCY=6
COUNT="${PREP_COUNT:-150}"
CRITERIA="${CRITERIA:-}"
MESSAGE_MODE="${MESSAGE_MODE:-template}"
DRY="${DRY:-0}"
# 使用モデル（kick_sales.sh が config から解決して export）。空＝claude の既定モデルを継承。
MODEL_FLAG=()
[[ -n "${MODEL:-}" ]] && MODEL_FLAG=(--model "$MODEL")
# 計測モード（テスト時だけ・既定オフ）: KICK_METRICS=1 で子と照合ステップの出力をJSONにし、
# 各自の usage/total_cost_usd を集計してログに出す（誰がいくら使ったかが分かる）。
METRICS_FLAG=()
[[ -n "${KICK_METRICS:-}" ]] && METRICS_FLAG=(--output-format json)
# 空CSVだったシャードの再試行モデル（既定 sonnet）。RETRY_MODEL=off で再試行しない。
RETRY_MODEL="${RETRY_MODEL:-sonnet}"

SCRIPTS="${REPO_ROOT}/.claude/skills/007-schedule-setup/scripts"
# 直列python: sheets_io/gspread が要る（001の.venv）。004は004の.venv。純stdは shard割当のみ。
PY_STD="$(command -v python3)"
PY_SHEETS="${REPO_ROOT}/.claude/skills/001-list-extract/.venv/bin/python"; [[ -x "$PY_SHEETS" ]] || PY_SHEETS="$PY_STD"
PY_004="${REPO_ROOT}/.claude/skills/004-template-fill/.venv/bin/python"; [[ -x "$PY_004" ]] || PY_004="$PY_STD"

WORKDIR="$(mktemp -d)"
# 調査用に残したい時は PREP_KEEP_WORKDIR=1 を付ける（既定は掃除）。
[[ -n "${PREP_KEEP_WORKDIR:-}" ]] || trap 'rm -rf "$WORKDIR"' EXIT
log "=== kick_prep_parallel start (dry=$DRY, N=$CONCURRENCY, count=$COUNT, model=${MODEL:-継承}) workdir=$WORKDIR ==="

# ---- 1) シャード割当（決定論・都市シャード・日替わりローテーション）----
# 一時的に都市を指定したい時は PREP_CITIES="東京,横浜,..."（カンマ区切り）を渡す＝その都市だけで回す。
# PREP_SLOT を渡すと時刻でなく指定スロットを使う（別窓の都市群を取りたい時）。未指定は既定(15都市＋現在時刻slot)。
SHARD_OPT=()
[[ -n "${PREP_CITIES:-}" ]] && SHARD_OPT+=(--cities "$PREP_CITIES")
[[ -n "${PREP_SLOT:-}" ]] && SHARD_OPT+=(--slot "$PREP_SLOT")
if [[ -n "${PREP_SHARDS_JSON:-}" ]]; then
  # ★手書きのシャード定義を使う（都市×業種を自分で組みたい単発バッチ用）。
  #   形式は prep_shards.py の出力と同じ: {date,rotation_offset,shards,count,workers:[{i,city,scope,count,out_csv,task}]}
  #   out_csv は WORKDIR 配下に振り直す（渡されたパスは無視＝作業域の一貫性を保つ）。
  "$PY_STD" -c "
import json,sys,os
src,workdir,out = sys.argv[1],sys.argv[2],sys.argv[3]
d = json.load(open(src, encoding='utf-8'))
for w in d.get('workers', []):
    w['out_csv'] = os.path.join(workdir, 'worker_%d.csv' % w['i'])
json.dump(d, open(out,'w',encoding='utf-8'), ensure_ascii=False)
print('[shards] 手書き定義を使用: %s (workers=%d)' % (src, len(d.get('workers',[]))))
" "$PREP_SHARDS_JSON" "$WORKDIR" "$WORKDIR/shards.json" >> "$LOG" 2>> "$ERR" || die "シャード定義の読込失敗: $PREP_SHARDS_JSON"
else
  "$PY_STD" "$SCRIPTS/prep_shards.py" --count "$COUNT" --shards "$CONCURRENCY" \
    --workdir "$WORKDIR" --criteria "$CRITERIA" ${SHARD_OPT[@]+"${SHARD_OPT[@]}"} \
    --out "$WORKDIR/shards.json" >> "$LOG" 2>> "$ERR" \
    || die "shard 割当失敗"
fi
NWORK="$("$PY_STD" -c "import json,sys;print(len(json.load(open(sys.argv[1]))['workers']))" "$WORKDIR/shards.json" 2>/dev/null || echo 0)"
[[ "$NWORK" =~ ^[0-9]+$ && "$NWORK" -ge 1 ]] || die "worker数 不正: $NWORK"

# ---- 1.5) 既知会社スナップショット（★HPを開く前に捨てるための土台・決定論）----
# シート全タブ（作業タブ/既存提携先/要手動送信タブ…）に一度でも載った会社の照合キーだけを抜く。
# これを子に渡し、子は「候補が揃った時点で・HPを取りに行く前に」機械的に間引く。
# 失敗しても収集は止めない（KNOWN_JSON を空にする＝従来どおり全候補を追う。親のマージが最後に落とす）。
KNOWN_JSON="$WORKDIR/known.json"
if "$PY_SHEETS" "$SCRIPTS/known_companies.py" dump "$SHEET_KEY" --out "$KNOWN_JSON" \
     >> "$LOG" 2>> "$ERR"; then
  KNOWN_N="$("$PY_STD" -c "import json,sys;d=json.load(open(sys.argv[1]));print(d.get('size',0))" "$KNOWN_JSON" 2>/dev/null || echo 0)"
  log "既知会社スナップショット: 照合キー ${KNOWN_N}件 -> $KNOWN_JSON"
else
  log "既知会社スナップショット失敗（事前間引きなしで続行＝従来挙動）"
  KNOWN_JSON=""
fi

if [[ "$DRY" == "1" ]]; then
  log "DRY: シャード計画のみ（子は起動せず・シートへ書き込みなし）。"
  "$PY_STD" -c "import json,sys
d=json.load(open(sys.argv[1]))
print('[DRY] date=%s offset=%s shards=%s count=%s' % (d['date'],d['rotation_offset'],d['shards'],d['count']))
for w in d['workers']: print('  worker %d: %s 目標%d -> %s' % (w['i'],w['scope'],w['count'],w['out_csv']))
" "$WORKDIR/shards.json" >> "$LOG" 2>> "$ERR"
  log "=== kick_prep_parallel end (dry) ==="
  exit 0
fi

# 子の許可ツール（収集①②用・シート書き込み系は含めない＝①はCSVのみ）。
# ★python は "python" と "python3" 両方許可（Bash(python *) は python3 にマッチしないため両方明記）。
CHILD_TOOLS=( "Read" "Write" "Bash(python *)" "Bash(python3 *)" "Bash(uv *)" "WebFetch" "WebSearch"
  "mcp__opener-core__get_skill_flow" "mcp__opener-core__list_build_queries"
  "mcp__opener-core__list_parse_jobposting" "mcp__opener-core__list_pick_official_url"
  "mcp__opener-core__list_filter_exclude" "mcp__opener-core__contact_detect" )

# ---- 2) 子をN本 背景並列起動（各自 worker_i.csv に①②）----
PIDS=(); IDXS=()
for i in $(seq 1 "$NWORK"); do
  IFS=$'\t' read -r CITY WCNT OUTCSV < <("$PY_STD" -c "import json,sys
w=json.load(open(sys.argv[1]))['workers'][int(sys.argv[2])-1]
print(w['city'],w['count'],w['out_csv'],sep='\t')" "$WORKDIR/shards.json" "$i")
  CLOG="$WORKDIR/child_${i}.log"
  CANDJSON="$WORKDIR/cand_${i}.json"; KEPTJSON="$WORKDIR/kept_${i}.json"
  # シャード定義に task があれば「1) ①収集」の中身をそれで置き換える（単発バッチで経路を変えたい時）。
  WTASK="$("$PY_STD" -c "import json,sys
w=json.load(open(sys.argv[1]))['workers'][int(sys.argv[2])-1]
sys.stdout.write(w.get('task') or '')" "$WORKDIR/shards.json" "$i")"
  if [[ -n "$WTASK" ]]; then
    COLLECT_STEP=" 1) ①収集: ${WTASK}
    公式URLは list_pick_official_url で解決してよい。
    除外は list_filter_exclude を必ず通すこと。判定の反映（★重要・厳守）:
      - no_contact（営業不可）と 既存提携先(partner) は **CSVに書かない**（＝除外・落とす）。
      - 手動送信要(manual) は **CSVに残し、status列に「手動送信要」と記入**（落とさない）。"
  else
    COLLECT_STEP=" 1) ①収集: 上記スコープに絞ったクエリ（list_build_queries）で求人媒体から今 募集中の会社を探し、
    list_parse_jobposting / list_pick_official_url で公式URLを解決。
    除外は list_filter_exclude を必ず通すこと。判定の反映（★重要・厳守）:
      - no_contact（営業不可）と 既存提携先(partner) は **CSVに書かない**（＝除外・落とす）。
      - 手動送信要(manual) は **CSVに残し、status列に「手動送信要」と記入**（落とさない・後段が手動タブへ移送する）。"
  fi
  # 既知会社の事前間引き手順（known.json がある時だけ子に指示する。無ければ従来どおり）
  if [[ -n "$KNOWN_JSON" ]]; then
    SCREEN_STEP=" 1.5) ★事前間引き（HPを取りに行く前に必ず・トークン節約の要）: 1)で集めた候補を
    JSON配列 '${CANDJSON}'（各要素 {\"company_name\":\"…\",\"url\":\"…\"}・社名不明なら空文字でよい）に Write し、
    \`${PY_SHEETS} ${SCRIPTS}/known_companies.py screen --known ${KNOWN_JSON} --in ${CANDJSON} --out ${KEPTJSON}\`
    を実行。**残った '${KEPTJSON}' の社だけ**を以降（ページ取得・解析・②）の対象にする。
    ここで落ちた社は既にシートに在る＝送っても無駄なので、二度と取りに行かないこと。
    公式URLが後から確定した社が増えたら、その分だけ同じ screen をもう一度通してから② へ進む。"
  else
    SCREEN_STEP=""
  fi

  PROMPT="あなたは simesapo-sales-auto-skills の収集ワーカー(${i})です（無人・依頼確認なし）。
担当都市: 「${CITY}」（★この都市に所在する会社だけ・他の都市は集めない）。目標 ${WCNT} 件。方針: ${CRITERIA}
クエリには必ず地名「${CITY}」を含め、${CITY} の会社に地理的に絞ること。頭脳は opener-core ツール。手順:
${COLLECT_STEP}
${SCREEN_STEP}
 2) ②抽出: 各社HPから contact_detect で contact_url を確定。
 実装は自由（opener-core ツール＋WebFetch＋Write で直接CSVを組んでよい。002/001 のローカルpython
 スクリプト＝extract_contact_pages.py 等を使ってもよいが必須ではない）。速く確実な方を選べ。
出力: 必ず CSV『${OUTCSV}』へ保存（列は company_name,url,address,phone,maps_url,contact_url,status の順・ヘッダ付き。
      status は手動送信要の社だけ「手動送信要」・それ以外は空）。
★出力の書き方（最重要・ここを外すと全作業が無駄になる）: **最後にまとめて書こうとしないこと**。
  1社でも確定したら すぐ CSV を書き（ヘッダ＋その1行）、以降は確定するたびに追記して更新する。
  調査の途中で終わっても、その時点までの結果がCSVに残っている状態を常に保つこと。
★厳守: あなたはシートを持たない。Google Sheets へは絶対に書かない・run_on_sheet 系は呼ばない・出力はこのCSVだけ。
★件数の扱い（重要・コスト直結）: ${WCNT} は上限つきの目安であって必達ノルマではない。
  候補は最初の検索でまとめて多め（目安 目標の2〜3倍）に集め、間引きは上記の機械処理に任せる。
  間引き後に ${WCNT} へ届かなくても、クエリを言い換えての追い込み収集（同じ都市の再探索ループ）はしない。
  1パスで終え、最後の報告に『目標${WCNT}に対し実収集○件』と書けばよい。
最後に『worker ${i}: 収集○件 / contact付与△件 / out=${OUTCSV}』の1行を標準出力へ。"

  ( "$CLAUDE_BIN" -p "$PROMPT" \
      --allowedTools "${CHILD_TOOLS[@]}" \
      ${MODEL_FLAG[@]+"${MODEL_FLAG[@]}"} ${METRICS_FLAG[@]+"${METRICS_FLAG[@]}"} \
      --max-turns 400 --no-session-persistence \
      >> "$CLOG" 2>&1 ) &
  # 再試行で同じプロンプトを使えるよう保存（空CSVだったシャードだけ後で回す）
  printf '%s' "$PROMPT" > "$WORKDIR/prompt_${i}.txt"
  PIDS+=("$!"); IDXS+=("$i")
  log "worker $i 起動: ${CITY} 目標${WCNT} pid=$! log=$CLOG"
done

# ---- 3) 全子完了待ち ----
FAILED=0
for k in "${!PIDS[@]}"; do
  pid="${PIDS[$k]}"; idx="${IDXS[$k]}"
  if wait "$pid"; then rc=0; else rc=$?; fi
  if [[ $rc -ne 0 ]]; then
    FAILED=$((FAILED+1)); log "worker $idx 異常終了 rc=$rc（child log 末尾↓）"
    tail -n 6 "$WORKDIR/child_${idx}.log" >> "$ERR" 2>/dev/null || true
  else
    log "worker $idx 完了"
  fi
done

# ---- 4) 収集結果の検証（各worker CSV 行数）----
TOTAL_ROWS=0
for i in $(seq 1 "$NWORK"); do
  f="$WORKDIR/worker_${i}.csv"
  if [[ -s "$f" ]]; then
    n="$("$PY_STD" -c "import csv,sys;print(sum(1 for _ in csv.DictReader(open(sys.argv[1],encoding='utf-8-sig'))))" "$f" 2>/dev/null || echo 0)"
  else n=0; fi
  TOTAL_ROWS=$((TOTAL_ROWS+n)); log "worker $i CSV: ${n}行"
done
log "子CSV合計 ${TOTAL_ROWS}行（失敗worker=$FAILED / N=$NWORK）"

# ---- 4.5) ★空CSVのシャードを1回だけ再試行 ----
# 2026-08-04のToBバッチ3で、8本中3本が「調査はしたのにCSVを書かずに終了」した（haiku）。
# 異常終了ではないので検知されず、そのシャード分(約57社)の作業がまるごと消えた。
# 出力が空＝契約不履行として扱い、上位モデルで1回だけやり直す（RETRY_MODEL=off で無効）。
EMPTY=()
for i in $(seq 1 "$NWORK"); do [[ -s "$WORKDIR/worker_${i}.csv" ]] || EMPTY+=("$i"); done
if [[ ${#EMPTY[@]} -gt 0 && "$RETRY_MODEL" != "off" ]]; then
  log "空CSVのシャード ${#EMPTY[@]}本 (${EMPTY[*]}) を model=${RETRY_MODEL} で再試行"
  RPIDS=()
  for i in "${EMPTY[@]}"; do
    RPROMPT="$(cat "$WORKDIR/prompt_${i}.txt")
★これは再試行です。前回は調査だけして CSV を書かずに終了しました。
  **最優先事項は『${WORKDIR}/worker_${i}.csv』を必ず書くこと**。件数が目標に満たなくてもよいので、
  1社でも確定したら先にCSVへ書き、その後で追加を書き足すこと（最後にまとめて書こうとしない）。"
    ( "$CLAUDE_BIN" -p "$RPROMPT" \
        --allowedTools "${CHILD_TOOLS[@]}" \
        --model "$RETRY_MODEL" ${METRICS_FLAG[@]+"${METRICS_FLAG[@]}"} \
        --max-turns 400 --no-session-persistence \
        >> "$WORKDIR/child_${i}_retry.log" 2>&1 ) &
    RPIDS+=("$!"); log "  retry worker $i 起動 pid=$!"
  done
  for pid in "${RPIDS[@]}"; do wait "$pid" || true; done
  RETRY_ROWS=0
  for i in "${EMPTY[@]}"; do
    if [[ -s "$WORKDIR/worker_${i}.csv" ]]; then
      n="$("$PY_STD" -c "import csv,sys;print(sum(1 for _ in csv.DictReader(open(sys.argv[1],encoding='utf-8-sig'))))" "$WORKDIR/worker_${i}.csv" 2>/dev/null || echo 0)"
      RETRY_ROWS=$((RETRY_ROWS+n)); log "  retry worker $i: ${n}行 回収"
    else
      log "  retry worker $i: 再試行でも空（このシャードは諦める）"
    fi
  done
  TOTAL_ROWS=$((TOTAL_ROWS+RETRY_ROWS))
  log "再試行で ${RETRY_ROWS}行 追加（子CSV合計 ${TOTAL_ROWS}行）"
fi

if [[ "$TOTAL_ROWS" -eq 0 ]]; then
  log "収集ゼロ。追記スキップして終了。"
  log "=== kick_prep_parallel end (rc=0・収集0) ==="
  exit 0
fi

# ---- 5) ★親が1回まとめてサーバー照合 → 直列マージ＋1回追記（ここだけがシートに書く）----
WS_OPT=()
[[ -n "${TARGET_WORKSHEET:-}" ]] && WS_OPT=(--worksheet "$TARGET_WORKSHEET")

# 5-a) 候補を書き出す（重複除去済み・まだ追記しない）
CANDS="$WORKDIR/merged_candidates.json"
"$PY_SHEETS" "$SCRIPTS/prep_merge_append.py" "$SHEET_KEY" --manifest "$WORKDIR/shards.json" \
  ${WS_OPT[@]+"${WS_OPT[@]}"} --export-candidates "$CANDS" >> "$LOG" 2>> "$ERR" \
  || die "候補の書き出し失敗"

# 5-b) サーバー照合（営業不可を落とす／手動送信要に status を付ける）。
#   ★子に任せると飛ばされる（2026-08-04 ToBバッチ3で営業不可3社が素通り）。親が1回だけ通す。
#   会話は「ファイルを読む→ツールを1回呼ぶ→書く」だけ＝短く安い。ツールも1つしか許可しない。
FILTERED="$WORKDIR/filter_result.json"
FILTER_PROMPT="次を厳密に実行してください（無人・確認不要・これ以外は何もしない）。
1) Read で '${CANDS}' を読む（会社の配列: company_name/url/phone）。
2) その配列を丸ごと opener-core の list_filter_exclude に records として渡して1回だけ呼ぶ。
   （多い場合は200件ずつに分けて複数回呼び、kept と dropped をそれぞれ結合する）
3) 戻りJSON（kept/dropped/stats を持つオブジェクト）を **そのままの構造で** Write で '${FILTERED}' に保存する。
   加工・要約・並べ替えをしない。保存したら『filtered: kept=N dropped=M』の1行だけ出力して終了。"
if "$CLAUDE_BIN" -p "$FILTER_PROMPT" \
     --allowedTools "Read" "Write" "mcp__opener-core__list_filter_exclude" \
     ${MODEL_FLAG[@]+"${MODEL_FLAG[@]}"} ${METRICS_FLAG[@]+"${METRICS_FLAG[@]}"} \
     --max-turns 40 --no-session-persistence >> "$WORKDIR/filter.log" 2>&1 \
   && [[ -s "$FILTERED" ]]; then
  log "サーバー照合 完了 -> $FILTERED"
  FILTER_OPT=(--apply-filter "$FILTERED")
else
  log "🔴 サーバー照合に失敗。未照合のまま送らせないため status='要確認' を付けて追記する"
  FILTER_OPT=(--unverified-status "要確認")
fi

# 5-c) 照合結果を反映して追記
"$PY_SHEETS" "$SCRIPTS/prep_merge_append.py" "$SHEET_KEY" --manifest "$WORKDIR/shards.json" \
  ${WS_OPT[@]+"${WS_OPT[@]}"} "${FILTER_OPT[@]}" >> "$LOG" 2>> "$ERR" || die "マージ追記失敗"

# ---- 6) message を1回（004テンプレ差し込み・決定論）----
if [[ "$MESSAGE_MODE" == "none" ]]; then
  log "message_mode=none（営業文の差し込みはしない＝収集のみのバッチ）"
elif [[ "$MESSAGE_MODE" == "template" ]]; then
  "$PY_004" "${REPO_ROOT}/.claude/skills/004-template-fill/scripts/merge_on_sheet.py" "$SHEET_KEY" \
    >> "$LOG" 2>> "$ERR" || die "004 message 差し込み失敗"
else
  log "message_mode=${MESSAGE_MODE}（並列prep v1は template のみ自動。ai冒頭文は別途③実行が必要）"
fi

# ---- 7) ★手動送信要の自動仕分け（指示なしでも）: status=手動送信要 の行を専用タブへ移送 ----
#   子が list_filter_exclude 判定で status に「手動送信要」を記入 → ここで自動的にタブへ退避し、
#   ④自動送信の対象から外す。--status-values を「手動送信要」だけに限定＝送信段の「要手動送信（試行後）」を誤移送しない。
REAP_OPT=()
[[ -n "${TARGET_WORKSHEET:-}" ]] && REAP_OPT=(--source-worksheet "$TARGET_WORKSHEET")
if [[ "${SKIP_REAP:-}" == "1" ]]; then
  log "reap: スキップ（SKIP_REAP=1）"
else
  "$PY_SHEETS" "${SCRIPTS}/prep_reap_manual.py" "$SHEET_KEY" --status-values 手動送信要 \
    ${REAP_OPT[@]+"${REAP_OPT[@]}"} >> "$LOG" 2>> "$ERR" || log "reap: 手動送信要の移送 rc≠0（追記は成功のまま・行は残置）"
fi

# ---- 8) トークン/コスト集計（KICK_METRICS=1 のときだけ）----
if [[ -n "${KICK_METRICS:-}" ]]; then
  "$PY_STD" - "$WORKDIR" >> "$LOG" 2>> "$ERR" <<'PYEOF'
import json, re, sys, glob, os
wd = sys.argv[1]
def usage_of(path):
    try: t = open(path, encoding="utf-8", errors="replace").read()
    except OSError: return None
    dec = json.JSONDecoder()
    for m in reversed(list(re.finditer(r"\{", t))):
        try: o, _ = dec.raw_decode(t[m.start():])
        except ValueError: continue
        if isinstance(o, dict) and "usage" in o: return o
    return None
rows, tot_tok, tot_cost = [], 0, 0.0
for f in sorted(glob.glob(os.path.join(wd, "child_*.log")) + glob.glob(os.path.join(wd, "filter.log"))):
    o = usage_of(f)
    if not o: continue
    u = o.get("usage", {}) or {}
    tk = sum(u.get(k, 0) for k in ("input_tokens","output_tokens",
                                   "cache_read_input_tokens","cache_creation_input_tokens"))
    cost = o.get("total_cost_usd") or 0.0
    tot_tok += tk; tot_cost += cost
    rows.append((os.path.basename(f), o.get("num_turns", "?"), tk, cost))
if rows:
    print("=== トークン計測（並列prep）===")
    for name, turns, tk, cost in rows:
        print(f"  {name:<24} turns={turns:<4} tokens={tk:>10,}  ${cost:.4f}")
    print(f"  {'合計':<24} {'':<9} tokens={tot_tok:>10,}  ${tot_cost:.4f}")
PYEOF
fi
log "=== kick_prep_parallel end (rc=0・workers=$NWORK rows=$TOTAL_ROWS failed=$FAILED) ==="
exit 0
