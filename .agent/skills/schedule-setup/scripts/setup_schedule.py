#!/usr/bin/env python3
"""
007-schedule-setup — 配布用スケジューラ・セットアップの中核（DRAFT / 雛形）

営業パイプラインの定期実行を、ユーザーのPCへ登録/変更/解除する。
設計の真実の源: ~/.simesapo-sales/schedule.json（このスクリプトが読み書き）。
スケジューラ登録は設定から毎回レンダリングする（手編集させない）。

OS分岐:
  - macOS  : launchd（~/Library/LaunchAgents/*.plist ＋ launchctl bootstrap）
  - Windows: Task Scheduler（schtasks）

ジョブ2本:
  - prep : ①②③（毎日・送信しない）。message列まで用意して停止。
  - send : ④送信。send_mode = notify（通知のみ・既定） / auto（自動送信）。

使い方（SKILL.md がヒアリング結果を渡して呼ぶ）:
  setup_schedule.py show
  setup_schedule.py set  --prep-time 08:30 --prep-days daily \
                         --send-time 14:00 --send-days weekdays --send-mode notify --cap 100 \
                         [--criteria "..."] [--sheet-key KEY] [--notify-channel ID]
  setup_schedule.py apply     # schedule.json からスケジューラへ登録/更新
  setup_schedule.py remove    # スケジューラ登録を解除（設定は残す）
  setup_schedule.py verify    # 登録状態を一覧表示

★このファイルは master 専用の雛形。promote 時はロジックをサーバーへ寄せ、配布は薄殻＋トークン接続にする。
"""
from __future__ import annotations
import argparse, json, os, platform, subprocess, sys
from pathlib import Path

HOME = Path.home()
CONFIG_DIR = HOME / ".simesapo-sales"
CONFIG_PATH = CONFIG_DIR / "schedule.json"
SCRIPT_DIR = Path(__file__).resolve().parent
# リポジトリルート（.claude/skills/007-schedule-setup/scripts から4つ上）
REPO_ROOT = SCRIPT_DIR.parents[3]

LABEL_PREFIX = "com.claude.simesapo-sales"      # launchd Label / schtasks 名の接頭辞
DEFAULT_CRITERIA = "求人媒体から『今 求人を出している（直近2週間の新着）』Web制作・Webマーケ会社を、各社の自社採用ページ経由で新規収集"

DEFAULTS = {
    "timezone": "Asia/Tokyo",
    "repo_root": str(REPO_ROOT),
    # 無人実行のホスト。auto=claude優先→codex / claude / codex。kick_sales が参照する。
    "host": "auto",
    # Codex無人実行の承認モード（kick_sales が codex exec に渡す）。--full-auto=承認を挟まない。
    "codex_exec_flags": "--full-auto",
    "sheet_key": "",
    # 無人実行で使うモデル（claude -p --model に渡る）。空＝ユーザーのグローバル既定を継承。
    #   ★未指定だと「普段づかいの既定モデル」がそのまま夜間の自動実行に効く＝高額既定の人は毎晩高い。
    #   例: "sonnet"（収集は探索と決定論処理が主・十分）。prep/send 側に model を置けばジョブ別に上書き。
    "model": "",
    "criteria": DEFAULT_CRITERIA,
    "notify_channel_id": "",
    # time は単一時刻。1日複数回は times:["08:00","14:00"]（times があれば time より優先）。
    # message_mode: "ai"=③003冒頭文生成 / "template"=004固定文＋会社名差し替え（③を飛ばす）
    # parallel: True=並列リスト取り（担当を分けたN本を同時に走らせ、書き込みは親が1回にまとめる）。
    #   件数を一度に多く取りたいときの opt-in。既定 False＝従来どおり1本で順に処理（安全・低コスト）。
    #   concurrency=同時に走らせる本数。claude 環境限定。
    "prep": {"time": "08:30", "days": "daily", "count": 100, "budget_usd": 0, "message_mode": "ai",
             "parallel": False, "concurrency": 4},
    # mode: notify | auto。engine は mode=auto のときの送信方式:
    #   tier_a = 決定論python直実行（安全・ほぼ0トークン・送信率控えめ・既定）
    #   tier_b = AI並列ブラウザ（高送信率・プラントークン消費・要ブラウザN台・claude host限定）
    # concurrency = tier_b の並列ブラウザ台数（PCスペック依存＝preflight の推奨値をヒアリングで確定）
    "send": {"time": "14:00", "days": "weekdays", "mode": "notify", "cap": 100,
             "engine": "tier_a", "concurrency": 3},
}


# ------------------------------------------------------------------ config I/O
def load_config() -> dict:
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        # 欠損キーは既定で補完（前方互換）
        merged = json.loads(json.dumps(DEFAULTS))
        merged.update({k: v for k, v in cfg.items() if k not in ("prep", "send")})
        merged["prep"].update(cfg.get("prep", {}))
        merged["send"].update(cfg.get("send", {}))
        return merged
    return json.loads(json.dumps(DEFAULTS))


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def _hhmm(s: str) -> tuple[int, int]:
    h, m = s.split(":")
    h, m = int(h), int(m)
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"時刻が不正: {s}")
    return h, m


# ------------------------------------------------------------------ platform
def current_os() -> str:
    s = platform.system()
    return {"Darwin": "macos", "Windows": "windows"}.get(s, "unsupported")


# ------------------------------------------------------------------ Tier B: 並列台数の推奨 / preflight
def _detect_ram_gb() -> float | None:
    """総RAM(GB)をOS非依存のベストエフォートで取得。取れなければ None。"""
    try:
        osname = current_os()
        if osname == "macos":
            out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
            return int(out.stdout.strip()) / (1024 ** 3)
        if platform.system() == "Linux":
            for ln in Path("/proc/meminfo").read_text().splitlines():
                if ln.startswith("MemTotal:"):
                    return int(ln.split()[1]) / (1024 ** 2)  # kB → GB
        if osname == "windows":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            ms = MS(); ms.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
            return ms.ullTotalPhys / (1024 ** 3)
    except Exception:
        return None
    return None


def recommend_concurrency() -> dict:
    """RAM/CPU から Tier B の並列台数を推奨。1台のヘッドレスChromium≒0.7GB、律速はRAM。
    返り値: {recommended, ceiling, ram_gb, cores, note}"""
    ram = _detect_ram_gb()
    cores = os.cpu_count() or 2
    if ram is None:
        return {"recommended": 2, "ceiling": 3, "ram_gb": None, "cores": cores,
                "note": "RAM検出不可のため保守的な既定。手動で --send-concurrency 指定を推奨。"}
    hard_cap = 8  # 実運用の上限（モニター実績＝8並列）
    ceiling = max(1, min(int((ram * 0.4) // 0.7), cores, hard_cap))
    recommended = max(2, min(ceiling, cores // 2)) if ceiling >= 2 else 1
    return {"recommended": recommended, "ceiling": ceiling, "ram_gb": round(ram, 1),
            "cores": cores, "note": f"RAM {ram:.0f}GB / {cores}コア → 推奨{recommended}台・上限{ceiling}台"}


def _which(name: str) -> str | None:
    import shutil
    p = shutil.which(name)
    if p:
        return p
    for c in (HOME / ".nodebrew/current/bin" / name, HOME / ".npm-global/bin" / name,
              Path("/usr/local/bin") / name, Path("/opt/homebrew/bin") / name):
        if c.exists() and os.access(c, os.X_OK):
            return str(c)
    return None


def preflight(cfg: dict) -> int:
    """Tier B 無人並列送信の前提チェック（reproducibility ゲート）。go/no-go と推奨Nを表示。"""
    print("=== Tier B 並列送信 preflight ===")
    ok = True

    osname = current_os()
    if osname == "macos":
        print("  [OK] OS = macOS（launchd・検証済）")
    elif osname == "windows":
        print("  [WARN] OS = Windows（schtasks・Tier Bは未実機検証。tier_a 推奨）")
    else:
        print(f"  [NG] OS = {platform.system()}（未対応）"); ok = False

    # 1) インタプリタ検出（★python無しpython3のみ問題＝書き戻し全滅の真因を先に潰す）
    py = _which("python3") or _which("python")
    if py:
        print(f"  [OK] python インタプリタ = {py}")
    else:
        print("  [NG] python3/python が見つからない（書き戻し不可）"); ok = False

    # 2) claude CLI（tier_b は claude host 限定：MCPを --mcp-config で渡すため）
    claude = _which("claude")
    if claude:
        print(f"  [OK] claude CLI = {claude}")
    else:
        print("  [NG] claude CLI が見つからない（tier_b は claude 必須）"); ok = False
    host = cfg.get("host", "auto")
    if host == "codex":
        print("  [NG] host=codex は tier_b 非対応（MCPをper-runで渡せない）。host=claude/auto に。"); ok = False

    # 3) playwright MCP（npx 経由・chromium）
    npx = _which("npx")
    if npx:
        print(f"  [OK] npx = {npx}（@playwright/mcp を起動）")
        print("       ※初回は chromium 未導入だと失敗。未導入なら `npx playwright install chromium` を実行。")
    else:
        print("  [NG] npx が見つからない（@playwright/mcp を起動できない）"); ok = False

    # 4) サービスアカウント鍵（シート読み書き＝シャード生成/書き戻し）
    sa = REPO_ROOT / "shared" / "gcp_service_account.json"
    print(f"  [{'OK' if sa.exists() else 'NG'}] サービスアカウント鍵 = {sa}")
    ok = ok and sa.exists()

    # 5) RAM→並列台数の推奨
    rec = recommend_concurrency()
    print(f"  [i] {rec['note']}")
    cur_n = cfg.get("send", {}).get("concurrency", 3)
    print(f"      現在の設定 concurrency={cur_n}")

    # 6) トークンの注意
    print("  [i] Tier B はプラントークンを消費（Tier A はほぼ0）。小さいプランは3回/日×N本で"
          "レート上限に当たり得る（到達時はabortで可視）。")

    print(f"\n判定: {'GO ✅（tier_b 実行可）' if ok else 'NO-GO ❌（上の NG を解消）'}")
    print(f"推奨: python3 .../setup_schedule.py set --send-mode auto --send-engine tier_b "
          f"--send-concurrency {rec['recommended']}")
    return 0 if ok else 2


# ------------------------------------------------------------------ macOS (launchd)
def effective_model(cfg: dict, job: str) -> str:
    """そのジョブが実際に使うモデル名（kick_sales.sh の解決規則と同じ: ジョブ別 → 全体 → 継承）。"""
    m = (cfg.get(job, {}).get("model") or "").strip() or (cfg.get("model") or "").strip()
    return m or "（未指定＝グローバル既定を継承）"


def job_times(jc: dict) -> list[str]:
    """時刻リストを返す。times があればそれ、無ければ [time]。"""
    return list(jc["times"]) if jc.get("times") else [jc.get("time", "08:30")]


def _plist(job: str, cfg: dict) -> str:
    jc = cfg[job]
    days = jc.get("days", "daily")
    kick = SCRIPT_DIR / "kick_sales.sh"
    weekdays = list(range(1, 6)) if days == "weekdays" else [None]
    # StartCalendarInterval: 時刻×曜日の総当たりを1配列に（複数回/複数曜日をまとめて表現）
    entries = []
    for t in job_times(jc):
        h, m = _hhmm(t)
        for wd in weekdays:
            wdk = f"<key>Weekday</key><integer>{wd}</integer>" if wd is not None else ""
            entries.append(f"        <dict><key>Hour</key><integer>{h}</integer>"
                           f"<key>Minute</key><integer>{m}</integer>{wdk}</dict>")
    if len(entries) == 1:
        cal = "    <key>StartCalendarInterval</key>\n    " + entries[0].strip()
    else:
        cal = "    <key>StartCalendarInterval</key>\n    <array>\n" + "\n".join(entries) + "\n    </array>"
    logdir = HOME / "Library" / "Logs"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LABEL_PREFIX}-{job}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{kick}</string>
        <string>{job}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{cfg['repo_root']}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:{HOME}/.nodebrew/current/bin</string>
        <key>HOME</key>
        <string>{HOME}</string>
    </dict>
{cal}
    <key>StandardOutPath</key>
    <string>{logdir}/claude-sales-{job}.log</string>
    <key>StandardErrorPath</key>
    <string>{logdir}/claude-sales-{job}-error.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
"""


def macos_apply(cfg: dict, jobs=("prep", "send")) -> None:
    la = HOME / "Library" / "LaunchAgents"
    la.mkdir(parents=True, exist_ok=True)
    uid = os.getuid()
    for job in jobs:
        label = f"{LABEL_PREFIX}-{job}"
        pl = la / f"{label}.plist"
        pl.write_text(_plist(job, cfg), encoding="utf-8")
        # 既存を外してから入れ直す（更新反映）
        subprocess.run(["launchctl", "bootout", f"gui/{uid}/{label}"],
                       capture_output=True)  # 未登録なら失敗するが無視
        r = subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(pl)],
                           capture_output=True, text=True)
        status = "OK" if r.returncode == 0 else f"WARN({r.returncode}): {r.stderr.strip()}"
        print(f"[macos] {label}: {pl}  bootstrap={status}")


def macos_remove() -> None:
    la = HOME / "Library" / "LaunchAgents"
    uid = os.getuid()
    for job in ("prep", "send"):
        label = f"{LABEL_PREFIX}-{job}"
        subprocess.run(["launchctl", "bootout", f"gui/{uid}/{label}"], capture_output=True)
        pl = la / f"{label}.plist"
        if pl.exists():
            pl.unlink()
        print(f"[macos] removed {label}")


def macos_verify() -> None:
    r = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    hits = [ln for ln in r.stdout.splitlines() if LABEL_PREFIX in ln]
    print("[macos] 登録中のジョブ:")
    print("\n".join(hits) if hits else "  (なし)")


# ------------------------------------------------------------------ Windows (schtasks)  ※雛形・要実地検証
def _schtasks_args(job: str, cfg: dict, tindex: int = 0) -> list[str]:
    times = job_times(cfg[job])
    h, m = _hhmm(times[tindex])
    st = f"{h:02d}:{m:02d}"
    days = cfg[job]["days"]
    kick = SCRIPT_DIR / "kick_sales.ps1"
    tr = f'powershell -NoProfile -ExecutionPolicy Bypass -File "{kick}" {job}'
    tn = f"{LABEL_PREFIX}-{job}"
    base = ["schtasks", "/Create", "/F", "/TN", tn, "/TR", tr, "/ST", st, "/RL", "LIMITED"]
    if days == "weekdays":
        base += ["/SC", "WEEKLY", "/D", "MON,TUE,WED,THU,FRI"]
    else:
        base += ["/SC", "DAILY"]
    return base


def windows_apply(cfg: dict, jobs=("prep", "send")) -> None:
    for job in jobs:
        # 1日複数回は時刻ごとにタスクを作る（TN に _1,_2… を付与）
        for ti, _t in enumerate(job_times(cfg[job])):
            tn_suffix = "" if ti == 0 else f"_{ti+1}"
            args = _schtasks_args(job, cfg, ti)
            # TN を時刻連番に差し替え
            args[args.index("/TN") + 1] = f"{LABEL_PREFIX}-{job}{tn_suffix}"
            r = subprocess.run(args, capture_output=True, text=True)
            status = "OK" if r.returncode == 0 else f"WARN({r.returncode}): {r.stderr.strip()}"
            print(f"[windows] {LABEL_PREFIX}-{job}{tn_suffix} @{_t}: {status}")
    print("[windows] ※スリープ中も実行したい場合はタスクのプロパティで 'Wake the computer to run this task' を有効化")


def windows_remove() -> None:
    for job in ("prep", "send"):
        for suffix in ("", "_2", "_3", "_4"):
            tn = f"{LABEL_PREFIX}-{job}{suffix}"
            subprocess.run(["schtasks", "/Delete", "/F", "/TN", tn], capture_output=True)
        print(f"[windows] removed {LABEL_PREFIX}-{job}*")


def windows_verify() -> None:
    r = subprocess.run(["schtasks", "/Query", "/TN", LABEL_PREFIX + "-prep"], capture_output=True, text=True)
    print(r.stdout or r.stderr)


# ------------------------------------------------------------------ dispatch
def do_apply(cfg: dict, jobs=("prep", "send")) -> int:
    osname = current_os()
    if osname == "macos":
        macos_apply(cfg, jobs)
    elif osname == "windows":
        windows_apply(cfg, jobs)
    else:
        print(f"未対応OS: {platform.system()}（Mac/Windowsのみ対応）", file=sys.stderr)
        return 2
    pt = ", ".join(job_times(cfg["prep"]))
    mm = cfg["prep"].get("message_mode", "ai")
    msg_label = "テンプレ004(固定文)" if mm == "template" else "AI③(冒頭文生成)"
    sc = cfg["send"]
    eng = sc.get("engine", "tier_a")
    eng_label = eng
    if sc["mode"] == "auto":
        eng_label = f"{eng}" + (f"(並列{sc.get('concurrency', 3)}台)" if eng == "tier_b" else "(決定論)")
    print(f"\n設定: {CONFIG_PATH}")
    par = cfg["prep"].get("parallel")
    par_label = f" / 並列{cfg['prep'].get('concurrency', 4)}本" if par else ""
    print(f"  prep: [{pt}] / {cfg['prep']['days']} / message={msg_label} / count={cfg['prep'].get('count')}{par_label}（送信しない）")
    print(f"  send: {', '.join(job_times(sc))} / {sc['days']} / mode={sc['mode']}"
          f"{' / engine=' + eng_label if sc['mode'] == 'auto' else ''} / cap={sc['cap']}")
    print(f"  model: prep={effective_model(cfg, 'prep')} / send={effective_model(cfg, 'send')}")
    if not (cfg.get("model") or "").strip():
        print("  ※ モデル未指定＝あなたの普段の既定モデルが夜間の自動実行にもそのまま効きます。"
              "\n     コストを固定したいなら `setup_schedule.py set --model sonnet`（後から変更可）。")
    if sc["mode"] == "auto" and eng == "tier_b":
        print("  ※ tier_b は claude host 限定・要ブラウザ並列。登録前に `preflight` を通すこと。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="営業パイプラインの定期実行セットアップ（Mac/Windows）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("show", help="現在の設定を表示")
    ap_apply = sub.add_parser("apply", help="設定からスケジューラへ登録/更新")
    ap_apply.add_argument("--only", choices=["prep", "send"], help="指定ジョブだけ登録（既定は両方）")
    sub.add_parser("remove", help="スケジューラ登録を解除")
    sub.add_parser("verify", help="登録状態を一覧表示")
    sub.add_parser("preflight", help="Tier B 並列送信の前提チェック＋推奨並列台数を表示")
    sub.add_parser("recommend", help="このPCの推奨並列台数（RAM/CPUから）を表示")

    s = sub.add_parser("set", help="設定を更新（指定した項目だけ変更）")
    s.add_argument("--prep-time"); s.add_argument("--prep-days", choices=["daily", "weekdays"])
    s.add_argument("--prep-times", help="1日複数回の時刻をカンマ区切りで（例: 08:00,14:00）")
    s.add_argument("--prep-message-mode", choices=["ai", "template"],
                   help="ai=③冒頭文生成 / template=004固定文＋会社名差替（③を飛ばす）")
    s.add_argument("--prep-count", type=int)
    s.add_argument("--prep-budget", type=float, help="prepの推定コスト上限USD（0=上限なし）")
    s.add_argument("--prep-parallel", choices=["on", "off"],
                   help="on=並列リスト取り（同時に複数本で集める・claude限定）/ off=単一(既定)")
    s.add_argument("--prep-concurrency", type=int, help="並列リスト取りで同時に走らせる本数")
    s.add_argument("--send-time"); s.add_argument("--send-days", choices=["daily", "weekdays"])
    s.add_argument("--send-mode", choices=["notify", "auto"])
    s.add_argument("--send-engine", choices=["tier_a", "tier_b"],
                   help="auto送信の方式: tier_a=決定論python(安全・低コスト) / tier_b=AI並列ブラウザ(高送信率・トークン消費・claude限定)")
    s.add_argument("--send-concurrency", type=int,
                   help="tier_bの並列ブラウザ台数（PC依存。preflight の推奨値を使う）")
    s.add_argument("--cap", type=int)
    s.add_argument("--criteria"); s.add_argument("--sheet-key"); s.add_argument("--notify-channel")
    s.add_argument("--host", choices=["auto", "claude", "codex"],
                   help="無人実行のホスト（auto=claude優先→codex / claude / codex）")
    s.add_argument("--model", help="無人実行で使うモデル（例 sonnet / opus。空文字でグローバル既定の継承に戻す）")
    s.add_argument("--prep-model", help="prep だけモデルを上書き（未指定なら --model → グローバル既定）")
    s.add_argument("--send-model", help="send だけモデルを上書き（未指定なら --model → グローバル既定）")

    args = ap.parse_args()
    cfg = load_config()

    if args.cmd == "show":
        print(json.dumps(cfg, ensure_ascii=False, indent=2)); return 0
    if args.cmd == "set":
        # 時刻: --prep-times（複数）と --prep-time（単一）は排他。設定した方を残す。
        if args.prep_times:
            cfg["prep"]["times"] = [t.strip() for t in args.prep_times.split(",") if t.strip()]
            cfg["prep"].pop("time", None)
        elif args.prep_time:
            cfg["prep"]["time"] = args.prep_time
            cfg["prep"].pop("times", None)
        if args.prep_days: cfg["prep"]["days"] = args.prep_days
        if args.prep_message_mode: cfg["prep"]["message_mode"] = args.prep_message_mode
        if args.prep_count is not None: cfg["prep"]["count"] = args.prep_count
        if args.prep_budget is not None: cfg["prep"]["budget_usd"] = args.prep_budget
        if args.prep_parallel: cfg["prep"]["parallel"] = (args.prep_parallel == "on")
        if args.prep_concurrency is not None:
            cfg["prep"]["concurrency"] = max(1, args.prep_concurrency)
        if args.send_time: cfg["send"]["time"] = args.send_time
        if args.send_days: cfg["send"]["days"] = args.send_days
        if args.send_mode: cfg["send"]["mode"] = args.send_mode
        if args.send_engine: cfg["send"]["engine"] = args.send_engine
        if args.send_concurrency is not None:
            cfg["send"]["concurrency"] = max(1, args.send_concurrency)
        if args.cap is not None: cfg["send"]["cap"] = args.cap
        if args.criteria: cfg["criteria"] = args.criteria
        if args.sheet_key: cfg["sheet_key"] = args.sheet_key
        if args.notify_channel is not None: cfg["notify_channel_id"] = args.notify_channel
        if args.host: cfg["host"] = args.host
        if args.model is not None: cfg["model"] = args.model.strip()
        if args.prep_model is not None: cfg["prep"]["model"] = args.prep_model.strip()
        if args.send_model is not None: cfg["send"]["model"] = args.send_model.strip()
        for t in job_times(cfg["prep"]) + job_times(cfg["send"]): _hhmm(t)  # 検証
        save_config(cfg)
        print(f"保存: {CONFIG_PATH}")
        print(json.dumps(cfg, ensure_ascii=False, indent=2)); return 0
    if args.cmd == "apply":
        jobs = (args.only,) if getattr(args, "only", None) else ("prep", "send")
        return do_apply(cfg, jobs)
    if args.cmd == "remove":
        osname = current_os()
        (macos_remove if osname == "macos" else windows_remove)() if osname in ("macos", "windows") else print("未対応OS")
        return 0
    if args.cmd == "verify":
        osname = current_os()
        (macos_verify if osname == "macos" else windows_verify)() if osname in ("macos", "windows") else print("未対応OS")
        return 0
    if args.cmd == "preflight":
        return preflight(cfg)
    if args.cmd == "recommend":
        rec = recommend_concurrency()
        print(json.dumps(rec, ensure_ascii=False)); return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
