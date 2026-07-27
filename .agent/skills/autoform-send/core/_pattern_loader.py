"""Sprint 5 Task 1 — Static dictionary loader for the Python skill.

Reads the read-only dictionary JSON files at
`src/lib/browser/dictionaries/*.json` and exposes the lookups that the CF7
HTTP POST path / Pareto noAI filter / confirmation success detector need.

Design principles:
- read-only, no copy: dictionaries live in `src/lib/browser/dictionaries/`
  (mono-repo shared asset). When the skill is distributed standalone the
  `AUTOFORM_DICTIONARIES_PATH` environment variable overrides the path.
- bit-equivalent to the TS implementation at
  `src/lib/browser/dictionaries/index.ts`. Specifically, `normalize_l1`
  reproduces TS's L67-73 (`NFKC -> lowercase -> whitespace removal`).
- All loaders are memoized on first call to keep JSON parsing to 1 hit per
  dictionary per process.

NOTE: Sync with src/lib/browser/dictionaries/index.ts (normalizeL1,
matchLabel, loadProhibition, loadErrorTriggers, loadConfirmationSignals).
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

# -----------------------------------------------------------------------------
# Path resolution (Sprint 6 Task 0)
# -----------------------------------------------------------------------------
# This file moved from `python_worker/_pattern_loader.py` to
# `skill/core/_pattern_loader.py`. The default dictionary path is now the
# bundled Skill directory `skill/dictionaries/` (2 levels up from this file).
# Fallback to the mono-repo master `src/lib/browser/dictionaries/` so devs
# editing master directly without running the sync script still see changes.
#
# Search order:
#   1. AUTOFORM_DICTIONARIES_PATH env var (highest priority — explicit override)
#   2. ${CLAUDE_SKILL_DIR}/dictionaries/   — Skill standalone distribution path
#   3. <skill>/dictionaries/                — bundled in mono-repo context
#   4. <repo>/src/lib/browser/dictionaries/ — master fallback (dev convenience)
_THIS_FILE = Path(__file__).resolve()
_SKILL_ROOT = _THIS_FILE.parents[1]   # skill/core/ -> skill/
_REPO_ROOT = _THIS_FILE.parents[2]    # skill/core/ -> skill/ -> repo/


def _dict_dir() -> Path:
    """Resolve dictionary directory; checks 4 locations in priority order."""
    override = os.environ.get("AUTOFORM_DICTIONARIES_PATH", "").strip()
    if override:
        return Path(override).resolve()

    skill_dir_env = os.environ.get("CLAUDE_SKILL_DIR", "").strip()
    if skill_dir_env:
        candidate = Path(skill_dir_env).resolve() / "dictionaries"
        if candidate.exists():
            return candidate

    bundled = _SKILL_ROOT / "dictionaries"
    if bundled.exists():
        return bundled

    return _REPO_ROOT / "src" / "lib" / "browser" / "dictionaries"


# -----------------------------------------------------------------------------
# L1 normalization — bit-equivalent to TS dictionaries/index.ts:67-73
# -----------------------------------------------------------------------------
# TS: s.normalize('NFKC').toLowerCase().replace(/[\s\r\n\t　]+/g, '')
# Python whitespace class `\s` matches ASCII whitespace + (with UNICODE flag)
# also includes the full-width space U+3000.
_WHITESPACE_PATTERN = re.compile(r"[\s\r\n\t　]+")


def normalize_l1(s: str) -> str:
    """L1 normalize: NFKC + lowercase + whitespace removal.

    Bit-equivalent to TS dictionaries/index.ts normalizeL1 (L67-73).
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    s = _WHITESPACE_PATTERN.sub("", s)
    return s


# -----------------------------------------------------------------------------
# Internal JSON loader (memoized)
# -----------------------------------------------------------------------------
@lru_cache(maxsize=None)
def _read_json(filename: str) -> dict:
    """Read a JSON file from the dictionary directory, memoized.

    Raises:
        FileNotFoundError: when the file does not exist (Fail Fast for required
            dictionaries). Callers needing optional dictionaries (e.g.
            confirmation-signals) should catch this.
    """
    path = _dict_dir() / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Dictionary file not found: {path}. "
            f"Set AUTOFORM_DICTIONARIES_PATH to point to the dictionaries dir."
        )
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _clear_caches_for_test() -> None:
    """Clear all memoized caches (test-only helper)."""
    _read_json.cache_clear()
    load_label_dictionary.cache_clear()
    load_submit_buttons.cache_clear()
    load_prohibition.cache_clear()
    load_anti_sales_proximity.cache_clear()
    load_error_triggers.cache_clear()
    load_confirmation_signals.cache_clear()
    # Sprint 6: form-scoring / dynamic-detection / contact-links
    load_form_scoring.cache_clear()
    load_dynamic_detection.cache_clear()
    load_contact_links.cache_clear()


# -----------------------------------------------------------------------------
# Label Dictionary
# -----------------------------------------------------------------------------
SemanticType = str  # opaque alias for clarity; TS has a literal union


@lru_cache(maxsize=1)
def load_label_dictionary() -> list[dict[str, Any]]:
    """Load the label dictionary and pre-compute aliasesNormalized.

    Returns:
        List of entries, each:
            {
                "semantic": SemanticType,
                "aliases": list[str],
                "aliasesNormalized": list[str],
                "match"?: {"mode": "exact"|"contains", "excludeIfContains"?: list[str]},
                ...
            }

    NOTE: Sync with TS dictionaries/index.ts (LABEL_DICTIONARY at L83-86).
    """
    data = _read_json("labels.json")
    entries: list[dict[str, Any]] = []
    for entry in data.get("entries", []):
        aliases = entry.get("aliases") or []
        normalized = [normalize_l1(a) for a in aliases]
        entries.append({
            **entry,
            "aliasesNormalized": normalized,
        })
    return entries


def match_label(raw_label: str) -> Optional[SemanticType]:
    """Map a raw label (label/name/placeholder concatenation) to a semantic.

    Bit-equivalent to TS dictionaries/index.ts matchLabel (L107-130):
      - L1 normalize the input
      - For each entry, iterate aliasesNormalized
      - exact mode: full equality
      - contains mode (default): substring check + excludeIfContains gating
      - return the first hit's semantic

    Args:
        raw_label: concatenation of field label / name / placeholder.

    Returns:
        SemanticType string, or None if no entry matches.
    """
    normalized = normalize_l1(raw_label)
    if not normalized:
        return None

    for entry in load_label_dictionary():
        match_cfg = entry.get("match") or {}
        mode = match_cfg.get("mode") or "contains"
        excludes = match_cfg.get("excludeIfContains") or []
        excludes_normalized = [normalize_l1(e) for e in excludes]

        for alias_n in entry["aliasesNormalized"]:
            if not alias_n:
                continue
            if mode == "exact":
                if normalized == alias_n:
                    return entry["semantic"]
            else:
                if alias_n in normalized:
                    # Skip if an exclude word is present
                    if any(ex and ex in normalized for ex in excludes_normalized):
                        continue
                    return entry["semantic"]
    return None


# -----------------------------------------------------------------------------
# Submit Buttons Dictionary
# -----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_submit_buttons() -> dict[str, dict[str, list[str]]]:
    """Load submit-buttons.json (positive / negative / fallback).

    Returns:
        {
            "positive": {"aliases": [...], "aliasesNormalized": [...]},
            "negative": {"aliases": [...], "aliasesNormalized": [...]},
            "fallback": {"aliases": [...], "aliasesNormalized": [...]},
        }

    NOTE: Sync with TS dictionaries/index.ts SUBMIT_BUTTONS (L168-181).
    Currently unused by CF7 HTTP POST path; kept for future Phase 2-B use.
    """
    data = _read_json("submit-buttons.json")
    out: dict[str, dict[str, list[str]]] = {}
    for key in ("positive", "negative", "fallback"):
        section = data.get(key) or {}
        aliases = section.get("aliases") or []
        out[key] = {
            "aliases": list(aliases),
            "aliasesNormalized": [normalize_l1(a) for a in aliases],
        }
    return out


# -----------------------------------------------------------------------------
# Prohibition Dictionary
# -----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_prohibition() -> dict[str, dict[str, list[str]]]:
    """Load prohibition.json (prohibition + antiSales sections).

    Returns:
        {
            "prohibition": {"aliases": [...], "aliasesNormalized": [...]},
            "antiSales":   {"aliases": [...], "aliasesNormalized": [...]},
        }

    NOTE: Sync with TS dictionaries/index.ts PROHIBITION (L149-158).
    """
    data = _read_json("prohibition.json")
    out: dict[str, dict[str, list[str]]] = {}
    for key in ("prohibition", "antiSales"):
        section = data.get(key) or {}
        aliases = section.get("aliases") or []
        out[key] = {
            "aliases": list(aliases),
            "aliasesNormalized": [normalize_l1(a) for a in aliases],
        }
    return out


@lru_cache(maxsize=1)
def load_anti_sales_proximity() -> dict[str, Any]:
    """Load the antiSalesProximity section from prohibition.json (normalized).

    Returns:
        {
            "window": int,
            "salesTerms": [normalized...],
            "refusalTerms": [normalized...],
            "negationGuards": [normalized...],
        }
    空セクション (旧 seed) の場合は window=0 / 空リストを返し、判定を no-op にする。
    """
    data = _read_json("prohibition.json")
    section = data.get("antiSalesProximity") or {}
    try:
        window = int(section.get("window") or 0)
    except (TypeError, ValueError):
        window = 0
    return {
        "window": max(0, window),
        "salesTerms": [n for n in (normalize_l1(t) for t in section.get("salesTerms") or []) if n],
        "refusalTerms": [n for n in (normalize_l1(t) for t in section.get("refusalTerms") or []) if n],
        "negationGuards": [n for n in (normalize_l1(t) for t in section.get("negationGuards") or []) if n],
    }


def check_anti_sales_proximity(html: str) -> bool:
    """近接共起による営業禁止判定 (HTML 全文, L1 正規化後)。

    salesTerms のいずれかの出現位置の前後 `window` 文字以内に refusalTerms のいずれかが
    共起したら True。連続複合アリアス (prohibition セクション) では拾えない分断表現
    (例:「セールス、勧誘等は固くお断りいたします」) を弾くための第2判定。

    単語単独 (「1営業日以内」等) は拒否語が近傍に無いため発火しない。
    「ご遠慮なく」のような歓迎表現は negationGuards (拒否語直後の「なく」等) で除外する。
    辞書に antiSalesProximity が無い / 空なら常に False (旧 seed 互換, no-op)。
    """
    if not html:
        return False
    conf = load_anti_sales_proximity()
    window = conf["window"]
    sales = conf["salesTerms"]
    refusals = conf["refusalTerms"]
    if window <= 0 or not sales or not refusals:
        return False
    normalized = normalize_l1(html)
    if not normalized:
        return False
    guards = conf["negationGuards"]
    n = len(normalized)
    for term in sales:
        start = 0
        while True:
            i = normalized.find(term, start)
            if i < 0:
                break
            lo = max(0, i - window)
            hi = min(n, i + len(term) + window)
            ctx = normalized[lo:hi]
            for r in refusals:
                j = ctx.find(r)
                if j < 0:
                    continue
                # negation guard: 拒否語の直後が「なく」等なら歓迎表現とみなし除外
                tail = ctx[j + len(r): j + len(r) + 4]
                if any(tail.startswith(g) for g in guards):
                    continue
                return True
            start = i + len(term)
    return False


def check_prohibition(html: str) -> bool:
    """Return True if the HTML contains any prohibition alias.

    2段構え:
      1. `prohibition` セクションの連続複合アリアスを HTML 全文に部分一致 (従来)。
      2. `antiSalesProximity` の近接共起判定 (営業語 × 拒否語が window 内に共起)。
         連続アリアスでは拾えない分断表現 (「セールス、勧誘等は固くお断りいたします」) 用。

    `antiSales` セクション ("営業" "セールス" 等の単一語) は HTML 全文に単独適用すると
    「1営業日以内」のような営業日表記で誤検知するため、単独では使わない
    (checkbox ラベル限定の `check_anti_sales_checkbox()` と、拒否語共起を課す
    `check_anti_sales_proximity()` の2経路でのみ用いる)。

    NOTE: Sync with TS engine.ts checkProhibition (HTML 全文判定は prohibition のみ、
    antiSales は engine.ts antiSalesCheckbox で label.innerText に限定して判定)。
    2026-06-06 修正: 旧版は antiSales も HTML 全文に適用していたため誤検知 (FORGION 等)。
    2026-07-07 追加: antiSalesProximity で分断表現の取りこぼしを補強 (#29/#30)。
    """
    if not html:
        return False
    normalized = normalize_l1(html)
    if not normalized:
        return False
    sections = load_prohibition()
    # antiSales は HTML 全文に単独適用しない (上記 docstring 参照)
    for alias_n in sections["prohibition"]["aliasesNormalized"]:
        if alias_n and alias_n in normalized:
            return True
    # 第2判定: 近接共起 (営業語 × 拒否語)
    if check_anti_sales_proximity(html):
        return True
    return False


def check_anti_sales_checkbox(label_text: str) -> bool:
    """Return True if a checkbox label contains any antiSales alias.

    チェックボックスのラベル ("営業目的の方は送信できません" 等) を判定する用途。
    単一語 ("営業" "セールス" "売り込み" "勧誘") を HTML 全文に適用すると誤検知するため、
    呼び出し側で個別のチェックボックス label.innerText のみを渡すこと。

    NOTE: Sync with TS engine.ts antiSalesCheckbox.
    """
    if not label_text:
        return False
    normalized = normalize_l1(label_text)
    if not normalized:
        return False
    sections = load_prohibition()
    for alias_n in sections["antiSales"]["aliasesNormalized"]:
        if alias_n and alias_n in normalized:
            return True
    return False


# -----------------------------------------------------------------------------
# Error Triggers Dictionary (Pareto noAI filter)
# -----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_error_triggers() -> dict[str, list[str]]:
    """Load error-triggers.json (noAI + ai sections).

    Returns:
        {"noAI": [aliases...], "ai": [aliases...]}

    NOTE: Sync with TS dictionaries/index.ts ERROR_TRIGGERS (L331-334).
    NOTE: L1 normalization is NOT applied here — the TS engine.ts
    catch block uses rawMsg.includes() directly.
    """
    data = _read_json("error-triggers.json")
    return {
        "noAI": list((data.get("noAI") or {}).get("aliases") or []),
        "ai": list((data.get("ai") or {}).get("aliases") or []),
    }


def should_send_to_ai(message: str) -> bool:
    """Pareto noAI filter: decide whether to delegate to AI fallback.

    Returns:
        True if the message looks AI-recoverable (delegate to AI).
        False if the message hit a noAI alias (skip AI to save cost).

    Logic (mirrors engine.ts L1084-1101):
        - If message matches any noAI alias -> False (noAI takes precedence)
        - Else if message matches any ai alias -> True
        - Else -> True (conservative default: pay for the AI call rather than
          silently dropping an unknown error)

    NOTE: `includes()` semantics — case-sensitive substring match, no L1
    normalization. The Web engine.ts uses raw .includes() and we match that.
    """
    if not message:
        return True  # conservative: unknown -> try AI
    triggers = load_error_triggers()
    if any(alias and alias in message for alias in triggers["noAI"]):
        return False
    if any(alias and alias in message for alias in triggers["ai"]):
        return True
    return True


# -----------------------------------------------------------------------------
# Confirmation Signals Dictionary (optional)
# -----------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_confirmation_signals() -> dict[str, dict[str, list[str]]]:
    """Load confirmation-signals.json. OPTIONAL: returns {} on FileNotFoundError.

    Returns:
        {
            "urlKeywords":     {"aliases": [...], "aliasesNormalized": [...]},
            "titleKeywords":   {"aliases": [...], "aliasesNormalized": [...]},
            "contentKeywords": {"aliases": [...], "aliasesNormalized": [...]},
        }
        or {} when the file is missing (Skill standalone distribution support).

    NOTE: Sync with TS dictionaries/index.ts CONFIRMATION_SIGNALS (L204-217).
    """
    try:
        data = _read_json("confirmation-signals.json")
    except FileNotFoundError:
        return {}
    out: dict[str, dict[str, list[str]]] = {}
    for key in ("urlKeywords", "titleKeywords", "contentKeywords"):
        section = data.get(key) or {}
        aliases = section.get("aliases") or []
        out[key] = {
            "aliases": list(aliases),
            "aliasesNormalized": [normalize_l1(a) for a in aliases],
        }
    return out


# -----------------------------------------------------------------------------
# Sprint 6: Form scoring / dynamic detection / contact links dictionaries
# -----------------------------------------------------------------------------
# These three were Web-version-only until Sprint 6 added Stage 1.5 (汎用
# パターンマッピング送信). The Sprint 6 sync script copies them into
# skill/dictionaries/ so the Skill can load them locally.
@lru_cache(maxsize=1)
def load_form_scoring() -> dict[str, dict[str, list[str]]]:
    """Load form-scoring.json (contactKeywords / excludeKeywords / etc.).

    Returns each section as `{"aliases": [...], "aliasesNormalized": [...]}`.
    Returns {} if the file is missing (the Stage 1.5 caller falls back to
    score-only matching).

    NOTE: Sync with TS dictionaries/index.ts loadFormScoring (L320-360).
    """
    try:
        data = _read_json("form-scoring.json")
    except FileNotFoundError:
        return {}
    out: dict[str, dict[str, list[str]]] = {}
    for key in (
        "contactKeywords",
        "excludeKeywords",
        "bodyKeywords",
        "subjectKeywords",
        "nameKeywords",
        "submitButtonKeywords",
    ):
        section = data.get(key) or {}
        aliases = section.get("aliases") or []
        out[key] = {
            "aliases": list(aliases),
            "aliasesNormalized": [normalize_l1(a) for a in aliases],
        }
    return out


@lru_cache(maxsize=1)
def load_dynamic_detection() -> dict[str, dict[str, list[str]]]:
    """Load dynamic-detection.json.

    Used by Stage 1.5 to detect "送信完了" / "ありがとうございます" patterns
    after the submit button is clicked.

    NOTE: Sync with TS dictionaries/index.ts loadDynamicDetection.
    """
    try:
        data = _read_json("dynamic-detection.json")
    except FileNotFoundError:
        return {}
    out: dict[str, dict[str, list[str]]] = {}
    for key, value in (data or {}).items():
        if key.startswith("_") or not isinstance(value, dict):
            continue
        aliases = value.get("aliases") or []
        out[key] = {
            "aliases": list(aliases),
            "aliasesNormalized": [normalize_l1(a) for a in aliases],
        }
    return out


@lru_cache(maxsize=1)
def load_contact_links() -> dict[str, list[str]]:
    """Load contact-links.json (anchor text aliases for find_form_page).

    Returns `{"aliases": [...], "aliasesNormalized": [...]}`.

    NOTE: Sync with TS dictionaries/index.ts loadContactLinks.
    """
    try:
        data = _read_json("contact-links.json")
    except FileNotFoundError:
        return {"aliases": [], "aliasesNormalized": []}
    aliases = data.get("aliases") or []
    return {
        "aliases": list(aliases),
        "aliasesNormalized": [normalize_l1(a) for a in aliases],
    }


# -----------------------------------------------------------------------------
# Module self-check (import-graph debugging)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"[_pattern_loader] dictionary dir: {_dict_dir()}")
    print(f"  - label entries: {len(load_label_dictionary())}")
    print(f"  - submit buttons positive: {len(load_submit_buttons()['positive']['aliases'])}")
    print(f"  - prohibition aliases: {len(load_prohibition()['prohibition']['aliases'])}")
    print(f"  - error triggers noAI: {len(load_error_triggers()['noAI'])}")
    sig = load_confirmation_signals()
    print(f"  - confirmation signals: {'present' if sig else 'absent (optional)'}")
    fs = load_form_scoring()
    print(f"  - form-scoring contact: {len(fs.get('contactKeywords', {}).get('aliases', []))}")
    cl = load_contact_links()
    print(f"  - contact-links aliases: {len(cl.get('aliases', []))}")
    print(f"  - normalize_l1('お問い合わせ'): {normalize_l1('お問い合わせ')!r}")
    print(f"  - match_label('お名前'): {match_label('お名前')!r}")
    print(f"  - check_prohibition('当サイトは営業お断りです'): {check_prohibition('当サイトは営業お断りです')}")
    print(f"  - should_send_to_ai('WAF blocked'): {should_send_to_ai('WAF blocked')}")
    print(f"  - should_send_to_ai('Timeout exceeded'): {should_send_to_ai('Timeout exceeded')}")
