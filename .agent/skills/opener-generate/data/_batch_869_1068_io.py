#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SKILL_DIR = Path(__file__).resolve().parents[4]
SHARED_DIR = SKILL_DIR / "shared"
OPENER_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SHARED_DIR))
from sheets_io import open_worksheet, read_rows, resolve_columns, write_cells  # noqa: E402
sys.path.insert(0, str(OPENER_SCRIPTS))
import opener_helpers as opener_helpers  # noqa: E402


SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
WORKSHEET = "シート1"
COMMON_BODY_PATH = SHARED_DIR / "common_body.md"
BODY_START = "サイト制作後も、できれば継続してクライアントを支援したい。"

SALES_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"営業.{0,16}(?:お断り|断り|ご遠慮|遠慮|禁止|固く|かたく)",
        r"(?:セールス|売り込み|勧誘).{0,16}(?:お断り|断り|ご遠慮|遠慮|禁止|固く|かたく)",
        r"(?:お断り|断り|ご遠慮|遠慮|禁止).{0,16}(?:営業|セールス|売り込み|勧誘)",
        r"お客様(?:専用|用).{0,36}(?:営業|セールス|売り込み|勧誘)",
    ]
]


def body_text() -> str:
    raw = COMMON_BODY_PATH.read_text(encoding="utf-8")
    return raw.split("---本文ここから---", 1)[1].split("---本文ここまで---", 1)[0].strip()


def rows_for_range(ws, start: int, end: int) -> list[dict]:
    rows = read_rows(
        ws,
        want=["company_name", "url", "contact_url", "message", "status", "error_reason"],
        require=["company_name", "url"],
    )
    by_row = {int(r["_row"]): r for r in rows}
    return [dict(by_row.get(n, {"_row": n})) for n in range(start, end + 1)]


def cmd_snapshot(args):
    ws = open_worksheet(SHEET, WORKSHEET)
    selected = rows_for_range(ws, args.start, args.end)
    Path(args.out_json).write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
    with Path(args.out_csv).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["company_name", "url"])
        w.writeheader()
        for r in selected:
            w.writerow({"company_name": r.get("company_name", ""), "url": r.get("url", "")})
    summary = {
        "start": args.start,
        "end": args.end,
        "count": len(selected),
        "company": sum(bool(r.get("company_name")) for r in selected),
        "url": sum(bool(r.get("url")) for r in selected),
        "contact_url": sum(bool(r.get("contact_url")) for r in selected),
        "message": sum(bool(r.get("message")) for r in selected),
        "status": sum(bool(r.get("status")) for r in selected),
    }
    print(json.dumps(summary, ensure_ascii=False))


def clean_text(raw: str) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = html.unescape(soup.get_text(" ", strip=True))
    return re.sub(r"\s+", " ", text)


def scan_one(row: dict) -> dict:
    url = (row.get("contact_url") or "").strip()
    out = {"_row": row.get("_row"), "company_name": row.get("company_name", ""), "contact_url": url,
           "ok": False, "status_code": None, "final_url": "", "error": "", "sales_hits": []}
    if not url:
        out["error"] = "contact_url blank"
        return out
    try:
        res = requests.get(url, timeout=20, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        out["status_code"] = res.status_code
        out["final_url"] = res.url
        if res.status_code >= 400:
            out["error"] = f"HTTP {res.status_code}"
            return out
        text = clean_text(res.text)
        hits = []
        for pat in SALES_PATTERNS:
            for m in pat.finditer(text):
                s, e = max(0, m.start() - 45), min(len(text), m.end() + 65)
                hit = text[s:e].strip()
                if hit and hit not in hits:
                    hits.append(hit)
        out["sales_hits"] = hits[:8]
        out["ok"] = True
    except requests.exceptions.SSLError as exc:
        out["error"] = f"SSL: {type(exc).__name__}: {exc}"
    except requests.RequestException as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def cmd_scan(args):
    rows = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    results = [scan_one(r) for r in rows]
    Path(args.out).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "count": len(results),
        "ok": sum(r["ok"] for r in results),
        "errors": [{"row": r["_row"], "error": r["error"][:160]} for r in results if r["error"]],
        "sales_hits": [{"row": r["_row"], "hits": r["sales_hits"]} for r in results if r["sales_hits"]],
    }, ensure_ascii=False))


def cmd_eligible(args):
    rows = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    blockers = json.loads(Path(args.blockers).read_text(encoding="utf-8"))
    blocked = {int(x["_row"]) for x in blockers}
    eligible = [r for r in rows if int(r["_row"]) not in blocked]
    Path(args.out_json).write_text(json.dumps(eligible, ensure_ascii=False, indent=2), encoding="utf-8")
    with Path(args.out_csv).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["company_name", "url"])
        w.writeheader()
        for r in eligible:
            w.writerow({"company_name": r.get("company_name", ""), "url": r.get("url", "")})
    print(json.dumps({"eligible": len(eligible), "blocked": len(blocked)}, ensure_ascii=False))


def cmd_map_tasks(args):
    tasks = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    rows = json.loads(Path(args.eligible).read_text(encoding="utf-8"))
    if len(tasks) != len(rows):
        raise SystemExit(f"task/row mismatch: {len(tasks)} != {len(rows)}")
    for task, row in zip(tasks, rows):
        if task.get("company_name") != row.get("company_name") or task.get("url") != row.get("url"):
            raise SystemExit(f"mapping mismatch idx={task.get('idx')}")
        task["_row"] = int(row["_row"])
    Path(args.out).write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"mapped": len(tasks), "first": tasks[0]["_row"] if tasks else None,
                      "last": tasks[-1]["_row"] if tasks else None}, ensure_ascii=False))


def cmd_write_blockers(args):
    blockers = json.loads(Path(args.blockers).read_text(encoding="utf-8"))
    ws = open_worksheet(SHEET, WORKSHEET)
    headers, mapping = resolve_columns(ws, ["message", "status", "error_reason"])
    cols = {}
    for key in ("message", "status", "error_reason"):
        idx = mapping.get(key)
        if idx is None:
            raise SystemExit(f"missing column: {key}")
        cols[key] = headers[idx]
    payload = []
    for b in blockers:
        payload.append({"_row": int(b["_row"]), cols["message"]: "", cols["status"]: "送信不可",
                        cols["error_reason"]: b["reason"]})
    count = write_cells(ws, payload, [cols["message"], cols["status"], cols["error_reason"]], overwrite=True)
    print(json.dumps({"blockers": len(blockers), "cells": count}, ensure_ascii=False))


def cmd_audit(args):
    ws = open_worksheet(SHEET, WORKSHEET)
    selected = rows_for_range(ws, args.start, args.end)
    blockers = json.loads(Path(args.blockers).read_text(encoding="utf-8"))
    blocked = {int(x["_row"]): x for x in blockers}
    results = json.loads(Path(args.results).read_text(encoding="utf-8"))
    tasks = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    expected = {int(t["_row"]): results[str(t["idx"])] for t in tasks}
    body = opener_helpers.load_common_body()
    intro_tmpl = opener_helpers.load_intro()
    sender = opener_helpers.load_sender_info()
    para = {}
    exact = 0
    current_body = 0
    messages = []
    blockers_ok = 0
    for r in selected:
        row = int(r["_row"])
        msg = r.get("message", "")
        if row in blocked:
            b = blocked[row]
            if not msg and r.get("status") == "送信不可" and r.get("error_reason") == b["reason"]:
                blockers_ok += 1
            continue
        opener = expected[row]
        intro = opener_helpers.fill_placeholders(intro_tmpl, r.get("company_name", ""), sender)
        filled_body = opener_helpers.fill_placeholders(body, r.get("company_name", ""), sender)
        wanted = "\n\n".join(p for p in (intro, opener.strip(), filled_body) if p)
        if msg == wanted:
            exact += 1
        if BODY_START in msg:
            current_body += 1
        pcount = len([p for p in re.split(r"\n\s*\n", opener.strip()) if p.strip()])
        para[str(pcount)] = para.get(str(pcount), 0) + 1
        messages.append(opener.strip())
    out = {
        "target": args.end - args.start + 1,
        "eligible": len(expected),
        "blocked": len(blocked),
        "reconciled": len(expected) + len(blocked),
        "exact": exact,
        "current_body": current_body,
        "paragraph_counts": para,
        "unique_openers": len(set(messages)),
        "blockers_ok": blockers_ok,
        "ok": (len(expected) + len(blocked) == args.end - args.start + 1 and exact == len(expected)
               and current_body == len(expected) and para == {"3": len(expected)}
               and len(set(messages)) == len(expected) and blockers_ok == len(blocked)),
    }
    print(json.dumps(out, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("--start", type=int, required=True); s.add_argument("--end", type=int, required=True)
    s.add_argument("--out-csv", required=True); s.add_argument("--out-json", required=True); s.set_defaults(func=cmd_snapshot)
    s = sub.add_parser("scan")
    s.add_argument("--snapshot", required=True); s.add_argument("--out", required=True); s.set_defaults(func=cmd_scan)
    s = sub.add_parser("eligible")
    s.add_argument("--snapshot", required=True); s.add_argument("--blockers", required=True)
    s.add_argument("--out-csv", required=True); s.add_argument("--out-json", required=True); s.set_defaults(func=cmd_eligible)
    s = sub.add_parser("map-tasks")
    s.add_argument("--tasks", required=True); s.add_argument("--eligible", required=True); s.add_argument("--out", required=True); s.set_defaults(func=cmd_map_tasks)
    s = sub.add_parser("write-blockers")
    s.add_argument("--blockers", required=True); s.set_defaults(func=cmd_write_blockers)
    s = sub.add_parser("audit")
    s.add_argument("--start", type=int, required=True); s.add_argument("--end", type=int, required=True)
    s.add_argument("--blockers", required=True); s.add_argument("--tasks", required=True); s.add_argument("--results", required=True); s.set_defaults(func=cmd_audit)
    args = p.parse_args(); args.func(args)


if __name__ == "__main__":
    main()
