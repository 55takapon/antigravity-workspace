"""Sprint 5 Task 3 — CF7 detection + HTTP POST sender (Python port).

Ports `src/lib/http-post/cf7-detector.ts` and `cf7-sender.ts` into Python.
Adds:
  - Bot protection detection (Cloudflare Turnstile, hCaptcha)
  - Default request headers (ja-JP locale + Chrome 121 UA)
  - Pre-POST anti-spam delay (2-5s, OFF via AUTOFORM_DELAY_DISABLED=1)
  - Prohibition early-skip via _pattern_loader.check_prohibition

NOTE: Sync with src/lib/http-post/cf7-detector.ts + cf7-sender.ts +
src/lib/browser/engine.ts (User-Agent).
"""

from __future__ import annotations

import asyncio
import os
import random
import re
from dataclasses import dataclass, field
from typing import Optional, Union
from urllib.parse import urlparse

import httpx

# Sprint 6 Task 0: dual import — package context (skill.core.*) vs flat
# sys.path (skill/scripts/run_send.py inserts skill/core/ into sys.path).
try:
    from skill.core._form_filler_lite import FillData, FormField, determine_value
    from skill.core._pattern_loader import check_prohibition
except ImportError:
    from _form_filler_lite import FillData, FormField, determine_value  # type: ignore
    from _pattern_loader import check_prohibition  # type: ignore

# -----------------------------------------------------------------------------
# Default HTTP headers
# -----------------------------------------------------------------------------
# NOTE: Sync User-Agent with src/lib/browser/engine.ts (Chrome 121).
_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)
_DEFAULT_HEADERS: dict[str, str] = {
    "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.5",
    "User-Agent": _DEFAULT_USER_AGENT,
}

# -----------------------------------------------------------------------------
# Timeouts and delay
# -----------------------------------------------------------------------------
_HTTP_TIMEOUT_SEC = 10.0
_DELAY_MIN_SEC = 2.0
_DELAY_MAX_SEC = 5.0


def _delay_disabled() -> bool:
    return os.environ.get("AUTOFORM_DELAY_DISABLED", "").strip() == "1"


async def _anti_spam_sleep() -> None:
    """Sleep between 2 and 5 seconds unless AUTOFORM_DELAY_DISABLED=1."""
    if _delay_disabled():
        return
    await asyncio.sleep(random.uniform(_DELAY_MIN_SEC, _DELAY_MAX_SEC))


# -----------------------------------------------------------------------------
# Types
# -----------------------------------------------------------------------------
@dataclass
class Cf7FormField:
    """Mirrors cf7-detector.ts Cf7FormField (L9-13)."""

    name: str
    type: str
    label: str = ""


@dataclass
class Cf7DetectionResult:
    """Mirrors cf7-detector.ts Cf7DetectionResult (L15-22)."""

    is_cf7: bool
    form_id: Optional[str]
    fields: list[Cf7FormField] = field(default_factory=list)
    hidden_fields: dict[str, str] = field(default_factory=dict)
    has_recaptcha: bool = False
    action_url: Optional[str] = None


@dataclass
class Cf7SendResult:
    """Sprint 5-extended result type.

    Status values:
        completed              -> HTTP POST succeeded (mail_sent)
        validation_failed      -> CF7 returned validation_failed
        mail_failed            -> CF7 returned mail_failed
        error                  -> HTTP / network error
        bot_protection         -> Turnstile or hCaptcha detected
        prohibition_detected   -> prohibition keyword found in HTML
        non_cf7                -> page is not CF7 (caller decides next step)
        recaptcha_detected     -> CF7 page contains reCAPTCHA (defer to AI)
    """

    success: bool
    status: str
    message: str = ""
    data_summary: str = ""


# -----------------------------------------------------------------------------
# CF7 detector — Python port of cf7-detector.ts L28-125
# -----------------------------------------------------------------------------
# Same regex strings as the TS version — DO NOT change without syncing both sides.
_FORM_ID_PATTERN_A = re.compile(
    r"""<input[^>]+name\s*=\s*["']_wpcf7["'][^>]+value\s*=\s*["'](\d+)["'][^>]*>""",
    re.IGNORECASE,
)
_FORM_ID_PATTERN_B = re.compile(
    r"""<input[^>]+value\s*=\s*["'](\d+)["'][^>]+name\s*=\s*["']_wpcf7["'][^>]*>""",
    re.IGNORECASE,
)
_INPUT_TAG_REGEX = re.compile(r"<(?:input|textarea|select)[^>]*>", re.IGNORECASE)
_TYPE_HIDDEN_RE = re.compile(r"""type\s*=\s*["']hidden["']""", re.IGNORECASE)
_TYPE_SUBMIT_RE = re.compile(r"""type\s*=\s*["']submit["']""", re.IGNORECASE)
_TYPE_BUTTON_RE = re.compile(r"""type\s*=\s*["']button["']""", re.IGNORECASE)
_NAME_ATTR_RE = re.compile(r"""name\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
_TYPE_ATTR_RE = re.compile(r"""type\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
_PLACEHOLDER_RE = re.compile(r"""placeholder\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
_ARIA_LABEL_RE = re.compile(r"""aria-label\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
_HIDDEN_INPUT_RE = re.compile(
    r"""<input[^>]+type\s*=\s*["']hidden["'][^>]*>""", re.IGNORECASE
)
_VALUE_ATTR_RE = re.compile(r"""value\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
_RECAPTCHA_RE = re.compile(r"grecaptcha|recaptcha|g-recaptcha|reCAPTCHA", re.IGNORECASE)

# reCAPTCHA v2(チェックボックス) と v3(invisible/スコア式) を静的HTMLから判別する。
#  - v3 は「セッション全体の挙動を採点」する監視型。自動ブラウザで入力した時点で
#    低スコア＝bot 判定が確定し、最後だけ人間が操作しても弾かれる（＝アシスト不可）。
#    → 自動ツールを一切触らせず、人が自分のブラウザで丸ごと送る「手動ハンドオフ」に回す。
#    目印: api.js?render= / .grecaptcha-badge / grecaptcha.execute() / CF7 の wpcf7_recaptcha。
#  - v2 は対話型チェックボックス。自動入力＋人が最後にチェックを解けば送れる（＝アシスト可）。
#    目印: .g-recaptcha[data-sitekey] / api2/anchor iframe。
_RECAPTCHA_V3_RE = re.compile(
    r"recaptcha/api\.js\?[^\"'>]*\brender=|grecaptcha-badge|grecaptcha\.execute|wpcf7[_-]recaptcha",
    re.IGNORECASE,
)
_RECAPTCHA_V2_RE = re.compile(
    r"g-recaptcha[\"'\s]|data-sitekey|recaptcha/api2|api2/anchor",
    re.IGNORECASE,
)


def classify_recaptcha(html: str) -> Optional[str]:
    """reCAPTCHA の種別を静的HTMLから判定して返す ('v2' / 'v3' / 'unknown' / None)。

    None = reCAPTCHA 無し。'unknown' = reCAPTCHA はあるが v2/v3 を断定できない。
    v3 信号（render=/badge/execute/wpcf7_recaptcha）を優先（CF7 既定は v3 invisible）。
    """
    if not html or not _RECAPTCHA_RE.search(html):
        return None
    if _RECAPTCHA_V3_RE.search(html):
        return "v3"
    if _RECAPTCHA_V2_RE.search(html):
        return "v2"
    return "unknown"


def detect_cf7(html: str, site_url: str) -> Cf7DetectionResult:
    """Detect whether `html` contains a CF7 form, and extract POST metadata.

    NOTE: Sync with src/lib/http-post/cf7-detector.ts detectCf7 (L28-125).
    """
    empty = Cf7DetectionResult(
        is_cf7=False, form_id=None, fields=[], hidden_fields={},
        has_recaptcha=False, action_url=None,
    )

    if "wpcf7-form" not in html and "wpcf7" not in html:
        return empty

    m = _FORM_ID_PATTERN_A.search(html) or _FORM_ID_PATTERN_B.search(html)
    if not m:
        return empty
    form_id = m.group(1)

    # Locate the CF7 form block boundaries
    form_start_idx = html.find("wpcf7-form")
    form_block_start = html.rfind("<form", 0, form_start_idx) if form_start_idx >= 0 else -1
    form_block_end = html.find("</form>", form_start_idx) if form_start_idx >= 0 else -1
    if form_block_start >= 0 and form_block_end >= 0:
        form_html = html[form_block_start : form_block_end + len("</form>")]
    else:
        form_html = html

    fields: list[Cf7FormField] = []
    for match in _INPUT_TAG_REGEX.finditer(form_html):
        tag = match.group(0)
        if _TYPE_HIDDEN_RE.search(tag):
            continue
        if _TYPE_SUBMIT_RE.search(tag):
            continue
        if _TYPE_BUTTON_RE.search(tag):
            continue

        name_match = _NAME_ATTR_RE.search(tag)
        if not name_match:
            continue
        name = name_match.group(1)
        # Skip CF7 internal fields
        if name.startswith("_wpcf7"):
            continue

        type_match = _TYPE_ATTR_RE.search(tag)
        if type_match:
            ftype = type_match.group(1)
        elif tag.lower().startswith("<textarea"):
            ftype = "textarea"
        elif tag.lower().startswith("<select"):
            ftype = "select"
        else:
            ftype = "text"

        placeholder_match = _PLACEHOLDER_RE.search(tag)
        aria_label_match = _ARIA_LABEL_RE.search(tag)
        label = (
            (placeholder_match.group(1) if placeholder_match else "")
            or (aria_label_match.group(1) if aria_label_match else "")
            or ""
        )

        fields.append(Cf7FormField(name=name, type=ftype, label=label))

    hidden_fields: dict[str, str] = {}
    for match in _HIDDEN_INPUT_RE.finditer(form_html):
        tag = match.group(0)
        nm = _NAME_ATTR_RE.search(tag)
        vm = _VALUE_ATTR_RE.search(tag)
        if nm:
            hidden_fields[nm.group(1)] = vm.group(1) if vm else ""

    has_recaptcha = bool(_RECAPTCHA_RE.search(form_html))

    # Build action URL = origin + /wp-json/contact-form-7/v1/contact-forms/<id>/feedback
    parsed = urlparse(site_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    action_url = f"{origin}/wp-json/contact-form-7/v1/contact-forms/{form_id}/feedback"

    return Cf7DetectionResult(
        is_cf7=True,
        form_id=form_id,
        fields=fields,
        hidden_fields=hidden_fields,
        has_recaptcha=has_recaptcha,
        action_url=action_url,
    )


# -----------------------------------------------------------------------------
# Bot protection detection (Sprint 5 Task 3 §3-8-2)
# -----------------------------------------------------------------------------
_TURNSTILE_RE = re.compile(
    r"cf-turnstile|challenges\.cloudflare\.com", re.IGNORECASE
)
_HCAPTCHA_RE = re.compile(r"h-captcha|hcaptcha\.com", re.IGNORECASE)


def detect_bot_protection(html: str) -> Optional[str]:
    """Return 'turnstile' / 'hcaptcha' / None.

    NOTE: Sync with detection markers used by Web engine.ts detectBotProtection.
    Sprint 5 covers only HTTP POST short-circuit; CapSolver integration is
    Phase 2-B.
    """
    if not html:
        return None
    if _TURNSTILE_RE.search(html):
        return "turnstile"
    if _HCAPTCHA_RE.search(html):
        return "hcaptcha"
    return None


# -----------------------------------------------------------------------------
# CF7 HTTP POST sender — Python port of cf7-sender.ts L29-130
# -----------------------------------------------------------------------------
async def send_cf7_form(
    action_url: str,
    cf7_fields: list[Cf7FormField],
    hidden_fields: dict[str, str],
    fill_data: FillData,
    form_id: str,
    *,
    client: Optional[httpx.AsyncClient] = None,
) -> Cf7SendResult:
    """POST sender form data to a CF7 REST endpoint.

    Args:
        action_url:    /wp-json/contact-form-7/v1/contact-forms/<id>/feedback
        cf7_fields:    visible fields from detect_cf7
        hidden_fields: hidden inputs from detect_cf7 (incl. _wpcf7 etc.)
        fill_data:     sender info
        form_id:       CF7 form id
        client:        optional shared httpx.AsyncClient. When omitted we
                       create-and-close one for this call.

    NOTE: Sync with src/lib/http-post/cf7-sender.ts sendCf7Form (L29-165).
    """
    # Build multipart payload as a list of (name, (None, value)) tuples for
    # httpx `files=` so duplicate keys are preserved (matches TS FormData
    # behaviour). httpx's `data=list[tuple]` is broken in 0.28 (it dispatches
    # through the sync transport — see GH#3076), so we use `files=`.
    multipart: list[tuple[str, tuple[None, str]]] = []

    # 1. Hidden fields first
    for key, value in hidden_fields.items():
        multipart.append((key, (None, value)))

    # 2. Ensure essential CF7 hidden fields exist
    existing_keys = {k for k, _ in multipart}
    if "_wpcf7" not in existing_keys:
        multipart.append(("_wpcf7", (None, form_id)))
    if "_wpcf7_unit_tag" not in existing_keys:
        multipart.append(("_wpcf7_unit_tag", (None, f"wpcf7-f{form_id}-o1")))

    mapped_fields: list[dict[str, str]] = []
    seen_visible: set[str] = set()

    # 3. Visible fields -> determineValue
    for cf7_field in cf7_fields:
        ff = FormField(
            name=cf7_field.name,
            type=cf7_field.type,
            label=cf7_field.label,
        )
        value = determine_value(ff, fill_data)
        if value:
            multipart.append((cf7_field.name, (None, value)))
            seen_visible.add(cf7_field.name)
            mapped_fields.append({
                "fieldName": cf7_field.name,
                "label": cf7_field.label or cf7_field.name,
                "value": value,
            })

    # 4. Ensure message/body field present
    textarea_fields = [f for f in cf7_fields if f.type == "textarea"]
    message = fill_data.get("message") or ""
    for ta in textarea_fields:
        if ta.name not in seen_visible and message:
            multipart.append((ta.name, (None, message)))
            mapped_fields.append({
                "fieldName": ta.name,
                "label": ta.label or ta.name,
                "value": (message[:50] + "...") if len(message) > 50 else message,
            })
            seen_visible.add(ta.name)

    summary_parts: list[str] = []
    for m in mapped_fields:
        v = m["value"]
        disp = (v[:30] + "...") if len(v) > 30 else v
        summary_parts.append(f"{m['label']}: {disp}")

    # 5. POST
    await _anti_spam_sleep()

    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(
            timeout=_HTTP_TIMEOUT_SEC, headers=_DEFAULT_HEADERS, follow_redirects=True
        )
    try:
        try:
            resp = await client.post(
                action_url,
                files=multipart,
                headers={"Accept": "application/json"},
            )
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPError) as e:
            msg = str(e) or e.__class__.__name__
            is_timeout = "timeout" in msg.lower() or isinstance(e, httpx.TimeoutException)
            return Cf7SendResult(
                success=False,
                status="error",
                message="HTTP POSTタイムアウト（10秒）" if is_timeout else msg,
                data_summary=f"[HTTP POST] エラー: {msg}",
            )

        if resp.status_code >= 400:
            return Cf7SendResult(
                success=False,
                status="error",
                message=f"HTTP {resp.status_code}: {resp.reason_phrase}",
                data_summary=(
                    f"[HTTP POST] 送信失敗 (HTTP {resp.status_code}) / "
                    + " / ".join(summary_parts)
                ),
            )

        try:
            result = resp.json()
        except ValueError as e:  # response not valid JSON
            return Cf7SendResult(
                success=False,
                status="error",
                message=f"non-JSON response: {e}",
                data_summary=f"[HTTP POST] エラー: response not JSON",
            )

        cf7_status = str(result.get("status") or "unknown")
        cf7_message = str(result.get("message") or "")

        if cf7_status == "mail_sent":
            return Cf7SendResult(
                success=True,
                status="completed",
                message=cf7_message,
                data_summary=f"[HTTP POST] 送信成功 / " + " / ".join(summary_parts),
            )

        return Cf7SendResult(
            success=False,
            status=cf7_status if cf7_status in {"validation_failed", "mail_failed"} else "error",
            message=f"{cf7_message} ({cf7_status})",
            data_summary=f"[HTTP POST] {cf7_status}: {cf7_message} / " + " / ".join(summary_parts),
        )
    finally:
        if own_client:
            await client.aclose()


# -----------------------------------------------------------------------------
# High-level helper: fetch -> early-skip -> detect -> POST
# -----------------------------------------------------------------------------
async def try_http_post(
    url: str,
    fill_data: FillData,
    *,
    client: Optional[httpx.AsyncClient] = None,
) -> Cf7SendResult:
    """End-to-end HTTP POST attempt with early-skip judgments.

    Sequence (Stage 0 + Stage 1 of the system-workflow):
        fetch URL -> prohibition check -> bot-protection check -> CF7 detect
        -> reCAPTCHA gate -> send_cf7_form

    Returns a Cf7SendResult whose `status` field tells the caller what to do
    next (see Cf7SendResult docstring).
    """
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(
            timeout=_HTTP_TIMEOUT_SEC, headers=_DEFAULT_HEADERS, follow_redirects=True
        )
    try:
        # 1. Fetch the page
        try:
            page_resp = await client.get(url)
        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPError) as e:
            msg = str(e) or e.__class__.__name__
            return Cf7SendResult(
                success=False,
                status="error",
                message=msg,
                data_summary=f"[HTTP POST] fetch エラー: {msg}",
            )

        if page_resp.status_code >= 400:
            return Cf7SendResult(
                success=False,
                status="error",
                message=f"HTTP {page_resp.status_code}: {page_resp.reason_phrase}",
                data_summary=f"[HTTP POST] fetch エラー: HTTP {page_resp.status_code}",
            )

        html = page_resp.text

        # 2. Prohibition early-skip
        if check_prohibition(html):
            return Cf7SendResult(
                success=False,
                status="prohibition_detected",
                message="prohibition keyword detected in HTML",
                data_summary="[HTTP POST] 営業禁止検知 → スキップ",
            )

        # 3. Bot protection early-skip
        bot = detect_bot_protection(html)
        if bot:
            return Cf7SendResult(
                success=False,
                status="bot_protection",
                message=bot,
                data_summary=f"[HTTP POST] Bot 保護検知 ({bot}) → スキップ",
            )

        # 4. CF7 detection
        result = detect_cf7(html, str(page_resp.url))
        if not result.is_cf7:
            return Cf7SendResult(
                success=False,
                status="non_cf7",
                message="not a Contact Form 7 site",
                data_summary="[HTTP POST] 非 CF7 → スキップ",
            )

        # 5. reCAPTCHA gate — v2/v3 種別を message に載せて上流(事前ゲート)へ渡す。
        #    error_reason は "recaptcha_detected:<type>" になり、HybridProvider が
        #    種別＋スイッチで「v2→アシスト / v3→手動ハンドオフ / (OFF時)1回試す」を決める。
        if result.has_recaptcha:
            rc_type = classify_recaptcha(html) or "unknown"
            return Cf7SendResult(
                success=False,
                status="recaptcha_detected",
                message=rc_type,
                data_summary=f"[HTTP POST] reCAPTCHA {rc_type} 検知 → 事前ゲート判定へ",
            )

        # 6. Send
        if result.action_url is None or result.form_id is None:
            return Cf7SendResult(
                success=False,
                status="error",
                message="CF7 detected but action_url or form_id missing",
                data_summary="[HTTP POST] CF7 metadata 不完全",
            )

        return await send_cf7_form(
            action_url=result.action_url,
            cf7_fields=result.fields,
            hidden_fields=result.hidden_fields,
            fill_data=fill_data,
            form_id=result.form_id,
            client=client,
        )
    finally:
        if own_client:
            await client.aclose()
