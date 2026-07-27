"""Sprint 6 Task 2 — Playwright Python port of form-detector.ts.

Implements:
    analyze_form(page, dictionaries) -> list[FormField]
    detect_bot_protection(page) -> dict
    find_form_page(page, keywords) -> Optional[str]

The DOM-side JS is passed verbatim to `page.evaluate()` so the heuristics
stay bit-equivalent to the Web 版. The Python wrapper handles:
    - iframe traversal (page.frames())
    - dictionary injection (form-scoring.json contactKeywords / excludeKeywords)
    - Fail Safe try/except (detached frames, cross-origin restrictions)

NOTE: Sync with src/lib/browser/form-detector.ts:21-433 (detectBotProtection
L21-113, analyzeForm L257-433, findFormPage L122-255).
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from typing import Any, Optional

# #38: 個別 frame.evaluate() の上限(秒)。応答しない埋め込みiframe(地図等)の
# ゴーストフレームで永久待機するのを防ぐ。応答する frame は ms 級で通る。
_FRAME_EVAL_TIMEOUT_S = 3.0

try:
    from skill.core._pattern_loader import load_contact_links, load_form_scoring
except ImportError:
    from _pattern_loader import load_contact_links, load_form_scoring  # type: ignore


# -----------------------------------------------------------------------------
# Types
# -----------------------------------------------------------------------------
@dataclass
class FormField:
    """Mirrors TS form-detector.ts FormField (L4-11)."""

    name: str
    type: str
    label: str = ""
    selector: str = ""
    width: float = 0.0
    height: float = 0.0
    maxlength: int = 0  # <input maxlength>; 0 = 未指定。電話分割欄の検出に使う。
    placeholder: str = ""  # <input placeholder>。可視ラベル共通で姓/名分割を placeholder だけが示すフォーム用。


# -----------------------------------------------------------------------------
# Bot protection detection — JS port of detectBotProtection (L21-113)
# -----------------------------------------------------------------------------
# NOTE: Sync with src/lib/browser/form-detector.ts:21-113.
# The JS here is structurally identical; minor whitespace changes only.
_DETECT_BOT_PROTECTION_JS = r"""
() => {
    // Strong v3 signals
    const hasRenderParam = Array.from(document.scripts)
        .some(s => s.src && s.src.includes('recaptcha')
                && s.src.includes('render=')
                && !s.src.includes('render=explicit'));
    const hasRecaptchaBadge = document.querySelector('.grecaptcha-badge') !== null;
    const hasCF7Recaptcha = typeof window.wpcf7_recaptcha !== 'undefined'
        && !!(window.wpcf7_recaptcha && window.wpcf7_recaptcha.sitekey);
    const hasGrecaptchaExecute = Array.from(document.scripts)
        .some(s => !s.src && s.textContent && s.textContent.includes('grecaptcha.execute'));

    // Strong v2 signals
    const hasV2AnchorIframe = Array.from(document.querySelectorAll('iframe'))
        .some(f => f.src && f.src.includes('google.com/recaptcha/api2/anchor'));
    const hasRecaptchaWidget = document.querySelector('.g-recaptcha[data-sitekey]') !== null;

    // Ambiguous: api.js loaded
    const hasRecaptchaScript = Array.from(document.scripts)
        .some(s => s.src && (s.src.includes('google.com/recaptcha/api.js')
                          || s.src.includes('recaptcha/enterprise.js')));

    if (hasRenderParam || hasRecaptchaBadge || hasCF7Recaptcha || hasGrecaptchaExecute) {
        return {
            detected: false, blocking: false, type: 'reCAPTCHA v3',
            reason: 'reCAPTCHA v3（非表示型）が検知されましたが、送信を試みます。'
        };
    }
    if (hasV2AnchorIframe || hasRecaptchaWidget) {
        return {
            detected: false, blocking: false, type: 'reCAPTCHA v2',
            reason: 'reCAPTCHA v2（チェックボックス型）が検知されましたが、チェックボックスへの押下を試みます。'
        };
    }
    if (hasRecaptchaScript) {
        return {
            detected: false, blocking: false, type: 'reCAPTCHA v2',
            reason: 'reCAPTCHA（種類不明）が検知されました。v2として試行し、失敗時はv3にフォールバックします。'
        };
    }

    // Turnstile (BLOCKING)
    const hasTurnstileScript = Array.from(document.scripts)
        .some(s => s.src && s.src.includes('challenges.cloudflare.com/turnstile'));
    const hasTurnstileWidget = document.querySelector('.cf-turnstile') !== null;
    if (hasTurnstileScript || hasTurnstileWidget) {
        return {
            detected: true, blocking: true, type: 'Turnstile',
            reason: 'Cloudflare Turnstile が導入されています。'
        };
    }

    // hCaptcha (BLOCKING)
    const hasHcaptchaScript = Array.from(document.scripts)
        .some(s => s.src && s.src.includes('hcaptcha.com'));
    const hasHcaptchaWidget = document.querySelector('.h-captcha') !== null;
    if (hasHcaptchaScript || hasHcaptchaWidget) {
        return {
            detected: true, blocking: true, type: 'hCaptcha',
            reason: 'hCaptcha が導入されています。'
        };
    }

    return { detected: false };
}
"""


async def detect_bot_protection(page: Any) -> dict:
    """Detect strong bot protection systems on the current page.

    Returns a dict with the same shape as the TS version:
        {"detected": bool, "blocking"?: bool, "type"?: str, "reason"?: str}
    """
    try:
        result = await page.evaluate(_DETECT_BOT_PROTECTION_JS)
        if not isinstance(result, dict):
            return {"detected": False}
        return result
    except BaseException as e:  # noqa: BLE001 — Fail Safe per TS L109-112
        sys.stderr.write(
            f"[_form_detector] Bot protection detection failed (ignoring): "
            f"{type(e).__name__}: {e}\n"
        )
        return {"detected": False}


# -----------------------------------------------------------------------------
# Form analysis — JS port of analyzeForm (L257-433)
# -----------------------------------------------------------------------------
# NOTE: Sync with src/lib/browser/form-detector.ts:257-433.
# Form scoring weights:
#   wpcf7-form         +100  (CMS-specific structural signal, retained per Sprint 1 §3.1.6 #2)
#   contactKeywords    +50
#   textarea           +30
#   hasEmailInput      +20
#   visibleInputs * 5  varying
#   hasSearchInput     -100
#   excludeKeywords    -100
#   header/footer/nav  -50
#   <=2 visibleInputs  -20
_ANALYZE_FORM_JS = r"""
(dict) => {
    const forms = Array.from(document.querySelectorAll('form'));

    let bestForm = null;
    let bestScore = -Infinity;

    if (forms.length > 0) {
        for (const form of forms) {
            let score = 0;
            const html = form.innerHTML.toLowerCase();
            const formText = (form.textContent || '').toLowerCase();

            if (form.classList.contains('wpcf7-form')) score += 100;

            if (dict.contactKeywords.some(kw => html.includes(kw) || formText.includes(kw))) {
                score += 50;
            }

            if (form.querySelector('textarea')) score += 30;

            const hasEmailInput = form.querySelector('input[type="email"]') ||
                Array.from(form.querySelectorAll('input')).some(inp =>
                    (inp.name && inp.name.toLowerCase().includes('email')) ||
                    (inp.name && inp.name.toLowerCase().includes('メール'))
                );
            if (hasEmailInput) score += 20;

            const inputs = Array.from(form.querySelectorAll('input, textarea, select'));
            const visibleInputs = inputs.filter(inp => {
                if (inp.type === 'hidden') return false;
                if (inp.type === 'search') return false;
                const style = window.getComputedStyle(inp);
                return style.display !== 'none' && style.visibility !== 'hidden';
            });
            score += visibleInputs.length * 5;

            const hasSearchInput = form.querySelector('input[type="search"]') ||
                form.querySelector('input[name="s"]');
            if (hasSearchInput) score -= 100;

            if (dict.excludeKeywords.some(kw => html.includes(kw) || formText.includes(kw))) {
                score -= 100;
            }

            let parent = form.parentElement;
            while (parent) {
                const tag = parent.tagName.toLowerCase();
                if (['header', 'footer', 'nav'].includes(tag)) {
                    score -= 50;
                    break;
                }
                parent = parent.parentElement;
            }

            if (visibleInputs.length <= 2) score -= 20;

            if (score > bestScore) {
                bestScore = score;
                bestForm = form;
            }
        }
    }

    let container;
    let finalScore;

    if (bestForm && bestScore > 0) {
        container = bestForm;
        finalScore = bestScore;
    } else {
        container = document.body;
        const visibleInputs = Array.from(container.querySelectorAll('input, textarea, select'))
            .filter(inp => {
                if (inp.type === 'hidden' || inp.type === 'search') return false;
                const style = window.getComputedStyle(inp);
                return style.display !== 'none' && style.visibility !== 'hidden';
            });
        finalScore = visibleInputs.length > 0 ? visibleInputs.length * 5 : -Infinity;
    }

    const inputs = Array.from(container.querySelectorAll('input, textarea, select'));

    const mappedInputs = inputs
        .filter(el => {
            if (el.type === 'hidden' || el.type === 'search') return false;
            return true;
        })
        .map(el => {
            const input = el;
            const rect = input.getBoundingClientRect();

            let labelText = '';

            // 1. Explicit label[for]
            if (input.id) {
                const label = document.querySelector('label[for="' + input.id + '"]');
                if (label && label.innerText && label.innerText.trim()) {
                    labelText = label.innerText.trim();
                }
            }
            // 2. aria-label
            if (!labelText) {
                const aria = input.getAttribute('aria-label');
                if (aria) labelText = aria;
            }
            // 3. Parent text
            if (!labelText && input.parentElement) {
                const parentText = input.parentElement.innerText || '';
                if (parentText.length < 50) labelText = parentText;
            }
            // 4. Previous sibling
            if (!labelText) {
                const prev = input.previousElementSibling;
                if (prev && ['TH','LABEL','SPAN','DIV','P'].includes(prev.tagName)) {
                    labelText = prev.innerText || '';
                }
            }
            // 5. Parent's previous sibling (uncle)
            if (!labelText && input.parentElement) {
                const parent = input.parentElement;
                const uncle = parent.previousElementSibling;
                if (uncle && ['TH','DT','DIV','LABEL'].includes(uncle.tagName)) {
                    labelText = uncle.innerText || '';
                }
            }
            // placeholder は常に別途保持する（可視ラベルが「ご担当者名」等で共通でも
            // 姓/名の分割 signal が placeholder にしかないフォームがあるため）。
            const phAttr = (input.getAttribute ? input.getAttribute('placeholder') : '') || '';
            // 6. placeholder (last resort for label)
            if (!labelText && phAttr) {
                labelText = phAttr;
            }

            const maxAttr = input.getAttribute ? input.getAttribute('maxlength') : null;
            const maxLen = maxAttr != null && maxAttr !== '' ? parseInt(maxAttr, 10) : 0;

            return {
                name: input.name || input.id || '',
                type: input.type || input.tagName.toLowerCase(),
                label: labelText,
                selector: input.id ? '#' + input.id : (input.name ? '[name="' + input.name + '"]' : input.tagName),
                width: rect.width || 0,
                height: rect.height || 0,
                maxlength: (Number.isFinite(maxLen) && maxLen > 0) ? maxLen : 0,
                placeholder: phAttr
            };
        });

    return { score: finalScore, inputs: mappedInputs };
}
"""


def _build_analyze_dict() -> dict:
    """Pre-compute the lowercase keyword lists from form-scoring.json."""
    fs = load_form_scoring()
    contact = fs.get("contactKeywords", {}).get("aliases", []) or []
    exclude = fs.get("excludeKeywords", {}).get("aliases", []) or []
    return {
        "contactKeywords": [str(k).lower() for k in contact],
        "excludeKeywords": [str(k).lower() for k in exclude],
    }


async def analyze_form(
    page: Any,
    *,
    dictionaries: Optional[dict] = None,
) -> tuple[list[FormField], Any]:
    """Analyze all frames of `page` and return the best-scoring form's fields
    AND the frame that contains it.

    Args:
        page: Playwright Page.
        dictionaries: optional precomputed analyzeDict (form-scoring lowercased).
            When None, we load form-scoring.json here.

    Returns:
        (fields, frame): fields は空なら未検出。frame は当該フォームのある Frame。
        iframe埋め込み(formzu/Googleフォーム等)では main_frame ではなく当該 iframe を
        返し、呼び出し側が入力/送信をそのフレーム上で行えるようにする。未検出でも
        main_frame を返す。
    """
    if dictionaries is None:
        dictionaries = _build_analyze_dict()

    best_overall_score: float = float("-inf")
    best_inputs: list[FormField] = []
    best_frame: Any = getattr(page, "main_frame", page)

    for frame in page.frames:
        try:
            # #38: ゴーストフレーム(実行コンテキスト未確定の埋め込みiframe)では
            # frame.evaluate が timeout を持たず永久ハングする。wait_for で打ち切り、
            # 応答しない frame はスキップ(TimeoutError は例外なので下の except で拾える)。
            result = await asyncio.wait_for(
                frame.evaluate(_ANALYZE_FORM_JS, dictionaries),
                timeout=_FRAME_EVAL_TIMEOUT_S,
            )
        except BaseException:  # noqa: BLE001 — TimeoutError/detached/cross-origin 等
            continue

        if not isinstance(result, dict):
            continue
        score_raw = result.get("score")
        try:
            score = float(score_raw)
        except (TypeError, ValueError):
            continue
        if score <= best_overall_score:
            continue
        raw_inputs = result.get("inputs") or []
        if not isinstance(raw_inputs, list):
            continue
        fields: list[FormField] = []
        for entry in raw_inputs:
            if not isinstance(entry, dict):
                continue
            try:
                maxlength = int(entry.get("maxlength", 0) or 0)
            except (TypeError, ValueError):
                maxlength = 0
            fields.append(
                FormField(
                    name=str(entry.get("name", "") or ""),
                    type=str(entry.get("type", "") or ""),
                    label=str(entry.get("label", "") or ""),
                    selector=str(entry.get("selector", "") or ""),
                    width=float(entry.get("width", 0) or 0),
                    height=float(entry.get("height", 0) or 0),
                    maxlength=maxlength,
                    placeholder=str(entry.get("placeholder", "") or ""),
                )
            )
        best_overall_score = score
        best_inputs = fields
        best_frame = frame

    return best_inputs, best_frame


# -----------------------------------------------------------------------------
# Find form page — minimal port of findFormPage (L122-255)
# -----------------------------------------------------------------------------
# Sprint 6 KISS: only the contact-link search path is ported. Strategy 2
# (form scoring) and Strategy 3 (menu hamburger expansion) are deferred to
# Phase 2-C per spec §6 Task 2.
_FIND_LINK_JS = r"""
(keywords) => {
    const lowered = keywords.map(k => String(k).toLowerCase());
    const anchors = Array.from(document.querySelectorAll('a'));
    for (const a of anchors) {
        const text = ((a.innerText || '') + ' ' + (a.getAttribute('aria-label') || ''))
            .toLowerCase().trim();
        const imgAlt = Array.from(a.querySelectorAll('img'))
            .map(img => (img.getAttribute('alt') || '').toLowerCase()).join(' ');
        const combined = text + ' ' + imgAlt;
        if (combined.trim() && lowered.some(kw => combined.includes(kw))) {
            return a.href || null;
        }
    }
    return null;
}
"""


async def find_form_page(
    page: Any,
    *,
    keywords: Optional[list[str]] = None,
) -> Optional[str]:
    """Try to find a contact-form link on the current page.

    Returns the absolute href, or None if no candidate link was found.
    """
    if keywords is None:
        cl = load_contact_links()
        keywords = list(cl.get("aliases", []) or [])
    if not keywords:
        return None
    try:
        href = await page.evaluate(_FIND_LINK_JS, keywords)
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_form_detector] find_form_page failed (ignoring): "
            f"{type(e).__name__}: {e}\n"
        )
        return None
    if isinstance(href, str) and href.strip():
        return href
    return None
