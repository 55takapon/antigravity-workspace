"""Sprint 6 Task 7 — Stage 1.5 main engine (Playwright + pattern matching).

Combines the helper modules built in Task 1-6 into a `LocalGeneralFormProvider`
that the `HybridProvider` invokes between Stage 1 (CF7 HTTP POST) and Stage
2/3 (noAI filter + AI fallback).

Flow inside send():
    1. Reachability classification (404 / WAF 403 / 5xx / network_error)
    2. Domain cooldown check
    3. Launch Playwright Chromium (headless=False — visible mode per Phase 2-B)
    4. Goto + bot protection detect (Turnstile / hCaptcha -> early return)
    5. Workflow cache lookup -> replay if hit (AI completely bypassed)
    6. Form detection -> field list
    7. Field resolution: static dict -> learned dict -> form-reasoning AI
       (gpt-4o-mini, optional)
    8. Fill form via Playwright
    9. CAPTCHA solver (optional, CAPSOLVER_API_KEY)
   10. Click submit, wait for success signals
   11. On success: accumulate learned dictionary + record workflow + reset
       cooldown + screenshot
   12. On failure: classify error, increment cooldown counter, screenshot
   13. Close browser

NOTE: Sync with src/lib/browser/engine.ts L449-820 (Stage D-G of system-workflow).
"""

from __future__ import annotations

import asyncio
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# -----------------------------------------------------------------------------
# Sanitization (Stage 1.5 用、NOTE: Sync with _skill_core._sanitize_error_reason)
# error_reason に sender_info の個人情報や API キー断片が混入することを防ぐ。
# `_skill_core` への循環 import を避けるためローカルコピー。
# -----------------------------------------------------------------------------
_SENSITIVE_SENDER_KEYS = (
    "email",
    "phone",
    "address",
    "lastName",
    "firstName",
    "nameKana",
    "nameHiragana",
    "zip",
    "companyUrl",
)
_API_KEY_PATTERN = re.compile(r"sk-ant-[A-Za-z0-9_\-]+")
_SANITIZE_MIN_VALUE_LEN = 3


def _sanitize_text(text: Optional[str], sender_info: Optional[dict]) -> Optional[str]:
    """Stage 1.5 で error_reason に書き出す前に PII / API キー断片を伏字化する Fail Safe ヘルパー。

    NOTE: Sync with skill/core/_skill_core.py:_sanitize_error_reason
    """
    if not text:
        return text
    try:
        if isinstance(sender_info, dict):
            for key in _SENSITIVE_SENDER_KEYS:
                raw = sender_info.get(key)
                if raw is None:
                    continue
                value = str(raw)
                if len(value) >= _SANITIZE_MIN_VALUE_LEN and value in text:
                    text = text.replace(value, "<redacted>")
        text = _API_KEY_PATTERN.sub("<redacted-api-key>", text)
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_general_form_sender] _sanitize_text failed (continuing with raw text): "
            f"{type(e).__name__}: {e}\n"
        )
    return text

# Module-level imports: prefer the package form so type checkers can follow.
try:
    from skill.core._captcha_solver import prepare_captcha_for_submission
    from skill.core._domain_cooldown import (
        is_cooldown,
        origin_for_url,
        record_failure,
        record_success,
    )
    from skill.core._form_detector import (
        FormField,
        analyze_form,
        detect_bot_protection,
    )
    from skill.core._form_filler_lite import FillData, determine_value
    from skill.core._form_filler_lite import _semantic_to_value, split_phone_value
    from skill.core._fuzzy_select import best_option, default_inquiry_option
    from skill.core._learning_dictionary import (
        accumulate_on_success,
        load_learned_dictionary,
        match_learned_label,
    )
    from skill.core._pattern_loader import (
        check_prohibition,
        load_confirmation_signals,
        load_dynamic_detection,
        load_submit_buttons,
        match_label,
        normalize_l1,
    )
    from skill.core._reachability_classifier import classify_reachability
    from skill.core import _server_client
    from skill.core._usage_logger import log_usage
    from skill.core._workflow_cache import (
        build_workflow_from_general_form_success,
        compute_form_fingerprint,
        lookup_workflow,
        record_successful_workflow,
        record_workflow_failure,
        replay_workflow,
    )
except ImportError:  # flat sys.path (run_send.py)
    from _captcha_solver import prepare_captcha_for_submission  # type: ignore
    from _domain_cooldown import (  # type: ignore
        is_cooldown,
        origin_for_url,
        record_failure,
        record_success,
    )
    from _form_detector import (  # type: ignore
        FormField,
        analyze_form,
        detect_bot_protection,
    )
    from _form_filler_lite import FillData, determine_value  # type: ignore
    from _form_filler_lite import _semantic_to_value, split_phone_value  # type: ignore
    from _fuzzy_select import best_option, default_inquiry_option  # type: ignore
    from _learning_dictionary import (  # type: ignore
        accumulate_on_success,
        load_learned_dictionary,
        match_learned_label,
    )
    from _pattern_loader import (  # type: ignore
        check_prohibition,
        load_confirmation_signals,
        load_dynamic_detection,
        load_submit_buttons,
        match_label,
        normalize_l1,
    )
    from _reachability_classifier import classify_reachability  # type: ignore
    import _server_client  # type: ignore
    from _usage_logger import log_usage  # type: ignore
    from _workflow_cache import (  # type: ignore
        build_workflow_from_general_form_success,
        compute_form_fingerprint,
        lookup_workflow,
        record_successful_workflow,
        record_workflow_failure,
        replay_workflow,
    )


# -----------------------------------------------------------------------------
# Tunables
# -----------------------------------------------------------------------------
_PAGE_NAVIGATION_TIMEOUT_MS = 30_000
_SUCCESS_WAIT_TIMEOUT_MS = 12_000
_SUCCESS_POLL_INTERVAL_MS = 400
_FIELD_FILL_TIMEOUT_MS = 4_000
# #38: 個別 frame 操作(count/evaluate)の上限。応答するフレームは ms 級で通るので、
# これは「実行コンテキストが来ないゴーストフレーム」だけを打ち切るための余裕値。
_FRAME_OP_TIMEOUT_S = 3.0
_DEFAULT_VIEWPORT = {"width": 1280, "height": 800}


def _now_iso() -> str:
    return datetime.now().isoformat()


def _lookup_decision(field_decisions: Optional[dict], label: Optional[str]):
    """④式ハンドオフの決定辞書から、欄ラベルに対応する値を引く（正規化一致）。

    field_decisions は {欄ラベル: 選んだ値}。直接一致 → normalize_l1 正規化一致の順。
    無ければ None。
    """
    if not field_decisions or not label:
        return None
    if label in field_decisions:
        return field_decisions[label]
    nl = normalize_l1(label)
    for k, v in field_decisions.items():
        if normalize_l1(k) == nl:
            return v
    return None


# 同意/承諾チェックの「実行」はローカル、「語彙」はサーバー、という分割。
# ★成長する語彙の本体は server-formsend/payload/consent_labels.json（resolve_fields が
#   consent_agreement を返す）。ローカルのこの seed は普遍語のみの最小フォールバックで、
#   サーバー不達時にだけ効く（滅多に増やさない＝再配布を誘発しない）。
_CONSENT_LABEL_SEED = (
    "同意", "承諾", "プライバシーポリシー", "個人情報", "利用規約",
    "agree", "consent",
)


def _is_consent_label(label: Optional[str]) -> bool:
    """ラベルが同意/承諾チェックか（ローカル最小 seed の正規化 substring 一致）。

    語彙の育成はサーバー（resolve_fields）側で行う。ここはサーバー不達時のフォールバック。
    """
    if not label:
        return False
    nl = normalize_l1(label)
    return any(normalize_l1(s) in nl for s in _CONSENT_LABEL_SEED)


async def _fill_field(page, field_type, selector, value, name=None, nth=None) -> None:
    """1 欄を型に応じて入力する（送信本体と assist_mode で共有）。

    - select : value/label 完全一致 → ファジー一致（全半角正規化＋編集距離）
    - radio  : name 属性(field.name)と value/ラベルを DOM プロパティで比較してクリック
               （CSS セレクタを組み立てないので特殊文字・空白に強い）
    - その他 : page.fill（nth 指定時は同一セレクタの nth 番目に入力＝電話分割欄対応）

    失敗時は例外を送出（呼び出し側が Fail-safe で握る）。
    """
    ftype = (field_type or "").lower()
    if ftype in ("select", "select-one"):
        loc = page.locator(selector).first
        target = str(value)
        opts = await loc.evaluate(
            "el => Array.from(el.options || [])"
            ".map(o => ({value: o.value, label: (o.textContent||'').trim()}))"
        )
        vals = [o.get("value", "") for o in opts]
        labels = [o.get("label", "") for o in opts]
        if target in vals:
            await loc.select_option(value=target, timeout=_FIELD_FILL_TIMEOUT_MS)
        elif target in labels:
            await loc.select_option(label=target, timeout=_FIELD_FILL_TIMEOUT_MS)
        else:
            choice = best_option(target, [x for x in labels if x])
            if choice:
                await loc.select_option(label=choice, timeout=_FIELD_FILL_TIMEOUT_MS)
            else:
                cv = best_option(target, [x for x in vals if x])
                if cv:
                    await loc.select_option(value=cv, timeout=_FIELD_FILL_TIMEOUT_MS)
                else:
                    raise RuntimeError(f"select option not matched target={target!r}")
    elif ftype == "radio":
        rname = name or ""
        rval = str(value)
        clicked = await page.evaluate(
            """([name, value]) => {
                const els = document.querySelectorAll('input[type="radio"]');
                for (const el of els) {
                    const nameOk = name ? el.name === name : true;
                    const valOk = el.value === value ||
                        (el.labels && Array.from(el.labels)
                            .some(l => (l.textContent || '').trim() === value));
                    if (nameOk && valOk) { el.click(); return true; }
                }
                return false;
            }""",
            [rname, rval],
        )
        if not clicked:
            raise RuntimeError(f"radio option not found name={rname!r} value={rval!r}")
    elif ftype == "checkbox":
        # 同意/承諾チェック（送信ゲート）を ON にする。通常は check()、カスタムUIで
        # input が hidden の場合は actionability で失敗するため JS で checked+change を発火。
        loc = page.locator(selector).first
        try:
            await loc.check(timeout=_FIELD_FILL_TIMEOUT_MS)
        except BaseException:
            await loc.evaluate(
                "el => { if (el && el.type === 'checkbox' && !el.checked) {"
                " el.checked = true;"
                " el.dispatchEvent(new Event('input', { bubbles: true }));"
                " el.dispatchEvent(new Event('change', { bubbles: true })); } }"
            )
    else:
        if nth is not None:
            # 同一セレクタ (name="tel[]" 等) が複数ある分割欄で nth 番目を狙い撃つ。
            await page.locator(selector).nth(nth).fill(
                str(value), timeout=_FIELD_FILL_TIMEOUT_MS
            )
        else:
            await page.fill(selector, str(value), timeout=_FIELD_FILL_TIMEOUT_MS)


# -----------------------------------------------------------------------------
# Central-brain (formsend-core) integration — server-first, local fallback.
# step2-2: cooldown ゲートと結果書き戻しのドメイン状態をサーバーへ。未設定/不達は
# ローカル(_domain_cooldown)へ自動フォールバック（_server_client が None を返す）。
# 学習辞書 learned[] の中央書き戻しは欄解決の作り替え(step3)と一体で folding する。
# -----------------------------------------------------------------------------
async def _domain_in_cooldown(origin: str) -> bool:
    """送信前ゲート。サーバーが応答すれば send_ok を尊重、None ならローカル判定。"""
    gate = await _server_client.check_domain(origin)
    if gate is not None:
        return not gate.get("send_ok", True)
    return is_cooldown(origin)


async def _report_domain_outcome(
    origin: str,
    status: str,
    error_reason: str = "",
    *,
    fingerprint: str = "",
    learned: Optional[list[dict]] = None,
    workflow: Optional[dict] = None,
) -> None:
    """結果を中央へ報告（cooldown＋success時は学習辞書/ workflow も書き戻し）。

    1社1回だけ呼ぶ（外側スコープ）。learned[] / workflow を成功時にまとめて送る
    ことで二重カウントを防ぐ。ローカル record_success/failure・accumulate_on_success・
    record_successful_workflow は呼び出し側で常時実行済み（オフライン整合）。失敗は無視。
    """
    if not _server_client.is_configured():
        return
    payload_learned = None
    if learned:
        # ローカルの {normalized_label, semantic, origin} を契約の {label, semantic, origin} へ。
        # サーバー側で再正規化されるため normalized_label をそのまま label に渡してよい。
        payload_learned = [
            {
                "label": e.get("normalized_label") or e.get("label") or "",
                "semantic": e.get("semantic") or "",
                "origin": e.get("origin") or "learned",
            }
            for e in learned
            if (e.get("normalized_label") or e.get("label")) and e.get("semantic")
        ]
    await _server_client.report_outcome(
        status=status,
        domain=origin,
        error_reason=error_reason,
        form_fingerprint=fingerprint,
        learned=payload_learned,
        workflow=workflow,
    )


def _resolve_headless_mode() -> bool:
    """Sprint 6 §3-6: default headless=False. Phase 3 flips this.

    For Phase 2-B, allow opt-in via AUTOFORM_HEADLESS=1 for CI.
    """
    raw = os.environ.get("AUTOFORM_HEADLESS", "").strip()
    return raw == "1"


# os import here to keep top tidy
import os  # noqa: E402


# -----------------------------------------------------------------------------
# Result helpers
# -----------------------------------------------------------------------------
def _result(
    *,
    status: str,
    provider_used: str,
    error_reason: Optional[str] = None,
    screenshot_path: Optional[str] = None,
    trace_detail: Optional[dict] = None,
) -> dict:
    out = {
        "status": status,
        "error_reason": error_reason,
        "screenshot_path": screenshot_path,
        "ended_at": _now_iso(),
        "provider_used": provider_used,
    }
    # 診断トレース（純観測）: 欄検出 detail を `_trace_detail` で添える。
    # consumer は `.get()` 参照なので送信ロジック・出力には影響しない。
    if trace_detail is not None:
        out["_trace_detail"] = trace_detail
    return out


def _save_screenshot_bytes(
    screenshot_bytes: Optional[bytes],
    screenshot_dir: Optional[str],
    company_name: str,
) -> Optional[str]:
    """Same shape as _skill_core._save_screenshot but local to avoid coupling."""
    if not screenshot_bytes or not screenshot_dir:
        return None
    try:
        dir_path = Path(screenshot_dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = "".join(
            c if c.isalnum() or c in ("-", "_") else "_" for c in company_name
        )[:40] or "company"
        path = dir_path / f"{ts}_{safe}_stage15.png"
        path.write_bytes(screenshot_bytes)
        return str(path.resolve())
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_general_form_sender] screenshot save failed (continuing): "
            f"{type(e).__name__}: {e}\n"
        )
        return None


# -----------------------------------------------------------------------------
# Resolution helpers
# -----------------------------------------------------------------------------
# 可視ラベルが共通(例「ご担当者名」)でも placeholder だけが姓/名の分割を示すフォーム用。
# normalize_l1 済みの値で厳密一致する（"名前"等は入れない＝単一フルネーム欄を壊さない）。
# ★カナ分割(セイ/メイ)は kanji を入れると弾かれるため含めない。
_SPLIT_NAME_PH_LAST = {"姓", "名字", "苗字"}
_SPLIT_NAME_PH_FIRST = {"名"}


def _resolve_label_semantic(field: FormField) -> tuple[Optional[str], str]:
    """Resolve a field's semantic via static dictionary first, then learned.

    Returns:
        (semantic, origin) where origin is one of:
            "static"      — found in labels.json
            "learned"     — found in the local label_dictionary table
            ""            — no match
    """
    label = field.label or ""
    name = field.name or ""

    # 分割氏名の優先解決: 可視ラベルが「ご担当者名」等で共通のとき、姓/名の区別は
    # placeholder にしかない。ラベル基準だと「担当」等を含み full name(sender_name)に
    # 吸われ、姓/名 両欄に氏名が入る。明確な姓/名 placeholder はラベルより優先して
    # last/first に確定する（2026-07-09 実フォーム・アシスト検証で発見）。
    ph_n = normalize_l1(getattr(field, "placeholder", "") or "")
    if ph_n in _SPLIT_NAME_PH_LAST:
        return "sender_last_name", "static"
    if ph_n in _SPLIT_NAME_PH_FIRST:
        return "sender_first_name", "static"

    combined = f"{label} {name}".strip()

    semantic = match_label(combined)
    if semantic:
        return semantic, "static"
    if label:
        semantic = match_label(label)
        if semantic:
            return semantic, "static"
    if name:
        semantic = match_label(name)
        if semantic:
            return semantic, "static"

    # Learned dictionary fallback
    if combined:
        learned = match_learned_label(combined)
        if learned:
            return learned, "learned"
    if label:
        learned = match_learned_label(label)
        if learned:
            return learned, "learned"
    if name:
        learned = match_learned_label(name)
        if learned:
            return learned, "learned"

    return None, ""


# -----------------------------------------------------------------------------
# 電話番号の分割入力欄 (市外/市内/加入者番号) 検出 — AIなし・決定論
# -----------------------------------------------------------------------------
_PHONE_HINT_RE = re.compile(r"(tel|phone|denwa|電話|でんわ)", re.IGNORECASE)
_PHONE_SPLIT_MAXLEN = 6  # 小欄判定: maxlength がこれ以下なら分割欄候補
# name の末尾の連番/括弧/区切りを剥がして「名前ファミリ」を得る (tel1/tel[]/tel_3 -> tel)
_NAME_TAIL_RE = re.compile(r"[\[\]()0-9_\-]+$")


def _is_phone_anchor(field: FormField) -> bool:
    """type=tel、または name/label に電話系語彙を含めば電話欄アンカー。"""
    if (field.type or "").lower() == "tel":
        return True
    hay = f"{field.name or ''} {field.label or ''}"
    return bool(_PHONE_HINT_RE.search(hay))


def _name_family(name: str) -> str:
    """name の末尾連番/括弧を除いた語幹。tel1/tel2/tel[] → 'tel'。空なら ''。"""
    if not name:
        return ""
    return _NAME_TAIL_RE.sub("", name.strip().lower())


def _detect_phone_split_groups(fields: list[FormField]) -> list[list[int]]:
    """連続する電話分割欄のグループ(各 length>=2)を fields のインデックスで返す。

    先頭は電話アンカー (_is_phone_anchor)。後続を巻き込む条件は次のいずれか:
      (a) その欄自身も電話アンカー (例: tel1/tel2/tel3、複数の type=tel)。
      (b) 先頭とname語幹が一致 (例: name="tel[]" が3つ、tel_1/tel_2/tel_3)。
      (c) 先頭が小欄(maxlength<=6)で、後続も小欄かつ別セマンティクスに解決しない
          (ラベルが先頭のみに付く 市外/市内/加入者 の3枠パターン)。
    郵便番号(zip1/zip2 等)は電話アンカーにならず語幹も別なので巻き込まない。
    単独の電話欄(length==1)はグループ化せず従来どおりフル番号1欄入力に任せる。
    """
    n = len(fields)
    groups: list[list[int]] = []
    used = [False] * n

    def _small(f: FormField) -> bool:
        ml = getattr(f, "maxlength", 0) or 0
        return 0 < ml <= _PHONE_SPLIT_MAXLEN

    for i in range(n):
        if used[i]:
            continue
        f = fields[i]
        if (f.type or "").lower() not in ("", "text", "tel"):
            continue
        if not _is_phone_anchor(f):
            continue
        anchor_family = _name_family(f.name)
        anchor_small = _small(f)
        run = [i]
        j = i + 1
        while j < n:
            g = fields[j]
            if (g.type or "").lower() not in ("", "text", "tel"):
                break
            g_family = _name_family(g.name)
            same_family = bool(anchor_family) and g_family == anchor_family
            if _is_phone_anchor(g) or same_family:
                run.append(j)
                j += 1
                continue
            # ラベル無しの小欄: 先頭も小欄で、別セマンティクスに解決しない場合のみ巻き込む
            if anchor_small and _small(g):
                sem, _ = _resolve_label_semantic(g)
                if sem and sem != "phone":
                    break
                run.append(j)
                j += 1
                continue
            break
        if len(run) >= 2:
            for k in run:
                used[k] = True
            groups.append(run)
    return groups


def _build_phone_split_overrides(
    fields: list[FormField],
    fill_data: FillData,
) -> dict[int, str]:
    """分割電話欄の {fields index -> その欄へ入れる値} を返す。分割不能なら空 dict。"""
    phone = fill_data.get("phone")
    if not phone:
        return {}
    overrides: dict[int, str] = {}
    for run in _detect_phone_split_groups(fields):
        parts = split_phone_value(phone, len(run))
        if not parts or len(parts) != len(run):
            # 分割できない → このグループは従来動作(各欄フル番号)にフォールバック
            continue
        for idx, part in zip(run, parts):
            overrides[idx] = part
    return overrides


def _build_address_dedup_skips(
    fields: list[FormField],
    fill_data: FillData,
) -> set[int]:
    """複数の text/textarea 欄が同一 address 値に解決する場合、先頭1欄だけ残し
    以降をスキップする fields index 集合を返す。

    送信者住所は1本(例『愛知県名古屋市中区』)しか持たないため、'番地' や
    'マンション名等' の欄にも同じ都道府県+市区町村が重複充填されてしまう。
    番地・建物名は不明なので空のままにする方が安全（実フォーム eo-marketing の
    form_address/form_address2/form_address3 で発見・2026-07-10）。
    prefecture 等の select は対象外（住所からのファジー一致で個別に解決するため）。
    """
    if not fill_data.get("address"):
        return set()
    skips: set[int] = set()
    seen_first = False
    for idx, f in enumerate(fields):
        if (f.type or "").lower() not in ("", "text", "textarea"):
            continue
        value, semantic, _ = _field_resolution_value(f, fill_data)
        if semantic == "address" and value:
            if seen_first:
                skips.add(idx)
            else:
                seen_first = True
    return skips


def _field_resolution_value(
    field: FormField,
    fill_data: FillData,
) -> tuple[Optional[str], Optional[str], str]:
    """Return (value, semantic, origin) for one field.

    The origin tags how the semantic was resolved (or empty for unresolved).
    """
    # HTML type signals (email / tel / url) override semantic-by-label
    ftype = (field.type or "").lower()
    if ftype == "email":
        return fill_data.get("email"), "email", "static"
    if ftype == "tel":
        return fill_data.get("phone"), "phone", "static"
    if ftype == "url":
        return fill_data.get("companyUrl"), "company_url", "static"

    # radio/checkbox は「選択肢」を選ぶ欄であり、識別情報(氏名/URL/会社名等)を流し込む
    # 対象ではない。ラベル意味がたまたま identity に当たっても、その text 値は選択肢に
    # 一致せず（radio は "option not found"、checkbox は型エラーで)skip され、必須選択欄を
    # “埋めたつもり”にして送信失敗やアシスト送りを増やす。→ None を返し、選択値は
    # 未解決欄として options 採取 → サーバー解決 / field_decisions / auto_default /
    # ④式ハンドオフ側に委ねる。
    # ※ select は除外（都道府県等が送信者住所からファジー一致で正しく埋まる既存挙動を保つ）。
    if ftype in ("radio", "checkbox"):
        # 選択肢欄はここでは解決しない。checkbox の同意ゲートは後段で処理する
        # （server resolve_fields の consent_agreement ＋ ローカル seed フォールバック）。
        return None, None, ""

    semantic, origin = _resolve_label_semantic(field)
    if not semantic:
        # ラベルが辞書に無い textarea は本文欄とみなして message を流し込む。
        # （以前はこの分岐より前の early return に阻まれ fallback が死んでいた。
        #  Shopify「コメント」等、辞書に無い本文欄が常に空になる不具合の修正。）
        if ftype == "textarea":
            msg = fill_data.get("message") or None
            if msg:
                return msg, "message_body", "fallback"
        return None, None, ""
    value = _semantic_to_value(semantic, fill_data)
    if value is None and ftype == "textarea":
        # ラベルは当たったが値が無い textarea も本文へフォールバック。
        value = fill_data.get("message") or None
        if value:
            return value, "message_body", "static"
    return value, semantic, origin


# -----------------------------------------------------------------------------
# Confirmation page handling (minimal port of handleConfirmationPage)
# -----------------------------------------------------------------------------
async def _click_confirm_if_present(page: Any) -> Optional[str]:
    """Look for a 確認/Next button and click it. Returns the selector used."""
    candidates = [
        'button:has-text("確認する")',
        'button:has-text("確認画面")',
        'button:has-text("確認")',
        'button:has-text("次へ")',
        'button:has-text("Next")',
        'input[type="submit"][value*="確認"]',
    ]
    for sel in candidates:
        try:
            locator = page.locator(sel).first
            if await locator.count() == 0:
                continue
            await locator.click(timeout=2_000)
            await page.wait_for_load_state("domcontentloaded", timeout=5_000)
            return sel
        except BaseException:  # noqa: BLE001 — best effort, try next candidate
            continue
    return None


# -----------------------------------------------------------------------------
# Success signal detection
# -----------------------------------------------------------------------------
def _build_success_keywords() -> list[str]:
    """送信完了を示す語彙。確認画面の語(「以下の内容で送信」「入力内容をご確認」等)は
    含めない — 含めると確認ページを完了と誤検知し早期に成功扱いしてしまうため
    (confirmation-signals.json は確認画面検知用で成功検知用ではない)。"""
    keywords: list[str] = []
    try:
        dyn = load_dynamic_detection() or {}
        for section_name in ("successKeywords", "successContent"):
            section = dyn.get(section_name) or {}
            for alias in section.get("aliases", []):
                if alias and alias not in keywords:
                    keywords.append(alias)
    except BaseException:  # noqa: BLE001 — best effort
        pass
    for fallback in (
        "送信完了", "送信が完了", "送信しました", "送信されました",
        "送信を受け付け", "受け付けました", "受付けました", "受付完了",
        "お問い合わせありがとう", "お問合せありがとう", "お問い合わせを受け付け",
        "ありがとうございました", "完了しました", "正常に送信",
        "Thank you", "thank you", "successfully", "has been sent", "been received",
    ):
        if fallback not in keywords:
            keywords.append(fallback)
    return keywords


async def _wait_for_success(page: Any, timeout_ms: int, *, check_gone=None) -> bool:
    """Poll the page for success indicators.

    check_gone: 任意の async callable。送信後にフォーム入力欄が消えた(=完了ページへ
    置換された)ことを示す True を返したら成功とみなす。語彙に依存しない頑健な信号。
    """
    keywords = _build_success_keywords()
    url_pats = (
        "/thanks", "/thank", "/complete", "/completed", "/done", "/success",
        "/finish", "/sent", "mail_sent", "=thanks", "=complete", "/thankyou",
    )
    deadline = time.time() + (timeout_ms / 1000.0)
    while time.time() < deadline:
        try:
            content = await page.content()
            if any(kw in content for kw in keywords):
                return True
            url = page.url
            if isinstance(url, str):
                ul = url.lower()
                if any(k in ul for k in url_pats):
                    return True
        except BaseException:  # noqa: BLE001 — page may be navigating
            pass
        if check_gone is not None:
            try:
                if await check_gone():
                    return True
            except BaseException:  # noqa: BLE001
                pass
        await asyncio.sleep(_SUCCESS_POLL_INTERVAL_MS / 1000.0)
    return False


# -----------------------------------------------------------------------------
# Submit button discovery
# -----------------------------------------------------------------------------
async def _find_submit_selector(page: Any) -> Optional[str]:
    """最終送信ボタンのセレクタを多段検出する（Tier A）。

    native(submit/image) → テキスト一致(button / input[value] / role=button) →
    class ベース → 多段フォーム用 fallback(確認/次へ) の順。
    負語(戻る/修正/キャンセル等)を含むボタンは送信ではないので除外する。
    Returns the CSS selector actually used (so callers can persist it).
    """
    positive: list[str] = []
    fallback: list[str] = []
    negative: list[str] = []
    try:
        sb = load_submit_buttons()
        positive.extend(sb.get("positive", {}).get("aliases", []) or [])
        fallback.extend(sb.get("fallback", {}).get("aliases", []) or [])
        negative.extend(sb.get("negative", {}).get("aliases", []) or [])
    except BaseException:  # noqa: BLE001
        pass
    # quote を含む alias は CSS を壊すので除外（ラジオ BADSTRING の教訓）。
    positive = [a for a in dict.fromkeys(positive) if a and '"' not in a]
    fallback = [a for a in dict.fromkeys(fallback) if a and '"' not in a and a not in positive]

    async def _hit(sel: str) -> bool:
        try:
            loc = page.locator(sel).first
            if await loc.count() == 0:
                return False
            # 負語(戻る/キャンセル等)を含む要素は送信ボタンではない。
            try:
                txt = (await loc.inner_text(timeout=800)) or ""
            except BaseException:  # noqa: BLE001
                txt = ""
            if txt and any(neg and neg in txt for neg in negative):
                return False
            return True
        except BaseException:  # noqa: BLE001
            return False

    # 1. Native submit / image submit
    for selector in (
        'button[type="submit"]',
        'input[type="submit"]',
        'input[type="image"]',
    ):
        if await _hit(selector):
            return selector

    def _cands(alias: str) -> list[str]:
        return [
            f'button:has-text("{alias}")',
            f'input[type="button"][value*="{alias}"]',
            f'input[type="submit"][value*="{alias}"]',
            f'[role="button"]:has-text("{alias}")',
        ]

    # 2. 最終送信語(positive)を element 種別横断で
    for alias in positive:
        for sel in _cands(alias):
            if await _hit(sel):
                return sel

    # 3. class ベース（CF7 / 一般的な submit ボタン class）
    for css in (
        'button.wpcf7-submit', 'input.wpcf7-submit',
        'button.submit', 'button.btn-submit', 'button.btn_submit',
        '.submit-btn', '.btnSubmit', '.c-btn--submit',
    ):
        if await _hit(css):
            return css

    # 4. 多段フォーム用 fallback(確認/次へ/進む) — 最後の手段
    for alias in fallback:
        for sel in _cands(alias):
            if await _hit(sel):
                return sel
    return None


# -----------------------------------------------------------------------------
# Provider abstract entry — imported lazily to avoid circular import
# -----------------------------------------------------------------------------
class LocalGeneralFormProvider:
    """Stage 1.5 — generic form pattern-matching sender.

    Inherits the canonical Provider shape (status/error_reason/screenshot_path/
    ended_at/provider_used) but does NOT inherit from FormSendProvider to keep
    the module independent of _skill_core (avoids circular import during
    Sprint 6 Task 7). HybridProvider uses duck typing via .send().
    """

    def __init__(self) -> None:
        # Pre-load the learned dictionary so the first send doesn't pay for it.
        try:
            load_learned_dictionary()
        except BaseException:  # noqa: BLE001 — best effort
            pass

    async def send(
        self,
        company_name: str,
        url: str,
        message: str,
        sender_info: dict,
        *,
        screenshot_dir: Optional[str] = None,
        field_decisions: Optional[dict] = None,
        auto_default: bool = False,
    ) -> dict:
        """Thin wrapper for `_send_impl`.

        最終的な error_reason に PII / API キー断片が紛れないよう、
        _send_impl の戻り値に sanitize を一括適用する Safety Net。

        field_decisions: ④式ハンドオフでユーザーの Claude Code が決めた
          {欄ラベル: 選んだ値} 。未知の必須/select/radio をアシストに回す前に充填する。
        auto_default: True のとき、未解決の select/radio に汎用問い合わせの
          無難な選択肢（その他/お問い合わせ等）を AI なしで自動選択する（batch 向け）。
        """
        result = await self._send_impl(
            company_name=company_name,
            url=url,
            message=message,
            sender_info=sender_info,
            screenshot_dir=screenshot_dir,
            field_decisions=field_decisions,
            auto_default=auto_default,
        )
        if isinstance(result, dict) and result.get("error_reason"):
            result["error_reason"] = _sanitize_text(result["error_reason"], sender_info)
        return result

    async def _send_impl(
        self,
        company_name: str,
        url: str,
        message: str,
        sender_info: dict,
        *,
        screenshot_dir: Optional[str] = None,
        field_decisions: Optional[dict] = None,
        auto_default: bool = False,
    ) -> dict:
        provider_used = "general_form"

        # Step 0: short-circuit if URL is empty (defensive)
        if not url:
            return _result(
                status="failed",
                provider_used="none",
                error_reason="url is empty",
            )

        origin = origin_for_url(url) or ""
        if origin and await _domain_in_cooldown(origin):
            return _result(
                status="skipped",
                provider_used="none",
                error_reason="domain_cooldown",
            )

        # Step 1: reachability check
        try:
            reach = await classify_reachability(url, skip_robots=True)
        except BaseException as e:  # noqa: BLE001 — Fail Safe
            return _result(
                status="failed",
                provider_used=provider_used,
                error_reason=f"reachability_error:{type(e).__name__}",
            )
        if reach.status == "site_not_found":
            return _result(
                status="skipped",
                provider_used="none",
                error_reason="site_not_found",
            )
        if reach.status == "waf_403":
            return _result(
                status="failed",
                provider_used="none",
                error_reason="waf_403",
            )
        if reach.status == "transient_5xx":
            return _result(
                status="failed",
                provider_used="none",
                error_reason=f"transient_5xx:{reach.http_code}",
            )
        if reach.status == "network_error":
            return _result(
                status="failed",
                provider_used="none",
                error_reason="network_error",
            )
        if reach.status == "robots_disallow":
            return _result(
                status="skipped",
                provider_used="none",
                error_reason="robots_disallow",
            )

        # Step 2: launch Playwright + run the actual send
        try:
            from playwright.async_api import async_playwright  # type: ignore
        except ImportError:
            return _result(
                status="failed",
                provider_used=provider_used,
                error_reason=(
                    "playwright not installed: run `uv sync` and then "
                    "`playwright install chromium` inside skill/."
                ),
            )

        fill_data: FillData = dict(sender_info)  # type: ignore[assignment]
        fill_data["message"] = message

        screenshot_bytes: Optional[bytes] = None
        outcome: dict = _result(
            status="failed",
            provider_used=provider_used,
            error_reason="unknown",
        )

        async with async_playwright() as pw:
            try:
                browser = await pw.chromium.launch(
                    headless=_resolve_headless_mode(),
                )
            except BaseException as e:  # noqa: BLE001 — Fail Safe
                return _result(
                    status="failed",
                    provider_used=provider_used,
                    error_reason=f"browser_launch_failed:{type(e).__name__}",
                )
            try:
                context = await browser.new_context(
                    viewport=_DEFAULT_VIEWPORT,
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/121.0.0.0 Safari/537.36"
                    ),
                    locale="ja-JP",
                )
                page = await context.new_page()
                try:
                    await page.goto(
                        url, timeout=_PAGE_NAVIGATION_TIMEOUT_MS,
                        wait_until="domcontentloaded",
                    )
                except BaseException as e:  # noqa: BLE001
                    outcome = _result(
                        status="failed",
                        provider_used=provider_used,
                        error_reason=f"goto_failed:{type(e).__name__}",
                    )
                else:
                    outcome = await self._run_stage_15(
                        page=page,
                        company_name=company_name,
                        url=url,
                        origin=origin,
                        fill_data=fill_data,
                        message=message,
                        field_decisions=field_decisions,
                        auto_default=auto_default,
                    )

                # Always try to capture a screenshot before close
                try:
                    screenshot_bytes = await page.screenshot(full_page=False)
                except BaseException:  # noqa: BLE001 — best effort
                    pass
                await context.close()
            finally:
                try:
                    await browser.close()
                except BaseException:  # noqa: BLE001 — best effort
                    pass

        # Step 3: persist screenshot + update domain cooldown counters
        sp = _save_screenshot_bytes(screenshot_bytes, screenshot_dir, company_name)
        if sp:
            outcome["screenshot_path"] = sp

        if origin:
            if outcome["status"] == "completed":
                record_success(origin)
                await _report_domain_outcome(
                    origin,
                    "success",
                    fingerprint=outcome.get("_fingerprint") or "",
                    learned=outcome.get("_learned") or None,
                    workflow=outcome.get("_workflow") or None,
                )
            elif outcome["status"] == "failed":
                record_failure(origin)
                await _report_domain_outcome(
                    origin, "failed", outcome.get("error_reason") or ""
                )

        return outcome

    # -------------------------------------------------------------------------
    # The bulk of the work — runs after page.goto() has succeeded
    # -------------------------------------------------------------------------
    async def _run_stage_15(
        self,
        *,
        page: Any,
        company_name: str,
        url: str,
        origin: str,
        fill_data: FillData,
        message: str,
        field_decisions: Optional[dict] = None,
        auto_default: bool = False,
    ) -> dict:
        provider_used = "general_form"

        # 0. 営業禁止の再チェック（防御の二重化）。HTTP 段で取得失敗して Stage 1.5 に
        #    落ちた社でも、ここで実ページの HTML を見て「営業お断り」なら送らずスキップ。
        try:
            _html = await page.content()
            if check_prohibition(_html):
                return _result(
                    status="skipped",
                    provider_used="none",
                    error_reason="prohibition_detected",
                )
        except BaseException:  # noqa: BLE001 — Fail Safe（チェック失敗は送信を止めない）
            pass

        # 4. Bot protection probe (blocking types -> early skip)
        bot = await detect_bot_protection(page)
        if bot.get("detected") and bot.get("blocking"):
            reason = bot.get("type") or "unknown"
            return _result(
                status="skipped",
                provider_used="none",
                error_reason=f"bot_protection:{reason}",
            )

        # 5. Workflow cache lookup -> replay if hit
        try:
            fingerprint = await compute_form_fingerprint(page)
        except BaseException:  # noqa: BLE001 — Fail Safe
            fingerprint = None

        # workflow_cache の replay は本番実績 9試行0成功で、記録された欄マッピングが
        # 壊れている(本文欄に company_url/email が割り当たっている行が実在する)。
        # 既定は読まない。検証用にだけ AUTOFORM_WORKFLOW_CACHE=1 で開ける。
        if fingerprint and origin and os.environ.get("AUTOFORM_WORKFLOW_CACHE") == "1":
            cached = lookup_workflow(origin, fingerprint)
            if cached:
                replay = await replay_workflow(page, cached, fill_data)
                if replay.get("success"):
                    return _result(
                        status="completed",
                        provider_used="workflow_cache",
                    )
                # Replay failed -> demote and fall through to fresh general_form run
                record_workflow_failure(origin, fingerprint)

        # 6. Form detection
        # JS描画 / 遅延iframe(formzu・Googleフォーム等の埋め込み)対策:
        # メインまたは iframe のいずれかに入力欄が現れるまで待つ（domcontentloaded
        # 直後は未描画/未ロードのことがある）。出なければそのまま form_not_found 判定へ。
        # 「どれかの frame に 3 欄以上(=実フォームらしい)」が現れるまで待つ。
        # メイン frame の単独 input(検索欄など)で早期 break して、遅延ロードの
        # iframe フォーム(formzu等)を取りこぼすのを防ぐ。出なければ続行。
        # ★無限ハング対策(#38): 地図/YouTube/広告等の埋め込み iframe は Playwright から
        # 「実行コンテキスト未確定のゴーストフレーム」に見え、locator.count() が timeout を
        # 持たず永久待機する（例外も投げないので Fail Safe で救えない）。各 frame 操作を
        # asyncio.wait_for で打ち切り、応答しない frame はその社の間だけ dead-set に記録して
        # 二度と触らない。URLで skip しない（formzu/Googleフォーム等の正規埋め込みが空URLで
        # 現れうるため）—「応答するか」で切るのが安全。
        _field_sel = "input:not([type=hidden]):not([type=search]), textarea, select"
        _dead_frames: set = set()
        _deadline = time.monotonic() + 6.0
        while time.monotonic() < _deadline:
            _ready = False
            for _fr in page.frames:
                if _fr in _dead_frames:
                    continue
                try:
                    _n = await asyncio.wait_for(
                        _fr.locator(_field_sel).count(),
                        timeout=_FRAME_OP_TIMEOUT_S,
                    )
                    if _n >= 3:
                        _ready = True
                        break
                except asyncio.TimeoutError:  # 応答しないゴーストフレーム → 以降スキップ
                    _dead_frames.add(_fr)
                    continue
                except BaseException:  # noqa: BLE001 — detached/navigating frame
                    continue
            if _ready:
                break
            await asyncio.sleep(0.4)

        fields, form_frame = await analyze_form(page)
        if not fields:
            return _result(
                status="failed",
                provider_used=provider_used,
                error_reason="form_not_found",
            )

        # 7-8. Resolve each field via static + local-learned, then central learned dict.
        field_mapping: list[dict] = []
        # (field, options) のうち、ローカル辞書で解けなかったもの。サーバー2次解決へ回す。
        unresolved_fields: list = []
        # learned_entries collects rows for accumulate_on_success on success.
        learned_entries: list[dict] = []

        # 電話分割欄 (市外/市内/加入者番号) の値割り当てを事前計算 (AIなし・決定論)。
        # {fields index -> その欄へ入れる分割値}。分割不能なら空で従来動作にフォールバック。
        phone_split_overrides = _build_phone_split_overrides(fields, fill_data)
        # 複数の住所欄 (都道府県市区町村/番地/建物名) が同一住所に解決する重複を防ぐ。
        # 先頭1欄だけ充填し、以降は空のまま（送信者住所は1本しか無いため）。
        address_dedup_skips = _build_address_dedup_skips(fields, fill_data)
        # 同名 (name="tel[]" 等) の重複セレクタを nth で打ち分けるためのカウンタ。
        _selector_seen: dict[str, int] = {}

        for _idx, field in enumerate(fields):
            _sel_occurrence = _selector_seen.get(field.selector, 0)
            _selector_seen[field.selector] = _sel_occurrence + 1

            # 重複住所欄: 先頭以外は充填しない（未解決にも回さず空のまま）。
            if _idx in address_dedup_skips:
                continue

            # 分割電話欄: 事前計算した分割値を使い、通常解決/未解決フローを飛ばす。
            if _idx in phone_split_overrides:
                field_mapping.append({
                    "selector": field.selector,
                    "semantic": "phone",
                    "valueHint": phone_split_overrides[_idx],
                    "type": field.type,
                    "label": field.label,
                    "name": field.name,
                    "nth": _sel_occurrence,
                })
                continue

            value, semantic, origin_tag = _field_resolution_value(field, fill_data)
            if value is not None and semantic:
                field_mapping.append({
                    "selector": field.selector,
                    "semantic": semantic,
                    "valueHint": value,
                    "type": field.type,
                    "label": field.label,
                    "name": field.name,
                })
                # Only learned/ai_resolved entries get persisted
                if origin_tag == "learned" and field.label:
                    learned_entries.append({
                        "normalized_label": normalize_l1(field.label),
                        "semantic": semantic,
                        "origin": "learned",
                    })
                continue
            # ローカル辞書で解けない欄。options を採取してサーバー2次解決へ回す。
            options = await self._extract_options(form_frame, field)
            unresolved_fields.append((field, options))

        # 8. 中央学習辞書による2次解決（OpenAI form-reasoning は step3 で撤去）。
        # サーバー resolve_fields に未解決ラベルをまとめて問い合わせ、当たれば充填。
        # 当たらない欄は AI で推測せず、ブロッキング（必須 / select / radio）なら
        # 人間アシストキューへ回す（未知欄＝③式だがバッチ実行は辞書のみ→assist）。
        blocking_unknowns: list[dict] = []
        if unresolved_fields:
            payload_fields = [
                {"label": f.label or "", "type": f.type, "options": opts}
                for (f, opts) in unresolved_fields
            ]
            rf = await _server_client.resolve_fields(fingerprint, payload_fields)
            resolved_map: dict[str, str] = {}
            if rf:
                for item in rf.get("resolved") or []:
                    lbl = item.get("label")
                    sem = item.get("semantic")
                    if lbl and sem:
                        resolved_map[lbl] = sem
            for (f, opts) in unresolved_fields:
                sem = resolved_map.get(f.label or "")
                _ftype = (f.type or "").lower()
                # 同意/承諾ゲート: サーバーが consent_agreement を返した、または
                # ローカル最小 seed に当たる checkbox は自動チェック（value はダミー、
                # _fill_field の checkbox ブランチが ON にする）。語彙の育成はサーバー側。
                if _ftype == "checkbox" and (
                    sem == "consent_agreement" or _is_consent_label(f.label)
                ):
                    field_mapping.append({
                        "selector": f.selector,
                        "semantic": "consent_agreement",
                        "valueHint": "on",
                        "type": f.type,
                        "label": f.label,
                        "name": f.name,
                    })
                    continue
                # 非 consent の checkbox は識別セマンティクス(email/name 等)に誤解決されても
                # 埋めない（_fill_field の checkbox ブランチは値に関係なく ON にするため、
                # 「メールマガジンを希望する」等の任意 opt-in を勝手にチェックしてしまう）。
                # 選択は consent ゲートに限定し、それ以外の checkbox は未処理（未チェック）で残す。
                if _ftype == "checkbox":
                    continue
                val = _semantic_to_value(sem, fill_data) if sem else None
                if sem and val is not None:
                    field_mapping.append({
                        "selector": f.selector,
                        "semantic": sem,
                        "valueHint": val,
                        "type": f.type,
                        "label": f.label,
                        "name": f.name,
                    })
                    if f.label:
                        learned_entries.append({
                            "normalized_label": normalize_l1(f.label),
                            "semantic": sem,
                            "origin": "learned",
                        })
                    continue
                # ④式ハンドオフ: 会話側 Claude が決めた値があれば充填（label 正規化一致）。
                decided = _lookup_decision(field_decisions, f.label)
                if decided is not None and str(decided) != "":
                    field_mapping.append({
                        "selector": f.selector,
                        "semantic": "claude_decision",
                        "valueHint": decided,
                        "type": f.type,
                        "label": f.label,
                        "name": f.name,
                    })
                    continue
                # まだ未知。必須 or select/radio は送信を阻むのでアシスト対象。
                ftype = (f.type or "").lower()
                if bool(getattr(f, "required", False)) or ftype in (
                    "select", "select-one", "radio"
                ):
                    # batch 安全フォールバック（任意）: 汎用問い合わせの無難な選択肢を
                    # AI なしで自動選択。対話運用では既定 OFF＝Claude ハンドオフに回す。
                    if auto_default and ftype in ("select", "select-one", "radio"):
                        dv = default_inquiry_option(opts)
                        if dv:
                            field_mapping.append({
                                "selector": f.selector,
                                "semantic": "heuristic_default",
                                "valueHint": dv,
                                "type": f.type,
                                "label": f.label,
                                "name": f.name,
                            })
                            continue
                    blocking_unknowns.append({
                        "label": f.label or "",
                        "type": f.type,
                        "options": opts,
                    })

        # 8c. ブロッキング未知欄が残る → 自動では送らず人間アシストへ誘導（AI不使用）。
        if blocking_unknowns:
            return _result(
                status="failed",
                provider_used=provider_used,
                error_reason="unknown_fields:needs_assist",
                trace_detail={
                    "form_url": url,
                    "fields_detected": [
                        f.label for f in fields if getattr(f, "label", "")
                    ],
                    "fields_unmapped": [u["label"] for u in blocking_unknowns],
                    "unknown_fields": blocking_unknowns,
                },
            )

        # 診断トレース（純観測）: 検出した欄を「マッチした/しなかった」で仕分ける。
        # fields_unmapped が辞書追加候補の原材料になる（trace_report が提示）。
        _detected_labels = [f.label for f in fields if getattr(f, "label", "")]
        _mapped_labels = [m.get("label") for m in field_mapping if m.get("label")]
        trace_detail = {
            "form_url": url,
            "fields_detected": _detected_labels,
            "fields_mapped": _mapped_labels,
            "fields_unmapped": [
                lbl for lbl in _detected_labels if lbl not in _mapped_labels
            ],
        }

        if not field_mapping:
            return _result(
                status="failed",
                provider_used=provider_used,
                error_reason="field_mapping",
                trace_detail=trace_detail,
            )

        # 9. Fill form
        filled_count = 0
        _fill_failed: list[str] = []
        _body_failed = False
        for entry in field_mapping:
            selector = entry["selector"]
            value = entry["valueHint"]
            field_type = (entry.get("type") or "").lower()
            try:
                await _fill_field(
                    form_frame, field_type, selector, value,
                    entry.get("name"), entry.get("nth"),
                )
                filled_count += 1
            except BaseException as e:  # noqa: BLE001 — Fail Safe
                sys.stderr.write(
                    f"[_general_form_sender] fill failed {selector!r}: "
                    f"{type(e).__name__}: {e}\n"
                )
                # ラベルは親/兄弟の innerText 由来で数千文字になる実例があるため切る。
                _lbl = str(entry.get("label") or selector)[:60]
                _fill_failed.append(f"{_lbl}:{type(e).__name__}")
                if entry.get("semantic") == "message_body":
                    _body_failed = True

        trace_detail["fields_filled_count"] = filled_count
        if _fill_failed:
            trace_detail["fields_fill_failed"] = _fill_failed

        # 本文欄が入らないまま送るのは「営業文の無い問い合わせ」を確定送信すること。
        # 実trace 1604行で、送信完了292件のうち45件(15.4%)が一部欄未充填のまま
        # completed になっていた。本文だけは落ちたら送らない(送信率は下がる＝意図)。
        if _body_failed:
            return _result(
                status="failed",
                provider_used=provider_used,
                error_reason="field_mapping:message_body_fill_failed",
                trace_detail=trace_detail,
            )

        if filled_count == 0:
            return _result(
                status="failed",
                provider_used=provider_used,
                error_reason="field_mapping",
                trace_detail=trace_detail,
            )

        # 10. Optional CAPTCHA solver (Sprint 6 §3-5)
        try:
            captcha_result = await prepare_captcha_for_submission(page, bot)
            if captcha_result.get("status") not in ("passed", "skipped", "not_found"):
                # Error: continue anyway; the submit may still go through
                sys.stderr.write(
                    f"[_general_form_sender] captcha solver: "
                    f"{captcha_result}\n"
                )
        except BaseException as e:  # noqa: BLE001 — Fail Safe
            sys.stderr.write(
                f"[_general_form_sender] captcha probe error: "
                f"{type(e).__name__}: {e}\n"
            )

        # 11. Confirm button (minimal — single press)
        confirm_selector = await _click_confirm_if_present(form_frame)

        # 12. Submit
        submit_selector = await _find_submit_selector(form_frame)
        if not submit_selector:
            return _result(
                status="failed",
                provider_used=provider_used,
                error_reason="submit_button_not_found",
                trace_detail=trace_detail,
            )
        # 送信後に「フォーム欄が消えた＝完了ページへ置換」を完了signalにするため、
        # 送信前の入力欄数を記録（語彙に依存しない頑健な検知）。
        try:
            _pre_fields = await form_frame.locator(
                "input:not([type=hidden]):not([type=search]), textarea"
            ).count()
        except BaseException:  # noqa: BLE001
            _pre_fields = 0
        try:
            # セレクタが複数一致しても strict mode で落ちないよう first をクリック。
            await form_frame.locator(submit_selector).first.click(
                timeout=_FIELD_FILL_TIMEOUT_MS
            )
        except BaseException as e:  # noqa: BLE001 — Fail Safe
            return _result(
                status="failed",
                provider_used=provider_used,
                error_reason=f"submit_click_failed:{type(e).__name__}",
                trace_detail=trace_detail,
            )

        # 13. Success detection（語彙 / URL / 「フォーム欄消失」のいずれも完了とみなす。
        # iframeは frame 内完了表示、通常はページ遷移するため form_frame と page を両方見る）
        async def _form_gone() -> bool:
            if _pre_fields <= 0:
                return False
            try:
                return await form_frame.locator(
                    "input:not([type=hidden]):not([type=search]), textarea"
                ).count() == 0
            except BaseException:  # noqa: BLE001
                return False

        ok = await _wait_for_success(
            form_frame, _SUCCESS_WAIT_TIMEOUT_MS, check_gone=_form_gone
        )
        if not ok and form_frame is not getattr(page, "main_frame", page):
            ok = await _wait_for_success(page, 2500)
        if not ok:
            # 送信は押したが完了確認できず — confirmation_unclear（人間確認候補）。
            return _result(
                status="failed",
                provider_used=provider_used,
                error_reason="submit_stuck:no_confirmation",
                trace_detail=trace_detail,
            )

        # 14. Success bookkeeping
        try:
            if learned_entries:
                accumulate_on_success(learned_entries)
        except BaseException:  # noqa: BLE001 — Fail Safe
            pass

        success_workflow: Optional[dict] = None
        if fingerprint and origin:
            try:
                success_workflow = build_workflow_from_general_form_success(
                    fingerprint=fingerprint,
                    field_mapping=[
                        {
                            "selector": e["selector"],
                            "semantic": e["semantic"],
                            # valueHint(=各社宛の営業本文と送信者の氏名/メール/電話/住所)
                            # は記録しない。replay 側は resolver しか使わないので
                            # 読まれることが無く、ローカルDBと共有D1に PII を残すだけ。
                            "type": e.get("type"),
                        }
                        for e in field_mapping
                    ],
                    submit_selector=submit_selector,
                    confirm_button_selector=confirm_selector,
                )
                record_successful_workflow(
                    origin, fingerprint, success_workflow, "general_form"
                )
            except BaseException:  # noqa: BLE001 — Fail Safe
                pass

        res = _result(
            status="completed",
            provider_used=provider_used,
            trace_detail=trace_detail,
        )
        # 中央学習への書き戻し材料を結果に載せる。外側の単一 _report_domain_outcome が
        # ここから learned[] / workflow / fingerprint を拾って 1 回だけ送る（二重カウント防止）。
        res["_learned"] = learned_entries
        res["_fingerprint"] = fingerprint or ""
        if success_workflow:
            res["_workflow"] = success_workflow
        return res

    async def _extract_options(self, page: Any, field: FormField) -> list[str]:
        """Best-effort option extraction for select/radio fields."""
        if not field.selector:
            return []
        ftype = (field.type or "").lower()
        if ftype in ("select", "select-one"):
            try:
                values = await page.evaluate(
                    "(sel) => Array.from(document.querySelector(sel)?.options || [])"
                    ".map(o => o.value).filter(v => v)",
                    field.selector,
                )
                if isinstance(values, list):
                    return [str(v) for v in values if v]
            except BaseException:  # noqa: BLE001
                return []
        if ftype == "radio" and field.name:
            try:
                values = await page.evaluate(
                    "(n) => Array.from(document.querySelectorAll("
                    "  'input[type=\\\"radio\\\"][name=\\\"' + n + '\\\"]'))"
                    ".map(r => r.value)",
                    field.name,
                )
                if isinstance(values, list):
                    return [str(v) for v in values if v]
            except BaseException:  # noqa: BLE001
                return []
        return []
