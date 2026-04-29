#!/usr/bin/env python3
"""
Classify web-related companies as web production, web marketing, hybrid, or unknown.

This script intentionally uses rule-based scoring instead of LLM calls:
- fetches a small number of pages per site
- extracts title/meta/headings/nav/link/body text
- scores terms from rules/web_company_classification_rules.json
- writes a CSV with scores, evidence terms, and source pages
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RULES = SCRIPT_DIR.parent / "rules" / "web_company_classification_rules.json"
DEFAULT_CACHE_DIR = SCRIPT_DIR.parent / ".cache" / "site_classification"


@dataclass
class PageText:
    url: str
    title: str = ""
    meta_description: str = ""
    h1: str = ""
    h2: str = ""
    nav: str = ""
    link_text: str = ""
    body: str = ""
    links: List[Tuple[str, str]] = None

    def __post_init__(self) -> None:
        if self.links is None:
            self.links = []


class TextExtractingHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: List[str] = []
        self.meta_description = ""
        self.h1_parts: List[str] = []
        self.h2_parts: List[str] = []
        self.nav_parts: List[str] = []
        self.link_parts: List[str] = []
        self.body_parts: List[str] = []
        self.links: List[Tuple[str, str]] = []
        self._tag_stack: List[str] = []
        self._current_link_href: Optional[str] = None
        self._current_link_text: List[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}
        self._tag_stack.append(tag)

        if tag in {"script", "style", "noscript", "svg", "canvas"}:
            self._skip_depth += 1
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            if name == "description" or prop == "og:description":
                content = attrs_dict.get("content", "")
                if content and not self.meta_description:
                    self.meta_description = content
        elif tag == "a":
            self._current_link_href = attrs_dict.get("href", "")
            self._current_link_text = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg", "canvas"} and self._skip_depth:
            self._skip_depth -= 1

        if tag == "a" and self._current_link_href is not None:
            text = normalize_space(" ".join(self._current_link_text))
            self.links.append((self._current_link_href, text))
            if text:
                self.link_parts.append(text)
            self._current_link_href = None
            self._current_link_text = []

        for i in range(len(self._tag_stack) - 1, -1, -1):
            if self._tag_stack[i] == tag:
                del self._tag_stack[i:]
                break

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = normalize_space(data)
        if not text:
            return

        active = set(self._tag_stack)
        if "title" in active:
            self.title_parts.append(text)
        if "h1" in active:
            self.h1_parts.append(text)
        if "h2" in active:
            self.h2_parts.append(text)
        if "nav" in active:
            self.nav_parts.append(text)
        if self._current_link_href is not None:
            self._current_link_text.append(text)
        self.body_parts.append(text)

    def page_text(self, url: str) -> PageText:
        return PageText(
            url=url,
            title=normalize_space(" ".join(self.title_parts)),
            meta_description=normalize_space(self.meta_description),
            h1=normalize_space(" ".join(self.h1_parts)),
            h2=normalize_space(" ".join(self.h2_parts)),
            nav=normalize_space(" ".join(self.nav_parts)),
            link_text=normalize_space(" ".join(self.link_parts)),
            body=normalize_space(" ".join(self.body_parts)),
            links=self.links,
        )


def normalize_space(value: str) -> str:
    return re.sub(r"[\s\u3000]+", " ", html.unescape(value or "")).strip()


def normalize_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value):
        value = "https://" + value
    split = urlsplit(value)
    if split.scheme and split.scheme.lower() not in {"http", "https"}:
        return ""
    scheme = split.scheme.lower() if split.scheme else "https"
    netloc = split.netloc.lower()
    if not netloc:
        return ""
    path = split.path or "/"
    return urlunsplit((scheme, netloc, path, split.query, ""))


def domain_of(url: str) -> str:
    host = urlsplit(url).hostname or ""
    host = host.lower().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def same_site(url: str, base_domain: str) -> bool:
    host = domain_of(url)
    return host == base_domain or host.endswith("." + base_domain)


def cache_path(cache_dir: Path, url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return cache_dir / f"{digest}.html"


def fetch_url(url: str, rules: dict, cache_dir: Path, use_cache: bool) -> Tuple[Optional[str], str]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_path(cache_dir, url)
    if use_cache and path.exists():
        return path.read_text(encoding="utf-8", errors="ignore"), "cache"

    headers = {"User-Agent": rules["fetch"]["user_agent"]}
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=rules["fetch"]["timeout_seconds"]) as response:
            content_type = response.headers.get("content-type", "")
            raw = response.read(rules["fetch"]["max_bytes_per_page"])
    except Exception as exc:
        return None, f"error:{type(exc).__name__}"

    if "html" not in content_type.lower() and raw[:100].lower().find(b"<html") == -1:
        return None, "error:not_html"

    text = raw.decode("utf-8", errors="ignore")
    path.write_text(text, encoding="utf-8")
    return text, "network"


def parse_html(url: str, text: str) -> PageText:
    parser = TextExtractingHTMLParser()
    try:
        parser.feed(text)
    except Exception:
        pass
    return parser.page_text(url)


def link_priority(href: str, text: str, base_url: str, base_domain: str, rules: dict) -> Optional[int]:
    absolute = normalize_url(urljoin(base_url, href))
    if not absolute:
        return None
    absolute, _fragment = urldefrag(absolute)
    if not absolute or not same_site(absolute, base_domain):
        return None
    if absolute == base_url:
        return None

    haystack = f"{absolute} {text}".lower()
    if any(keyword.lower() in haystack for keyword in rules["page_selection"]["skip_link_keywords"]):
        return None

    preferred = rules["page_selection"]["preferred_internal_link_keywords"]
    for index, keyword in enumerate(preferred):
        if keyword.lower() in haystack:
            return index
    return None


def choose_pages(start_url: str, first_page: PageText, rules: dict) -> List[str]:
    base_domain = domain_of(start_url)
    candidates: List[Tuple[int, str]] = []
    seen = {start_url}
    for href, text in first_page.links:
        absolute = normalize_url(urljoin(start_url, href))
        if not absolute:
            continue
        absolute, _fragment = urldefrag(absolute)
        if absolute in seen:
            continue
        priority = link_priority(href, text, start_url, base_domain, rules)
        if priority is None:
            continue
        seen.add(absolute)
        candidates.append((priority, absolute))

    candidates.sort(key=lambda item: (item[0], len(item[1])))
    max_pages = rules["fetch"]["max_pages_per_site"]
    return [url for _priority, url in candidates[: max(0, max_pages - 1)]]


def count_term(text: str, term: str, cap: int) -> int:
    if not text or not term:
        return 0
    return min(len(re.findall(re.escape(term), text, flags=re.IGNORECASE)), cap)


def score_category(pages: Sequence[PageText], category_rules: dict, rules: dict) -> Tuple[int, List[str]]:
    section_weights = rules["section_weights"]
    cap = rules["scoring"]["max_occurrences_per_term_per_page"]
    strong_bonus = rules["scoring"]["strong_term_bonus"]
    title_or_h1_bonus = rules["scoring"]["title_or_h1_bonus"]

    score = 0
    evidence: Dict[str, int] = {}
    weighted_terms = [(term, 2, False) for term in category_rules.get("terms", [])]
    weighted_terms += [(term, 4, True) for term in category_rules.get("strong_terms", [])]

    for page in pages:
        sections = {
            "title": page.title,
            "meta_description": page.meta_description,
            "h1": page.h1,
            "h2": page.h2,
            "nav": page.nav,
            "link_text": page.link_text,
            "body": page.body,
        }
        for term, base_weight, is_strong in weighted_terms:
            term_hits = 0
            term_score = 0
            for section, text in sections.items():
                hits = count_term(text, term, cap)
                if not hits:
                    continue
                term_hits += hits
                term_score += hits * base_weight * section_weights.get(section, 1)
                if section in {"title", "h1"}:
                    term_score += title_or_h1_bonus
            if term_hits:
                if is_strong:
                    term_score += strong_bonus
                evidence[term] = evidence.get(term, 0) + term_hits
                score += term_score

    sorted_evidence = sorted(evidence.items(), key=lambda item: (-item[1], item[0]))
    return score, [term for term, _hits in sorted_evidence[:20]]


def classify(production_score: int, marketing_score: int, rules: dict) -> Tuple[str, str]:
    thresholds = rules["thresholds"]
    total = production_score + marketing_score
    gap = abs(production_score - marketing_score)

    if total < thresholds["minimum_total_score"]:
        return "unknown", "low"

    if production_score >= thresholds["hybrid_min_both_scores"] and marketing_score >= thresholds["hybrid_min_both_scores"]:
        relative_gap = gap / max(production_score, marketing_score)
        if gap < thresholds["medium_confidence_gap"] or relative_gap <= thresholds.get("hybrid_relative_gap_ratio", 0):
            return "hybrid", "medium"

    if production_score >= marketing_score + thresholds["high_confidence_gap"]:
        return "web_production", "high"
    if marketing_score >= production_score + thresholds["high_confidence_gap"]:
        return "web_marketing", "high"
    if production_score >= marketing_score + thresholds["medium_confidence_gap"]:
        return "web_production", "medium"
    if marketing_score >= production_score + thresholds["medium_confidence_gap"]:
        return "web_marketing", "medium"
    return "hybrid", "low"


def detect_column(fieldnames: Sequence[str], explicit: Optional[str], candidates: Sequence[str]) -> str:
    if explicit:
        if explicit not in fieldnames:
            raise ValueError(f"Column not found: {explicit}")
        return explicit
    for candidate in candidates:
        if candidate in fieldnames:
            return candidate
    raise ValueError(f"Could not detect column. Tried: {', '.join(candidates)}")


def classify_site(url: str, rules: dict, cache_dir: Path, use_cache: bool, sleep_seconds: float) -> dict:
    start_url = normalize_url(url)
    if not start_url:
        return {
            "classification": "unknown",
            "confidence": "low",
            "production_score": 0,
            "marketing_score": 0,
            "production_keywords": "",
            "marketing_keywords": "",
            "source_pages": "",
            "fetch_status": "error:no_url",
        }

    html_text, status = fetch_url(start_url, rules, cache_dir, use_cache)
    if not html_text and start_url.startswith("https://"):
        fallback = "http://" + start_url[len("https://") :]
        html_text, status = fetch_url(fallback, rules, cache_dir, use_cache)
        if html_text:
            start_url = fallback
    if not html_text:
        return {
            "classification": "unknown",
            "confidence": "low",
            "production_score": 0,
            "marketing_score": 0,
            "production_keywords": "",
            "marketing_keywords": "",
            "source_pages": start_url,
            "fetch_status": status,
        }

    pages = [parse_html(start_url, html_text)]
    page_urls = choose_pages(start_url, pages[0], rules)
    for page_url in page_urls:
        if sleep_seconds:
            time.sleep(sleep_seconds)
        page_html, page_status = fetch_url(page_url, rules, cache_dir, use_cache)
        if page_html:
            pages.append(parse_html(page_url, page_html))

    production_score, production_terms = score_category(pages, rules["categories"]["web_production"], rules)
    marketing_score, marketing_terms = score_category(pages, rules["categories"]["web_marketing"], rules)
    classification, confidence = classify(production_score, marketing_score, rules)

    return {
        "classification": classification,
        "confidence": confidence,
        "production_score": production_score,
        "marketing_score": marketing_score,
        "production_keywords": " | ".join(production_terms),
        "marketing_keywords": " | ".join(marketing_terms),
        "source_pages": " | ".join(page.url for page in pages),
        "fetch_status": status,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Classify web company sites using scrape + rule scoring.")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument("--rules", default=str(DEFAULT_RULES), help="Rules JSON path")
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR), help="HTML cache directory")
    parser.add_argument("--company-column", help="Company column name. Auto-detected if omitted.")
    parser.add_argument("--url-column", help="URL column name. Auto-detected if omitted.")
    parser.add_argument("--limit", type=int, help="Only process first N rows")
    parser.add_argument("--sleep", type=float, default=0.25, help="Seconds to sleep between page fetches")
    parser.add_argument("--no-cache", action="store_true", help="Do not read from cache before fetching")
    args = parser.parse_args(argv)

    rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    input_path = Path(args.input)
    output_path = Path(args.output)
    cache_dir = Path(args.cache_dir)

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header")
        company_col = detect_column(reader.fieldnames, args.company_column, ["企業名", "company", "company_name", "Company"])
        url_col = detect_column(reader.fieldnames, args.url_column, ["URL", "url", "site_url", "website", "Webサイト"])
        rows = list(reader)

    if args.limit is not None:
        rows = rows[: args.limit]

    output_fields = list(rows[0].keys()) if rows else []
    additions = [
        "classification",
        "confidence",
        "production_score",
        "marketing_score",
        "production_keywords",
        "marketing_keywords",
        "source_pages",
        "fetch_status",
    ]
    for field in additions:
        if field not in output_fields:
            output_fields.append(field)

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            company = row.get(company_col, "")
            url = row.get(url_col, "")
            print(f"[{index}/{len(rows)}] {company} {url}", file=sys.stderr)
            result = classify_site(url, rules, cache_dir, not args.no_cache, args.sleep)
            row.update(result)
            writer.writerow(row)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
