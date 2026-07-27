"""アシストモード（🟡 Human-in-the-loop）— Phase 1 骨組み。

契約（3 行）:
    入力: run_send が出した assist_queue_<run_id>.jsonl（CAPTCHA で“あと一歩”の社）
    動作: 1 社ずつ「目視ブラウザで再オープン＋自動入力」し、送信は押さず人を待つ
    出力: 人が CAPTCHA を解いて送信 → 完了を自動検知 → assist_result_<run_id>.csv

設計方針:
    - 送信本体（_general_form_sender）には触れない。**入力・完了検知の純粋ヘルパだけ再利用**。
    - 常に目視ブラウザ（headless=False）。人がその場で操作する前提なので隠す必要がない。
    - 1 社の入力に失敗しても次へ進む（Fail Safe）。中断（q）・スキップ（s）可。

Phase 2 以降（今はやらない）:
    - キューの優先度づけ・件数上限・done マーキングでの再開最適化
    - 複雑フィールド（select/radio）の form-reasoning 再現
    - アシスト成功を学習辞書へ還流

使い方:
    uv run --directory <skill> python scripts/assist_mode.py \
        logs/assist_queue_<run_id>.jsonl --sender sender_info.json
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 人がブラウザで CAPTCHA→送信する間、完了を自動検知して待つ最大秒数（社ごと）。
# ターミナル操作（Enter）を不要にするための待機。env で調整可。
_ASSIST_WAIT_TIMEOUT_SEC = float(os.environ.get("AUTOFORM_ASSIST_TIMEOUT_SEC", "180"))

# run_send.py と同じ sys.path 解決（core/ をフラット import 可能にする）。
_SKILL_DIR = Path(__file__).resolve().parents[1]
_SKILL_CORE_DIR = _SKILL_DIR / "core"
_REPO_ROOT = _SKILL_DIR.parent
# 送信者情報の正本はリポジトリ直下の shared/sender_info.json（run_send / run_on_sheet と統一）。
_DEFAULT_SENDER_INFO = _SKILL_DIR.parents[2] / "shared" / "sender_info.json"
for _entry in (_SKILL_CORE_DIR, _SKILL_DIR, _REPO_ROOT):
    if str(_entry) not in sys.path:
        sys.path.insert(0, str(_entry))


def _parse_args(argv: Optional[list[str]]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="アシストモード（CAPTCHA系の最終仕上げ）")
    p.add_argument("queue", help="assist_queue_<run_id>.jsonl のパス")
    p.add_argument(
        "--sender",
        default=str(_DEFAULT_SENDER_INFO),
        help="送信者情報 JSON（フォーム入力値の供給元）。既定: リポジトリ直下の shared/sender_info.json",
    )
    p.add_argument(
        "--output",
        default=None,
        help="結果 CSV（省略時 assist_result_<時刻>.csv を queue と同じ場所に）",
    )
    p.add_argument(
        "--decisions",
        default=None,
        help="④式ハンドオフの決定JSON（省略時 data/field_decisions.json があれば自動使用）",
    )
    return p.parse_args(argv)


def _load_queue(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                sys.stderr.write(f"[assist_mode] skip bad line: {e}\n")
    return rows


def _load_sender(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("sender_info.json must be a JSON object")
    return data


async def _poll_until_closed(page, timeout_sec: float, interval_ms: int = 1500) -> str:
    """人がウィンドウを閉じるまで待つ。閉じる前に送信完了を検知できたら completed と
    ラベル付けする。**自動では閉じない**＝確認ページ型でも早期に閉じてしまわない。

    Returns: "completed"(完了検知済) / "closed"(未検知で閉じた=スキップor検知漏れ) /
             "timeout"(未検知のまま時間切れ)
    """
    try:
        from _general_form_sender import _wait_for_success  # type: ignore
    except ImportError:
        from skill.core._general_form_sender import _wait_for_success  # type: ignore

    detected = False
    waited = 0.0
    while waited < timeout_sec:
        if page.is_closed():
            return "completed" if detected else "closed"
        if not detected:
            try:
                if await _wait_for_success(page, interval_ms):
                    detected = True
                    print("  ✓ 送信完了を検知しました。確認できたらウィンドウを閉じてください。")
            except BaseException:  # noqa: BLE001 — ページ遷移/クローズ中の一時例外
                if page.is_closed():
                    return "completed" if detected else "closed"
        else:
            await asyncio.sleep(interval_ms / 1000.0)
        waited += interval_ms / 1000.0
    return "completed" if detected else "timeout"


async def _prefill_form(
    page, fill_data: dict, field_decisions: Optional[dict] = None
) -> tuple[int, list[str]]:
    """送信本体と同じ充填ロジック(_fill_field)でフォームを事前入力する。

    text/email/tel に加え、**select はファジー一致・radio は DOMプロパティ比較**で
    自動入力する。辞書で解けない選択欄は ④式ハンドオフの決定(field_decisions)を当てる。
    どうしても不明な欄（＝CAPTCHA 等）だけ人に残す。

    Returns: (埋めた数, 埋めた欄ラベル一覧)
    """
    try:
        from _form_detector import analyze_form  # type: ignore
        from _general_form_sender import (  # type: ignore
            _build_address_dedup_skips,
            _build_phone_split_overrides,
            _field_resolution_value,
            _fill_field,
            _lookup_decision,
        )
    except ImportError:
        from skill.core._form_detector import analyze_form  # type: ignore
        from skill.core._general_form_sender import (  # type: ignore
            _build_address_dedup_skips,
            _build_phone_split_overrides,
            _field_resolution_value,
            _fill_field,
            _lookup_decision,
        )

    fields, form_frame = await analyze_form(page)
    # 分割電話欄(tel1/tel2/tel3 等)は本体の送信ループ(_general_form_sender)と同じく
    # 分割上書きを適用する。これを飛ばすと各欄が個別に「電話＝フル番号」に解決され、
    # 3欄すべてに同じ番号が入る（実フォーム検証で発覚・2026-07-10）。
    phone_split_overrides = _build_phone_split_overrides(fields, fill_data)
    # 複数の住所欄(番地/建物名等)に同じ住所が重複充填されるのを防ぐ(先頭1欄のみ)。
    address_dedup_skips = _build_address_dedup_skips(fields, fill_data)
    filled_labels: list[str] = []
    for idx, field in enumerate(fields):
        if idx in address_dedup_skips:
            continue  # 重複住所欄は空のまま
        value, semantic, _origin = _field_resolution_value(field, fill_data)
        if idx in phone_split_overrides:
            value = phone_split_overrides[idx]
            semantic = semantic or "phone"
        if value is None or not semantic:
            # 辞書で解けない欄は ④式ハンドオフの決定（あなたが選んだ値）を当てる。
            decided = _lookup_decision(field_decisions, getattr(field, "label", "") or "")
            if decided is None or str(decided) == "":
                continue  # それでも不明な欄は人がブラウザ上で直接（CAPTCHA 等）
            value = decided
        field_type = (getattr(field, "type", "") or "").lower()
        try:
            await _fill_field(
                form_frame, field_type, field.selector, value, getattr(field, "name", None)
            )
            filled_labels.append(
                getattr(field, "label", "") or semantic or field_type
            )
        except BaseException as e:  # noqa: BLE001 — best effort（次の欄へ）
            sys.stderr.write(
                f"[assist_mode] fill skip {field.selector!r}: "
                f"{type(e).__name__}: {e}\n"
            )
    return len(filled_labels), filled_labels


async def _assist_one(
    entry: dict, fill_data: dict, idx: int, total: int,
    field_decisions: Optional[dict] = None,
) -> dict:
    """1 社分: 目視ブラウザで開く → 自動で全欄入力（select/radio/ハンドオフ決定込み）→
    人が CAPTCHA を解いて【送信】まで押す → 完了検知。"""
    company = entry.get("company_name") or "(no name)"
    url = entry.get("url") or ""
    result = {
        "company_name": company,
        "url": url,
        "status": "failed",
        "provider_used": "human_assisted",
        "sent_at": "",
        "note": "",
    }

    try:
        from playwright.async_api import async_playwright  # type: ignore
    except ImportError:
        result["note"] = "playwright not installed"
        return result

    try:
        from _general_form_sender import (  # type: ignore
            _DEFAULT_VIEWPORT,
            _PAGE_NAVIGATION_TIMEOUT_MS,
            _SUCCESS_WAIT_TIMEOUT_MS,
            _wait_for_success,
        )
    except ImportError:
        from skill.core._general_form_sender import (  # type: ignore
            _DEFAULT_VIEWPORT,
            _PAGE_NAVIGATION_TIMEOUT_MS,
            _SUCCESS_WAIT_TIMEOUT_MS,
            _wait_for_success,
        )

    async with async_playwright() as pw:
        # アシストは常に目視ブラウザ（headless=False）。
        browser = await pw.chromium.launch(headless=False)
        try:
            context = await browser.new_context(
                viewport=_DEFAULT_VIEWPORT, locale="ja-JP"
            )
            page = await context.new_page()
            await page.bring_to_front()
            try:
                await page.goto(
                    url, timeout=_PAGE_NAVIGATION_TIMEOUT_MS,
                    wait_until="domcontentloaded",
                )
            except BaseException as e:  # noqa: BLE001
                result["note"] = f"goto_failed:{type(e).__name__}"
                return result

            # JS描画フォーム対策: domcontentloaded 直後は input が未生成のことがある
            # (React/Vue 等で goto 後にフォームを描画するサイト)。analyze_form を
            # 走らせる前に入力欄が現れるまで待つ。現れなければそのまま進む(静的フォーム
            # や本当にフォームが無いサイトを無用に遅延させない)。
            # ※ leadnine.co.jp で「待機ゼロ→0欄検出」だった不具合の修正(2026-07-10)。
            try:
                await page.wait_for_selector(
                    "input:not([type=hidden]), textarea, select", timeout=6_000
                )
                await page.wait_for_timeout(800)  # 残りの欄の描画が落ち着くのを待つ
            except BaseException:  # noqa: BLE001 — 現れなければ待たずに解析へ
                pass

            # 決定JSONは {url or company: {label: value}}。この社の分だけ取り出す。
            per_company_decisions = None
            if field_decisions:
                per_company_decisions = (
                    field_decisions.get(url) or field_decisions.get(company)
                )
            n_filled, labels = await _prefill_form(
                page, fill_data, per_company_decisions
            )

            print()
            print(f"【{idx}/{total}】{company}  {url}")
            print(f"  ✓ {n_filled} 欄を自動入力しました: {' / '.join(labels[:6])}")
            print("  → CAPTCHA を解き、内容を確認して【送信】（確認ページがあれば進めて送信）。")
            print("    送信完了ページを確認したら、このウィンドウを閉じてください（＝完了）。")
            print("    送らない/飛ばす場合も、ウィンドウを閉じてください。")
            print(f"    ※自動では閉じません（確認ページ型でも早閉じしない）。最大 {int(_ASSIST_WAIT_TIMEOUT_SEC)} 秒待機。")

            # 自動では閉じない。人がウィンドウを閉じるまで待ち、完了は検知でラベル付け。
            outcome = await _poll_until_closed(page, _ASSIST_WAIT_TIMEOUT_SEC)
            result["sent_at"] = datetime.now().isoformat()
            if outcome == "completed":
                result["status"] = "completed"
                print("  ✓ 送信完了（検知済み）")
            elif outcome == "closed":
                result["status"] = "unconfirmed"
                result["note"] = "closed_without_detection"
                print("  – ウィンドウが閉じられました（完了を自動検知できず＝送信済みか要確認）")
            else:  # timeout
                result["status"] = "unconfirmed"
                result["note"] = "timeout_no_close"
                print("  ⚠ 時間切れ（ウィンドウ未クローズ／要目視）")
            return result
        finally:
            try:
                await browser.close()
            except BaseException:  # noqa: BLE001
                pass


async def _run(
    queue: list[dict], fill_data: dict, output_path: Path,
    field_decisions: Optional[dict] = None,
) -> int:
    pending = [e for e in queue if (e.get("status") or "pending") == "pending"]
    total = len(pending)
    if total == 0:
        print("アシスト対象がありません（キューが空、または全て処理済み）。")
        return 0

    print("=" * 56)
    print(f" アシストモード — {total} 社（CAPTCHA系の最終仕上げ）")
    print(" 各社ブラウザが順に開きます。CAPTCHA を解いて【送信】を押すだけ。")
    print(" ターミナル操作は不要（送信を自動検知して次の社へ進みます）。")
    print("=" * 56)

    results: list[dict] = []
    for idx, entry in enumerate(pending, start=1):
        # message を fill_data に載せて 1 社分の入力値を作る。
        per_company = dict(fill_data)
        per_company["message"] = entry.get("message") or fill_data.get("message", "")
        try:
            res = await _assist_one(entry, per_company, idx, total, field_decisions)
        except BaseException as e:  # noqa: BLE001 — Fail Safe（次社へ）
            res = {
                "company_name": entry.get("company_name") or "",
                "url": entry.get("url") or "",
                "status": "failed",
                "provider_used": "human_assisted",
                "sent_at": "",
                "note": f"{type(e).__name__}: {e}"[:200],
            }
        results.append(res)
        if res.get("status") == "aborted":
            print("中断しました。ここまでの結果を保存します。")
            break

    _write_results(results, output_path)
    completed = sum(1 for r in results if r.get("status") == "completed")
    print()
    print(f"アシスト完了: {completed}/{len(results)} 社 送信。結果 → {output_path}")
    return 0


def _write_results(results: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["company_name", "url", "status", "provider_used", "sent_at", "note"]
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    queue_path = Path(args.queue).resolve()
    if not queue_path.exists():
        sys.stderr.write(f"[assist_mode] queue not found: {queue_path}\n")
        return 1
    try:
        sender = _load_sender(Path(args.sender).resolve())
    except BaseException as e:  # noqa: BLE001
        sys.stderr.write(f"[assist_mode] sender_info 読み込み失敗: {e}\n")
        return 1

    queue = _load_queue(queue_path)
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = queue_path.parent / f"assist_result_{ts}.csv"

    # ④式ハンドオフの決定JSON（明示 --decisions or 既定 data/field_decisions.json）。
    field_decisions: Optional[dict] = None
    dec_path = Path(args.decisions).resolve() if args.decisions else (
        _SKILL_DIR / "data" / "field_decisions.json"
    )
    if dec_path.exists():
        try:
            field_decisions = json.loads(dec_path.read_text(encoding="utf-8"))
            sys.stderr.write(
                f"[assist_mode] 決定JSON {dec_path.name} を読み込み"
                f"（{len(field_decisions or {})} 社分）\n"
            )
        except BaseException as e:  # noqa: BLE001
            sys.stderr.write(f"[assist_mode] 決定JSON 読み込み失敗（無視）: {e}\n")

    try:
        return asyncio.run(_run(queue, sender, output_path, field_decisions))
    except KeyboardInterrupt:
        sys.stderr.write("\n[assist_mode] 中断しました。\n")
        return 130


if __name__ == "__main__":
    sys.exit(main())
