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

# --- 拡張取得（会社紹介ページの限定探索）の閾値 ---
# 単純な文字数だけだと「グローバルナビの語が並んでいるだけのページ」が本文として合格してしまう
# （実測: 求人404ページがナビだけで358字＝MIN_TEXT_LEN合格）。そこで“中身のある文章の量”で測り直す。
PROSE_MIN_LINE = 20   # この文字数以上の行だけを本文とみなして合計する（ナビ語は1行が短い）
# 起点ページの散文量がこれ未満なら会社紹介ページを探しに行く。既定300。
# 根拠: 実データ198社の実測で prose<300 は9.6%（<400 だと16.7%へ急増し健全なページを巻き込む）。
THIN_PROSE = int(os.environ.get("OPENER_THIN_PROSE", "300"))
# 探して見つけたページは、この散文量以上のときだけ採用する。既定100。
# 発火閾値と別値にするのは、会社概要ページが表形式（設立年・所在地）で散文量が低く出るため
# （実測: kitobi /about/ =121・Sole Collect /company.html =105。ここを300にすると会社概要を捨てる）。
MIN_PAGE_PROSE = int(os.environ.get("OPENER_MIN_PAGE_PROSE", "100"))
MAX_EXTRA_PAGES = int(os.environ.get("OPENER_MAX_EXTRA_PAGES", "2"))   # 1社あたり追加で読むページ数の上限
PER_PAGE_MAX = int(os.environ.get("OPENER_PER_PAGE_MAX", "2000"))      # 1ページが全体の枠を食い潰さないための上限


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


def _fetch_raw(url: str, *, quiet: bool = False) -> tuple[int | None, str]:
    """requests でHTMLを取得し `(HTTPステータス, HTML)` を返す。失敗時は `(None, "")`。

    拡張取得はリンク抽出のため**HTML本体**を、404判定のため**ステータス**を必要とする。
    既存の `_fetch_static` はこの上の薄いラッパに変わるだけで、返り値も挙動も従来どおり。
    """
    try:
        import requests
    except ImportError:
        if not quiet:
            print("[warn] requests 未インストール。--dry-run 以外では `pip install requests beautifulsoup4` が必要",
                  file=sys.stderr)
        return None, ""
    try:
        resp = requests.get(url, headers={"User-Agent": HP_UA}, timeout=HTTP_TIMEOUT)
        status = resp.status_code
        html = _decode_response(resp)
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001 — Fail-safe
        if not quiet:
            print(f"[warn] HP取得失敗(static) {url}: {e}", file=sys.stderr)
        # ステータスは取れているがエラー応答（404等）のケースは status だけ返す（本文は使わせない）
        return (locals().get("status"), "")
    return status, html


def _fetch_static(url: str) -> str:
    """requests でHTMLを取得して可読テキストへ。失敗時は空文字（高速パス）。"""
    _, html = _fetch_raw(url)
    return _html_to_text(html)[:HP_TEXT_MAX] if html else ""


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


def _render_raw(url: str) -> tuple[int | None, str]:
    """JSを実行してから `(HTTPステータス, HTML)` を返す（STUDIO等のSPA向け）。失敗時は `(None, "")`。

    ★ここでステータスを拾うのが要点。以前は `page.goto` の戻り値（Response）を捨てていたため、
    **404ページをそのまま描画してグローバルナビを「HP本文」として持ち帰っていた**
    （静的取得が404で空→薄いと判定→この経路に落ちる、が実際の発生経路）。
    """
    browser = _get_browser()
    if browser is None:
        return None, ""
    page, status = None, None
    try:
        page = browser.new_page(user_agent=HP_UA)
        try:
            resp = page.goto(url, timeout=HTTP_TIMEOUT * 1000, wait_until="networkidle")
            if resp is not None:
                status = resp.status
        except Exception:  # noqa: BLE001 — タイムアウトでも、その時点で描画済みの内容を拾う
            pass
        html = page.content()
    except Exception as e:  # noqa: BLE001 — Fail-safe
        print(f"[warn] HP取得失敗(render) {url}: {e}", file=sys.stderr)
        return None, ""
    finally:
        if page is not None:
            try:
                page.close()
            except Exception:  # noqa: BLE001
                pass
    return status, html


def render_hp_text(url: str) -> str:
    """JSを実行してから本文を取得（STUDIO等のSPA向け）。失敗時は空文字。"""
    _, html = _render_raw(url)
    return _html_to_text(html)[:HP_TEXT_MAX] if html else ""


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


# ---------------------------------------------------------------- 拡張取得（会社紹介ページの限定探索）
def prose_len(text: str) -> int:
    """“中身のある文章の量”。PROSE_MIN_LINE 文字以上の行だけを合計する。

    単純な文字数だと、グローバルナビの語（1行が短い）が並ぶだけのページが本文として合格する。
    行の長さで足切りすると、ナビ主体ページと本文ページが実測できれいに分かれる
    （実測: ナビのみ=41〜145 / 本文あり=305以上が大半）。
    """
    return sum(len(ln.strip()) for ln in (text or "").split("\n") if len(ln.strip()) >= PROSE_MIN_LINE)


# 会社紹介ページらしさのスコア。パス（URL）とアンカーテキストの両方から加点する。
_PATH_HINTS = [
    (re.compile(r"(^|/)(about|company|corporate|profile)(/|$|\.)", re.I), 5),
    (re.compile(r"(^|/)(philosophy|concept|vision|mission|value)(/|$|\.)", re.I), 5),
    (re.compile(r"(^|/)(message|greeting|ceo|president|representative)(/|$|\.)", re.I), 4),
    # works（実績一覧）は案件名の羅列になりやすく冒頭文の材料として弱いので候補にしない
    (re.compile(r"(^|/)(service|business|strength)(/|$|\.)", re.I), 2),
]
_TEXT_HINTS = [("会社概要", 5), ("企業情報", 5), ("私たちについて", 5), ("理念", 5), ("ビジョン", 5),
               ("コンセプト", 5), ("ごあいさつ", 4), ("代表", 4), ("ミッション", 4),
               ("about", 4), ("company", 4), ("事業内容", 3), ("私たち", 3), ("強み", 3)]
# 冒頭文の材料にならない／むしろ品質を下げるリンクは候補にしない。
# recruit を落とすのは、求人票（職種・待遇の羅列）が混ざると最も汎用的な語を掴んだ薄い出力になりやすいため。
_LINK_DENY = re.compile(
    r"(news|blog|column|contact|privacy|sitemap|recruit|entry|login|cart|"
    r"mailto:|tel:|javascript:|\.pdf|\.jpg|\.jpeg|\.png|\.zip)", re.I)


def _candidate_pages(root_url: str, html: str, limit: int) -> list[str]:
    """ルートHTMLのリンクから「会社紹介ページ」候補を選ぶ（同一ホスト・スコア順・浅い順）。"""
    from urllib.parse import urldefrag, urljoin, urlparse
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        anchors = [(a.get("href") or "", a.get_text(" ").strip()) for a in soup.find_all("a")]
    except Exception:  # noqa: BLE001 — bs4 無し等。拡張を諦めるだけ（Fail-safe）
        return []
    host = urlparse(root_url).netloc
    scored: dict[str, tuple[int, int]] = {}
    for href, text in anchors:
        if not href or _LINK_DENY.search(href):
            continue
        absu = urldefrag(urljoin(root_url, href))[0].rstrip("/")
        p = urlparse(absu)
        # 同一ホストのみ（外部サイト・SNSへ出て行かない）。ルート自身は候補にしない
        if p.netloc != host or not p.scheme.startswith("http") or not p.path.strip("/"):
            continue
        score = sum(w for pat, w in _PATH_HINTS if pat.search(p.path))
        score += sum(w for k, w in _TEXT_HINTS if k.lower() in text.lower())
        if score <= 0:
            continue
        depth = p.path.strip("/").count("/")
        if absu not in scored or score > scored[absu][0]:
            scored[absu] = (score, depth)
    # スコア降順 → 階層が浅い順 → URL順（決定論：同じサイトなら常に同じ2件を選ぶ）
    ranked = sorted(scored.items(), key=lambda kv: (-kv[1][0], kv[1][1], kv[0]))
    return [u for u, _ in ranked[:limit]]


def _assemble_blocks(pages: list[tuple[str, str]]) -> str:
    """複数ページを見出し付きで連結する。**全ページに共通して出る行＝ナビ/フッタを落とす**。

    単純な「既出行の除去」では、最初のブロックに載ったナビが残ってしまう
    （ナビは1ページ目の先頭に出るため）。2ページ以上あるときは、
    複数ページに現れる行を先に数えて落としてから連結する。
    """
    from collections import Counter
    freq: Counter = Counter()
    if len(pages) >= 2:
        for _, text in pages:
            for s in {ln.strip() for ln in (text or "").split("\n") if ln.strip()}:
                freq[s] += 1

    seen: set[str] = set()
    blocks = []
    for label, text in pages:
        lines = []
        for ln in (text or "").split("\n"):
            s = ln.strip()
            if not s or s in seen or freq.get(s, 0) >= 2:   # 共通行＝ナビ/フッタ/著作権表記
                continue
            seen.add(s)
            lines.append(s)
        body = "\n".join(lines)[:PER_PAGE_MAX].strip()
        if body:
            blocks.append(f"{label}\n{body}")
    return "\n\n".join(blocks).strip()


def fetch_company_text(url: str, *, expand: bool = True, thin_prose: int | None = None) -> dict:
    """冒頭文の材料としてのHP本文を取る。薄いときだけ会社紹介ページを追加で読む。

    返り値: `{"text": 本文, "sources": [出典URL], "prose": 散文量, "expanded": bool}`

    設計:
      - 起点ページ（`url`）が十分（散文量 >= thin_prose）なら**追加リクエストはゼロ**＝従来と完全に同じ。
      - 薄い／HTTPエラーのときだけ、ドメインルートのリンクから会社紹介ページを最大 MAX_EXTRA_PAGES 件だけ読む。
      - 何が起きても例外は投げない。失敗時は従来の `fetch_hp_text` 相当に落ちる（Fail-safe）。
    """
    url = (url or "").strip()
    if not url:
        return {"text": "", "sources": [], "prose": 0, "expanded": False}
    try:
        return _fetch_company_text(url, expand, THIN_PROSE if thin_prose is None else thin_prose)
    except Exception as e:  # noqa: BLE001 — 拡張はあくまで上積み。壊れたら従来経路へ
        print(f"[warn] 拡張取得に失敗したため従来の取得に戻します {url}: {e}", file=sys.stderr)
        text = fetch_hp_text(url)
        return {"text": text, "sources": [url] if text else [], "prose": prose_len(text), "expanded": False}


def _fetch_company_text(url: str, expand: bool, thin: int) -> dict:
    from urllib.parse import urlparse

    # --- 1) 起点ページ（従来と同じ順序：静的 → 薄ければJS描画）---
    status, html = _fetch_raw(url)
    text = _html_to_text(html)[:HP_TEXT_MAX] if html else ""
    if len(text) < MIN_TEXT_LEN:
        r_status, r_html = _render_raw(url)
        r_text = _html_to_text(r_html)[:HP_TEXT_MAX] if r_html else ""
        if len(r_text) > len(text):
            status, html, text = (r_status if r_status is not None else status), r_html, r_text
    # HTTPエラーのページ（404の「お探しのページは見つかりません」＋グローバルナビ等）は本文として使わない。
    # ここを通していたのが「ナビだけの404ページを会社説明として生成に渡していた」不具合の本体。
    if status is not None and status >= 400:
        print(f"[warn] HTTP {status} のページは本文として使いません: {url}", file=sys.stderr)
        text, html = "", ""
    prose = prose_len(text)

    if not expand or prose >= thin:
        return {"text": text, "sources": [url] if text else [], "prose": prose, "expanded": False}

    # --- 2) 薄いので会社紹介ページを探す ---
    p = urlparse(url)
    root = f"{p.scheme}://{p.netloc}/"
    is_root = url.rstrip("/") == root.rstrip("/")
    if is_root:
        root_html, root_text = html, text          # 起点がルート＝追加リクエスト不要（実測で大半がこれ）
    else:
        _, root_html = _fetch_raw(root, quiet=True)
        root_text = _html_to_text(root_html)[:HP_TEXT_MAX] if root_html else ""

    picked: list[tuple[str, str]] = []
    for cand in _candidate_pages(root, root_html, MAX_EXTRA_PAGES) if root_html else []:
        c_status, c_html = _fetch_raw(cand, quiet=True)
        if c_status != 200 or not c_html:
            continue
        c_text = _html_to_text(c_html)[:HP_TEXT_MAX]
        if prose_len(c_text) < MIN_PAGE_PROSE:     # 発火閾値とは別の下限（会社概要は表形式で散文量が低い）
            continue
        # 同じ中身を2つのURLで配っているサイト（/about/ と /company/ が同一等）は1件だけ採る。
        # ★これを許すと _assemble_blocks の「共通行＝ナビ」除去が全行に当たって本文が消え、救済が空振りする
        if any(c_text == t for _, t in picked):
            continue
        picked.append((cand, c_text))

    # --- 3) 連結。HP_TEXT_MAX は末尾を単純に切るので、価値の高い順に並べる ---
    pages, sources = [], []
    for cand, c_text in picked:                     # 理念・代表の言葉＝最も個別化が強い材料を先頭に
        pages.append(("【会社紹介】", c_text))
        sources.append(cand)
    if not is_root and prose_len(root_text) >= MIN_PAGE_PROSE:
        pages.append(("【トップページ】", root_text))
        sources.append(root)
    if text:                                        # 起点ページは最後（求人ページのことが多く、文言に引っ張られやすい）
        pages.append(("【起点ページ】", text))
        sources.append(url)

    # 会社紹介ページが1件も採れなかった＝実質 起点ページだけ。見出しを付けても情報は増えないので
    # 従来の本文をそのまま返す（拡張が空振りした社は変更前と1文字も変わらない）。
    # ★判定は `picked` で行う。`len(pages)` で見ると「起点が404で本文ゼロ＋会社紹介1件だけ採れた」社の
    #   救済まで捨てて材料ゼロに戻してしまう（＝この Issue で塞ぐはずの静かな劣化そのもの）。
    if not picked and len(pages) <= 1:
        return {"text": text, "sources": [url] if text else [], "prose": prose, "expanded": False}

    merged = _assemble_blocks(pages)[:HP_TEXT_MAX].strip()
    if not merged:
        return {"text": text, "sources": [url] if text else [], "prose": prose, "expanded": False}
    # 起点ページ以外から材料を採れたら拡張扱い（1件だけ採れた社も「拡張」として数える＝ログの正直さ）
    return {"text": merged, "sources": sources, "prose": prose_len(merged), "expanded": sources != [url]}


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
