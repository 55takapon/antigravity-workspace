"""select/radio の選択肢を AI なしで選ぶ軽量ユーティリティ。

外部依存なし（標準ライブラリのみ）。fuzzywuzzy 等は使わない。

- normalize: NFKC（全角/半角統一）+ lowercase + 空白除去
- best_option(target, options): 目的値に最も近い選択肢を編集距離で選ぶ
- default_inquiry_option(options): 営業の汎用問い合わせに無難な選択肢を選ぶ
  （その他/お問い合わせ等。求人/取材/苦情などは安全側で除外）

外部調査（Bitwarden/Firefox のルールベース＋Levenshtein/正規化）で確認した
「フィールド値マッチングは大半が AI なしのヒューリスティックで足りる」を実装したもの。
"""
from __future__ import annotations

import unicodedata


def normalize(s: str) -> str:
    """NFKC（全半角統一）+ 小文字化 + 空白除去。"""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    return "".join(s.split())


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def similarity(a: str, b: str) -> float:
    """0.0〜1.0 の類似度（正規化後の編集距離ベース）。"""
    a, b = normalize(a), normalize(b)
    if not a and not b:
        return 1.0
    m = max(len(a), len(b))
    if m == 0:
        return 0.0
    return 1.0 - _levenshtein(a, b) / m


def best_option(target: str, options: list[str], threshold: float = 0.6) -> str | None:
    """target に最も近い option を返す。完全一致 > 部分一致 > 編集距離。

    閾値未満しか無ければ None（無理に選ばない＝誤送信防止）。
    """
    if not target or not options:
        return None
    nt = normalize(target)
    # 1) 正規化後の完全一致
    for opt in options:
        if normalize(opt) == nt:
            return opt
    # 2) 正規化後の部分一致（どちらかが他方を含む）
    for opt in options:
        no = normalize(opt)
        if no and (nt in no or no in nt):
            return opt
    # 3) 編集距離スコア最大（閾値以上のみ）
    best: str | None = None
    best_score = 0.0
    for opt in options:
        sc = similarity(target, opt)
        if sc > best_score:
            best, best_score = opt, sc
    return best if best_score >= threshold else None


# 営業の汎用問い合わせとして無難な選択肢（優先順）。
_INQUIRY_POS = [
    "その他", "お問い合わせ", "お問合せ", "お問合わせ", "問い合わせ", "問合せ",
    "ご相談", "相談", "一般", "general", "inquiry", "other",
]
# これらに当たる選択肢は自動選択しない（明らかに目的外）。
_INQUIRY_NEG = [
    "求人", "採用", "応募", "エントリー", "取材", "プレス", "報道", "メディア",
    "苦情", "クレーム", "個人情報", "退会", "解約",
]


def default_inquiry_option(options: list[str]) -> str | None:
    """営業の汎用問い合わせに無難な選択肢を選ぶ。

    判断が割れる/該当なしの場合は None を返す（→ Claude ハンドオフや人間アシストへ）。
    """
    if not options:
        return None
    cand: list[tuple[int, str]] = []
    for opt in options:
        no = normalize(opt)
        if not no:
            continue
        if any(normalize(neg) in no for neg in _INQUIRY_NEG):
            continue
        for rank, pos in enumerate(_INQUIRY_POS):
            if normalize(pos) in no:
                cand.append((rank, opt))
                break
    if not cand:
        return None
    cand.sort(key=lambda x: x[0])
    return cand[0][1]
