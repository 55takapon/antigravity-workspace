#!/usr/bin/env python3
"""opener_helpers — ③opener-generate の非秘匿ヘルパ（配布同梱）。

HP取得（requests→Playwrightフォールバック）・shared/ のテキスト/設定ロード・
プレースホルダ差し込みなど、**生成ノウハウを含まない汎用処理だけ**をここに集約する。
秘匿の生成プロンプト組み立て・API呼び出し・payload読込は generate_openers.py
（dev専用・配布除外）側に閉じる。

配布同梱スクリプト（prep_openers.py / assemble_openers.py）はこのモジュールを参照する。
generate_openers.py（dev）も同じ実装をここから import して**単一ソース**を保つ。

背景: 以前はこれらのヘルパが generate_openers.py に同居しており、同ファイルを配布除外
（秘匿IP）にした際にヘルパごと消え、配布物の prep/assemble が import で落ちていた。
非秘匿ヘルパを本ファイルへ分離することで、秘匿は隠しつつ配布物は起動する。
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# --- パス解決（このスキルディレクトリ基準） ---
SKILL_DIR = Path(__file__).resolve().parent.parent          # .../opener-generate
REPO_ROOT = SKILL_DIR.parent.parent.parent                  # リポジトリルート
COMMON_BODY = REPO_ROOT / "shared" / "common_body.md"       # 共通本文（サンドイッチの下パン）
INTRO = REPO_ROOT / "shared" / "intro.md"                   # 宛名＋名乗り（上パン）
SENDER_INFO = REPO_ROOT / "shared" / "sender_info.json"     # 自社の名乗りソース


# shared/.env（無ければ各所の .env）から APIキー等を読み込む
def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for p in (REPO_ROOT / "shared" / ".env", SKILL_DIR / ".env", REPO_ROOT / ".env"):
        if p.exists():
            load_dotenv(p, override=False)


_load_env()

HTTP_TIMEOUT = 15
# HP本文をこの文字数に切り詰める。既定4000。--hp-max / 環境変数 HP_TEXT_MAX で下げると入力トークンが減る（opt-in）。
HP_TEXT_MAX = int(os.environ.get("HP_TEXT_MAX", "4000"))
# 本文抽出モード。既定 "raw"（全テキスト）。"signal"＝nav/footer/定型を捨て要点だけ（抽出が空なら raw へ自動フォールバック）。
EXTRACT_MODE = os.environ.get("OPENER_EXTRACT", "raw")
MIN_TEXT_LEN = 200   # requests取得の本文がこの文字数未満なら「取れていない」とみなし
                     # JS描画フォールバック(Playwright)に切り替える。静的サイトはここで完結する
HP_UA = "Mozilla/5.0 (compatible; opener-generate/0.1)"


# ---------------------------------------------------------------- HP取得・本文抽出
def fetch_hp_text(url: str) -> str:
    """HP を取得し可読テキストを返す。失敗時は空文字。

    段階的取得（tiered fetching）:
      1. requests（軽量・高速）でまず取得。本文が十分に取れたらそこで終了（大多数の静的サイト）。
      2. 本文が空/極端に薄い（JS描画サイトの可能性）→ そのURLだけ Playwright で再取得。
    Playwright は未インストールでも静かに諦め、requests の結果（空でも）を返す（Fail-safe）。
    """
    if not (url or "").strip():
        return ""
    text = _fetch_static(url)
    if len(text) >= MIN_TEXT_LEN:
        return text
    # 静的取得で本文が薄い/空 → JS描画が必要なサイトとみなし Playwright で再取得
    rendered = render_hp_text(url)
    return rendered if len(rendered) > len(text) else text


def _fetch_static(url: str) -> str:
    """requests でHTMLを取得して可読テキストへ。失敗時は空文字（高速パス）。"""
    try:
        import requests
    except ImportError:
        print("[warn] requests 未インストール。--dry-run 以外では `pip install requests beautifulsoup4` が必要", file=sys.stderr)
        return ""
    try:
        resp = requests.get(url, headers={"User-Agent": HP_UA}, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        html = _decode_response(resp)
    except Exception as e:  # noqa: BLE001 — Fail-safe
        print(f"[warn] HP取得失敗(static) {url}: {e}", file=sys.stderr)
        return ""
    return _html_to_text(html)[:HP_TEXT_MAX]


def _decode_response(resp) -> str:
    """文字化け対策つきでレスポンス本文をデコードする。

    requests の `resp.text` は charset 未宣言サイトを ISO-8859-1 と決め打ちするため、
    Shift_JIS / EUC-JP / 宣言なしUTF-8 の日本語サイトが文字化けする（営業文の品質に直結）。
    → HTTPヘッダの charset が信頼できないときだけ apparent_encoding（chardet系の推定）に切替える。
    """
    enc = resp.encoding
    # ヘッダ未宣言時に requests が入れる既定値や空は信用せず、本文から推定する
    if not enc or enc.lower() in ("iso-8859-1", "ascii"):
        enc = resp.apparent_encoding or "utf-8"
    try:
        return resp.content.decode(enc, errors="replace")
    except (LookupError, TypeError):  # 未知のエンコーディング名など
        return resp.text


# --- JS描画フォールバック（Playwright）。requestsで本文が取れない社にだけ使う ---
# ブラウザは1ラン中に一度だけ起動して使い回す（社ごとに起動するとコストが大きい）。
_PW = {"started": False, "pw": None, "browser": None}


def _get_browser():
    """Playwright のブラウザを遅延起動して使い回す。
    未インストール/起動失敗時は None を返し、呼び出し側は静かに諦める（Fail-safe）。"""
    if _PW["started"]:
        return _PW["browser"]
    _PW["started"] = True
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[info] playwright 未導入のためJS描画フォールバックは無効。"
              "有効化: `uv pip install playwright && playwright install chromium`", file=sys.stderr)
        return None
    try:
        import atexit
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        _PW["pw"], _PW["browser"] = pw, browser
        atexit.register(_close_browser)
        return browser
    except Exception as e:  # noqa: BLE001 — Fail-safe（描画なしで続行）
        print(f"[warn] Playwright 起動失敗: {e}（JS描画フォールバック無効）", file=sys.stderr)
        return None


def _close_browser() -> None:
    try:
        if _PW["browser"]:
            _PW["browser"].close()
        if _PW["pw"]:
            _PW["pw"].stop()
    except Exception:  # noqa: BLE001
        pass


def render_hp_text(url: str) -> str:
    """JSを実行してから本文を取得（STUDIO等のSPA向け）。失敗時は空文字。"""
    browser = _get_browser()
    if browser is None:
        return ""
    page = None
    try:
        page = browser.new_page(user_agent=HP_UA)
        try:
            page.goto(url, timeout=HTTP_TIMEOUT * 1000, wait_until="networkidle")
        except Exception:  # noqa: BLE001 — タイムアウトでも、その時点で描画済みの内容を拾う
            pass
        html = page.content()
    except Exception as e:  # noqa: BLE001 — Fail-safe
        print(f"[warn] HP取得失敗(render) {url}: {e}", file=sys.stderr)
        return ""
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:  # noqa: BLE001
                pass
    return _html_to_text(html)[:HP_TEXT_MAX]


def _html_to_text(html: str) -> str:
    """EXTRACT_MODE に応じて分岐。"signal"（レバーA）なら定型を捨てて要点だけ返す。"""
    if EXTRACT_MODE == "signal":
        signal = _html_to_signal_text(html)
        if signal:                      # 抽出に成功したときだけ採用（Fail-safe：空なら raw に落ちる）
            return signal
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n")
    except ImportError:
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


# レバーA（#26）: 冒頭文に効かない定型（nav/header/footer/copyright/menu 等）を捨て、
# 効く所（<title>・meta description・見出し h1〜h4・本文段落）だけ残す決定論的抽出。
# 目的は「読む量を半分〜1/3に、固有引用の材料は温存」。BeautifulSoup 前提（無ければ空を返し raw に委ねる）。
_BOILERPLATE_TAGS = ("script", "style", "noscript", "nav", "header", "footer",
                     "aside", "form", "svg", "button", "iframe")
# class/id にこれらを含む要素は定型とみなして落とす（グローバルナビ/パンくず/著作権表記など）
_BOILERPLATE_HINT = re.compile(
    r"nav|menu|gnav|global|breadcrumb|pankuzu|footer|header|copyright|sidebar|"
    r"widget|banner|cookie|pagetop|sns|share|drawer|hamburger",
    re.I)


def _html_to_signal_text(html: str) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return ""                        # bs4 無し → raw フォールバック
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(list(_BOILERPLATE_TAGS)):
        tag.decompose()
    # class/id ヒントに当たる要素を除去（ページ全体を消さないよう body/main は温存）
    for el in soup.find_all(True):
        # 親を decompose 済みだと子孫は attrs=None になる → 触らず飛ばす（Fail-safe）
        if getattr(el, "decomposed", False) or el.attrs is None:
            continue
        if el.name in ("body", "main", "article", "html"):
            continue
        cls = el.get("class") or []
        ident = " ".join(filter(None, [
            " ".join(cls) if isinstance(cls, list) else str(cls),
            el.get("id") or "", el.get("role") or ""]))
        if ident and _BOILERPLATE_HINT.search(ident):
            el.decompose()

    parts: list[str] = []
    seen: set[str] = set()

    def _push(s: str) -> None:
        s = re.sub(r"\s+", " ", (s or "")).strip()
        if s and s not in seen and len(s) > 1:
            seen.add(s)
            parts.append(s)

    if soup.title and soup.title.string:
        _push(soup.title.string)
    for sel in ('meta[name="description"]', 'meta[property="og:description"]'):
        m = soup.select_one(sel)
        if m and m.get("content"):
            _push(m["content"])
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        _push(h.get_text(" "))
    # 本文段落：main/article があればそこ、無ければ body 全体から p / li を拾う
    root = soup.find("main") or soup.find("article") or soup.body or soup
    for p in root.find_all(["p", "li", "td", "dd", "figcaption"]):
        _push(p.get_text(" "))
    return "\n".join(parts).strip()


# ---------------------------------------------------------------- shared/ ローダ（非秘匿）
def _read_marker_text(path: Path) -> str:
    """`---本文ここから---` 〜 `---本文ここまで---` の間を返す（無ければ全文）。"""
    if not path.exists():
        return ""
    raw = path.read_text(encoding="utf-8")
    m = re.search(r"---本文ここから---\n(.*?)\n---本文ここまで---", raw, flags=re.S)
    return (m.group(1).strip() if m else raw.strip())


def load_common_body() -> str:
    """shared/common_body.md の本文マーカー間（サンドイッチの下パン）。"""
    return _read_marker_text(COMMON_BODY)


def load_intro() -> str:
    """shared/intro.md の本文マーカー間（宛名＋名乗り＝上パン）。"""
    return _read_marker_text(INTRO)


def load_sender_info() -> dict:
    """shared/sender_info.json を読む（名乗りの差し込み用）。無ければ空。"""
    import json
    if not SENDER_INFO.exists():
        return {}
    try:
        return json.loads(SENDER_INFO.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — Fail-safe
        return {}


def fill_placeholders(text: str, company: str, sender: dict) -> str:
    """テンプレ中のプレースホルダを相手会社名・自社情報で差し込む。"""
    sender_name = (sender.get("lastName") or "").strip() or sender.get("senderCompanyName", "")
    sender_full = f"{sender.get('lastName', '')}{sender.get('firstName', '')}".strip() or sender_name
    return (text.replace("{company_name}", company)
                .replace("{sender_company}", sender.get("senderCompanyName", ""))
                .replace("{sender_name}", sender_name)
                .replace("{sender_full_name}", sender_full))
