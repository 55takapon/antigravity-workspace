"""Sprint 5 Task 2 — Lightweight form filler (Python port of TS determineValue).

Ports the `determineValue()` function from the TS form-filler and the
`semanticToValue()` helper into Python for use by the CF7 HTTP POST sender.

KISS: ONLY the value resolution path is ported. The phone-number digits-only
heuristic (form-filler.ts L75-105), the textarea body scoring, the consent
checkbox handling, and the AI-driven complex-field reasoning are NOT ported
in Sprint 5 — those require a live browser. CF7 HTTP POST works purely from
hidden + visible field metadata, so they are YAGNI for this Sprint.

NOTE: Sync with src/lib/browser/form-filler.ts L374-450 (determineValue) and
L337-372 (semanticToValue).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, TypedDict

# Sprint 6 Task 0: dual import — package context (skill.core.*) vs
# flat sys.path (skill/scripts/run_send.py inserts skill/core/ into sys.path
# so sibling modules import without prefix).
try:
    from skill.core._pattern_loader import match_label
except ImportError:
    from _pattern_loader import match_label  # type: ignore


# -----------------------------------------------------------------------------
# Types (mirror the TS FillData / FormField shapes)
# -----------------------------------------------------------------------------
class FillData(TypedDict, total=False):
    """Sender info payload.

    Keys mirror src/lib/browser/form-filler.ts L16-33 (FillData type) and
    shared/5_sender_info.example.json (repo root). `total=False` because every
    key is optional — the form filler returns None for any missing value.
    """

    senderCompanyName: str
    senderCompanyNameKana: str
    companyUrl: str
    fax: str
    name: str
    nameKana: str
    firstName: str
    lastName: str
    email: str
    phone: str
    message: str
    entityType: str  # 'corporation' | 'individual'
    nameHiragana: str
    zip: str
    address: str
    subject: str
    department: str
    position: str


@dataclass
class FormField:
    """Minimal form field descriptor.

    Mirrors src/lib/browser/form-detector.ts FormField (L4-11). Selector /
    width / height are unused by the CF7 HTTP POST path but kept so the
    dataclass shape is identical for cross-language tests.
    """

    name: str
    type: str
    label: str = ""
    selector: str = ""
    width: int = 0
    height: int = 0


# -----------------------------------------------------------------------------
# Phone number splitter (deterministic, no AI) — 分割入力欄 (市外/市内/加入者番号) 対応
# -----------------------------------------------------------------------------
# ハイフン各種 (半角/全角/長音/波ダッシュ等) と空白を区切りとして扱う。
_PHONE_SEP_PATTERN = re.compile(r"[-‐‑‒–—―ー－−ｰ・.\s]+")


def split_phone_value(phone: Optional[str], n_boxes: int) -> Optional[list[str]]:
    """電話番号を n_boxes 個の分割入力欄用に区切る (AIなし・決定論)。

    優先順位:
      1. ハイフン等の区切りで割った要素数が n_boxes と一致 → そのまま各欄へ
         (送信者が "090-9744-6892" と入れていれば 3欄に 090/9744/6892)。
      2. 数字のみを取り出し、桁数と欄数から標準的な区切りを推定
         (携帯11桁→3/4/4、固定10桁→市外は判定不能なので 3桁固定でフォールバック、
          2欄→先頭3桁と残り)。
      3. どれも当てはまらなければ None (呼び出し側が従来動作=各欄フル番号にフォールバック)。

    戻り値は各欄へ入れる文字列 (数字のみ) のリスト。長さは n_boxes。
    """
    if not phone or n_boxes < 1:
        return None
    raw = str(phone).strip()
    if n_boxes == 1:
        return [raw]

    parts = [p for p in _PHONE_SEP_PATTERN.split(raw) if p]
    # 1. 区切り済みで欄数一致 → 最優先 (送信者フォーマットを尊重)
    if len(parts) == n_boxes and all(p for p in parts):
        return parts

    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None

    # 2. 区切り数が欄数超過 → 先頭を各欄に、余りは最終欄へ寄せる
    if len(parts) > n_boxes and n_boxes >= 2:
        head = parts[: n_boxes - 1]
        tail = "".join(parts[n_boxes - 1:])
        return head + [tail]

    # 3. 桁数ベースの推定 (区切りが足りない/無い場合)
    if n_boxes == 3:
        if len(digits) == 11:  # 携帯 (090/9744/6892) or 0120 等
            return [digits[:3], digits[3:7], digits[7:]]
        if len(digits) == 10:  # 固定電話。市外局番長は可変だが判定不能→3/3/4 で近似
            return [digits[:3], digits[3:6], digits[6:]]
        return None
    if n_boxes == 2:
        if len(digits) >= 4:
            return [digits[:3], digits[3:]]
        return None
    return None


# -----------------------------------------------------------------------------
# Semantic -> value resolver (TS form-filler.ts L337-372)
# -----------------------------------------------------------------------------
def _semantic_to_value(semantic: str, data: FillData) -> Optional[str]:
    """Map a SemanticType string to the corresponding FillData value.

    Preserves the TS fallback chain (e.g. nameKana -> name when kana missing).

    NOTE: Sync with src/lib/browser/form-filler.ts semanticToValue (L337-372).
    """
    if semantic == "sender_company_name":
        return data.get("senderCompanyName") or None
    if semantic == "sender_company_name_kana":
        # 会社名カナは人名カナにフォールバックさせない（別物のため）
        return data.get("senderCompanyNameKana") or None
    if semantic == "fax":
        return data.get("fax") or None
    if semantic == "sender_last_name":
        return data.get("lastName") or None
    if semantic == "sender_first_name":
        return data.get("firstName") or None
    if semantic == "sender_name_kana":
        # existing fallback: kana -> name
        return data.get("nameKana") or data.get("name") or None
    if semantic == "sender_name_hiragana":
        # existing fallback: hiragana -> kana -> name
        return data.get("nameHiragana") or data.get("nameKana") or data.get("name") or None
    if semantic == "sender_name":
        # Sprint 5 addition: when only "sender_name" matches but the data
        # offers lastName/firstName, build the full name. Matches TS behaviour
        # of returning data.name verbatim when present; falls back to
        # "<last> <first>" if no `name` key.
        if data.get("name"):
            return data.get("name") or None
        last = data.get("lastName") or ""
        first = data.get("firstName") or ""
        combined = f"{last} {first}".strip()
        return combined or None
    if semantic == "email":
        return data.get("email") or None
    if semantic == "phone":
        return data.get("phone") or None
    if semantic == "company_url":
        return data.get("companyUrl") or None
    if semantic == "zip":
        return data.get("zip") or None
    if semantic == "address":
        return data.get("address") or None
    if semantic == "subject":
        return data.get("subject") or None
    if semantic == "department":
        return data.get("department") or None
    if semantic == "position":
        return data.get("position") or None
    return None


# -----------------------------------------------------------------------------
# determine_value (TS form-filler.ts L374-439)
# -----------------------------------------------------------------------------
def determine_value(field: FormField, data: FillData) -> Optional[str]:
    """Resolve the value to fill into a form field.

    Bit-equivalent priority order to the TS determineValue:
      PRIORITY 0: HTML type attribute (email / tel / url) — strongest signal
      PRIORITY 1: Dictionary-based label/name matching (combined / label / name)
      PRIORITY 2: Learned dictionary (Sprint 1 DB) — NOT ported in Sprint 5
                  (Phase 2-B will add this when the local SQLite cache lands).

    NOTE: Sync with src/lib/browser/form-filler.ts:374-450 (determineValue).
    The phone digits-only stripping (form-filler.ts L75-105) is intentionally
    omitted — that runs at the page level, not here.
    """
    field_type = (field.type or "").lower()

    # ========================================================
    # [PRIORITY 0] HTML type attribute (strongest)
    # ========================================================
    if field_type == "email":
        return data.get("email") or None
    if field_type == "tel":
        return data.get("phone") or None
    if field_type == "url":
        return data.get("companyUrl") or None

    # ========================================================
    # [PRIORITY 1] Dictionary-based label/name matching
    # ========================================================
    label = field.label or ""
    name = field.name or ""
    combined = f"{label} {name}".strip()

    # 1. Combined contains-match
    semantic = match_label(combined)
    if semantic:
        return _semantic_to_value(semantic, data)

    # 2. label-only (exact-mode entries often hit only when isolated)
    if label:
        semantic = match_label(label)
        if semantic:
            return _semantic_to_value(semantic, data)

    # 3. name-only
    if name:
        semantic = match_label(name)
        if semantic:
            return _semantic_to_value(semantic, data)

    return None
