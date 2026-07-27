"""Sprint 6 Task 6 — Optional CapSolver integration (Python port of captcha.ts).

When `CAPSOLVER_API_KEY` is set, this module attempts to solve reCAPTCHA
v2/v3 challenges on the active Playwright page. When the env var is absent
the public entry point returns `{"status": "skipped"}` so the caller can
treat it as a no-op.

NOTE: Sync with src/lib/browser/captcha.ts.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Optional

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore

# -----------------------------------------------------------------------------
# CapSolver constants — bit-equivalent to captcha.ts L16-19
# -----------------------------------------------------------------------------
_CAPSOLVER_CREATE_TASK_URL = "https://api.capsolver.com/createTask"
_CAPSOLVER_GET_RESULT_URL = "https://api.capsolver.com/getTaskResult"
_CAPSOLVER_POLL_INTERVAL_MS = 3_000
_CAPSOLVER_MAX_WAIT_MS = 60_000


# -----------------------------------------------------------------------------
# Sitekey detection — JS port of detectSitekey (L24-87)
# -----------------------------------------------------------------------------
_DETECT_SITEKEY_JS = r"""
() => {
    let sitekey = null;
    let isEnterprise = false;
    const scripts = Array.from(document.querySelectorAll('script'));
    isEnterprise = scripts.some(s =>
        s.src && s.src.includes('recaptcha') && s.src.includes('enterprise.js')
    );

    // 1. ?render= parameter
    for (const s of scripts) {
        if (s.src && s.src.includes('?render=')) {
            const m = s.src.match(/[?&]render=([^&]+)/);
            if (m && m[1] !== 'explicit') {
                sitekey = m[1];
                break;
            }
        }
    }
    // 2. data-sitekey
    if (!sitekey) {
        const el = document.querySelector('[data-sitekey]');
        if (el) sitekey = el.getAttribute('data-sitekey');
    }
    // 3. iframe k=
    if (!sitekey) {
        const iframe = document.querySelector('iframe[src*="recaptcha"]');
        if (iframe && iframe.src) {
            const m = iframe.src.match(/[?&]k=([^&]+)/);
            if (m) sitekey = m[1];
        }
    }
    // 4. hidden input
    if (!sitekey) {
        const hidden = document.querySelector('input[name="g-recaptcha-sitekey"]');
        if (hidden) sitekey = hidden.value;
    }
    // 5. CF7 wpcf7_recaptcha
    if (!sitekey) {
        if (window.wpcf7_recaptcha && window.wpcf7_recaptcha.sitekey) {
            sitekey = window.wpcf7_recaptcha.sitekey;
        }
    }
    // 6. Regex fallback
    if (!sitekey) {
        const html = document.documentElement.outerHTML;
        const m = html.match(/['"](6[L|M][a-zA-Z0-9_-]{38})['"]/);
        if (m) sitekey = m[1];
    }
    return sitekey ? { sitekey: sitekey, isEnterprise: isEnterprise } : null;
}
"""


_INJECT_TOKEN_JS = r"""
(t) => {
    // 1. Standard hidden fields
    const fields = document.querySelectorAll(
        '[name="g-recaptcha-response"], [name="recaptcha-token"], ' +
        '[id="g-recaptcha-response"], [name="_wpcf7_recaptcha_response"]'
    );
    fields.forEach(el => {
        el.value = t;
        el.dispatchEvent(new Event('change', { bubbles: true }));
    });
    // 2. Monkey-patch grecaptcha.execute so CF7-style sites think the token is valid
    try {
        if (window.grecaptcha) {
            window.grecaptcha.execute = function() { return Promise.resolve(t); };
        }
    } catch (e) {}
    return fields.length;
}
"""


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------
async def prepare_captcha_for_submission(
    page: Any,
    bot_protection: Optional[dict] = None,
) -> dict:
    """Try to obtain a CapSolver token and inject it into the page.

    Returns:
        {"status": "passed" | "puzzle" | "not_found" | "skipped" | "error",
         "message": str}

    NOTE: Sync with src/lib/browser/captcha.ts prepareCaptchaForSubmission.
    """
    # ★ポリシー方針によるハード無効化（2026-07-03）:
    #   CAPTCHA の自動解答/回避は行わない。reCAPTCHA/hCaptcha 等は検出時にスキップし、
    #   最後の CAPTCHA 操作は assist_mode で「人間」が解く（human-in-the-loop）。
    #   CAPSOLVER_API_KEY を設定しても自動突破は動かないよう、ここで常に skipped を返す。
    #   （自動解答を復活させる判断は、方針変更として別途明示的に行うこと。）
    return {"status": "skipped", "message": "captcha auto-solve disabled by policy (human assist only)"}

    api_key = os.environ.get("CAPSOLVER_API_KEY", "").strip()  # noqa: F841 (unreachable; kept for context)
    if not api_key:
        return {"status": "skipped", "message": "CAPSOLVER_API_KEY not set"}
    if httpx is None:
        return {"status": "skipped", "message": "httpx not installed"}

    # Detect sitekey on page
    try:
        site = await page.evaluate(_DETECT_SITEKEY_JS)
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        return {"status": "error", "message": f"detectSitekey: {type(e).__name__}: {e}"}

    if not isinstance(site, dict) or not site.get("sitekey"):
        return {"status": "not_found", "message": "no recaptcha sitekey on page"}

    sitekey = str(site["sitekey"])
    is_enterprise = bool(site.get("isEnterprise"))
    page_url = page.url

    # Choose task type. v3 detection from bot_protection input (if provided).
    captcha_type = "v2"
    if bot_protection and bot_protection.get("type", "").startswith("reCAPTCHA v3"):
        captcha_type = "v3"

    if captcha_type == "v3":
        task = {
            "type": "ReCaptchaV3EnterpriseTaskProxyLess" if is_enterprise
            else "ReCaptchaV3TaskProxyLess",
            "websiteURL": page_url,
            "websiteKey": sitekey,
            "pageAction": "submit",
        }
    else:
        task = {
            "type": "ReCaptchaV2EnterpriseTaskProxyLess" if is_enterprise
            else "ReCaptchaV2TaskProxyLess",
            "websiteURL": page_url,
            "websiteKey": sitekey,
        }

    create_payload = {"clientKey": api_key, "task": task}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(_CAPSOLVER_CREATE_TASK_URL, json=create_payload)
            r.raise_for_status()
            create_resp = r.json()
            if create_resp.get("errorId"):
                return {
                    "status": "error",
                    "message": f"createTask: {create_resp.get('errorDescription', '')}",
                }
            task_id = create_resp.get("taskId")
            if not task_id:
                return {"status": "error", "message": "createTask: no taskId"}

            token: Optional[str] = None
            elapsed = 0
            while elapsed < _CAPSOLVER_MAX_WAIT_MS:
                await asyncio.sleep(_CAPSOLVER_POLL_INTERVAL_MS / 1000.0)
                elapsed += _CAPSOLVER_POLL_INTERVAL_MS
                rr = await client.post(
                    _CAPSOLVER_GET_RESULT_URL,
                    json={"clientKey": api_key, "taskId": task_id},
                )
                rr.raise_for_status()
                res = rr.json()
                if res.get("errorId"):
                    return {
                        "status": "error",
                        "message": f"getTaskResult: {res.get('errorDescription', '')}",
                    }
                if res.get("status") == "ready":
                    solution = res.get("solution") or {}
                    token = (
                        solution.get("gRecaptchaResponse")
                        or solution.get("token")
                    )
                    break
            if not token:
                return {"status": "error", "message": "CapSolver polling timeout"}
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        return {"status": "error", "message": f"{type(e).__name__}: {e}"}

    # Inject token into the page DOM
    try:
        await page.evaluate(_INJECT_TOKEN_JS, token)
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        return {
            "status": "error",
            "message": f"injectToken: {type(e).__name__}: {e}",
        }

    return {"status": "passed", "message": f"reCAPTCHA {captcha_type} token injected"}
