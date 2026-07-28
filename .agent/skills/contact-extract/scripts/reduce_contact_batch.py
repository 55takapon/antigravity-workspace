import argparse
import json
import re
from pathlib import Path


KEYWORDS = re.compile(
    r"contact|inquiry|toiawase|otoiawase|mail|form|apply|相談|問合|問い合|お問い合わせ|お問合せ|見積|資料請求|依頼",
    re.IGNORECASE,
)


def score_link(link: dict) -> int:
    value = " ".join(str(link.get(k) or "") for k in ("href", "text", "alt_title"))
    score = 0
    if KEYWORDS.search(value):
        score += 10
    href = str(link.get("href") or "").lower()
    if href.startswith("mailto:"):
        score += 8
    if href.startswith("#"):
        score -= 2
    if href.startswith("tel:"):
        score -= 8
    return score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dst")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--max-links", type=int, default=12)
    args = parser.parse_args()

    pages = json.loads(Path(args.src).read_text(encoding="utf-8"))
    selected = pages[args.start : args.start + args.count]
    reduced = []
    for page in selected:
        links = page.get("links") or []
        ranked = sorted(links, key=score_link, reverse=True)
        kept = [link for link in ranked if score_link(link) > 0][: args.max_links]
        if not kept:
            kept = ranked[: min(3, len(ranked))]
        reduced.append(
            {
                "idx": page.get("idx"),
                "_row": page.get("_row"),
                "base_url": page.get("base_url"),
                "links": kept,
            }
        )

    Path(args.dst).write_text(json.dumps(reduced, ensure_ascii=False), encoding="utf-8")
    print(f"[done] reduced {len(reduced)} pages -> {args.dst}")


if __name__ == "__main__":
    main()
