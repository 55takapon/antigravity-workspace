import csv
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
INPUTS = [
    ROOT / "data" / "maps_marketing_wave1.json",
    ROOT / "data" / "maps_marketing_wave2.json",
    ROOT / "data" / "maps_marketing_wave3.json",
    ROOT / "data" / "maps_marketing_wave4.json",
]
OUTPUT = ROOT / "data" / "maps_marketing_candidates_20260731.csv"

BLOCKED_HOSTS = {
    "instagram.com",
    "facebook.com",
    "x.com",
    "twitter.com",
    "line.me",
    "lin.ee",
    "youtube.com",
    "youtu.be",
    "ameblo.jp",
    "note.com",
    "sites.google.com",
    "wixsite.com",
    "jimdosite.com",
    "peraichi.com",
    "lit.link",
    "linktr.ee",
}
PHONE = re.compile(r"(?<!\d)(0\d{1,4}-\d{1,4}-\d{3,4})(?!\d)")


def host_of(url):
    try:
        return urlsplit(url).hostname.lower().removeprefix("www.")
    except (AttributeError, ValueError):
        return ""


def clean_url(url):
    try:
        parts = urlsplit(url)
    except ValueError:
        return ""
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        return ""
    kept_query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    return urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path or "/",
        urlencode(kept_query),
        "",
    ))


def blocked(host):
    return any(host == value or host.endswith(f".{value}") for value in BLOCKED_HOSTS)


def normalize_name(value):
    name = re.sub(r"\s+", " ", value or "").strip()
    name = name.replace("（株）", "株式会社").replace("(株)", "株式会社")
    name = name.replace("（有）", "有限会社").replace("(有)", "有限会社")
    return name


def address_from_lines(area, lines):
    for line in lines:
        if " · " not in line:
            continue
        parts = [part.strip(" ·") for part in line.split(" · ") if part.strip(" ·")]
        for part in parts[1:]:
            if re.search(r"(?:\d|丁目|番地|番|号)", part) and not re.search(
                r"(営業|終了|開始|時間|クチコミ|つ星)", part
            ):
                return f"{area} {part}".strip()
    return ""


def main():
    seen = set()
    rows = []
    stats = {"raw": 0, "no_url": 0, "blocked": 0, "duplicate": 0, "kept": 0}
    for path in INPUTS:
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data:
            stats["raw"] += 1
            url = clean_url(item.get("url", ""))
            host = host_of(url)
            if not host:
                stats["no_url"] += 1
                continue
            if blocked(host):
                stats["blocked"] += 1
                continue
            if host in seen:
                stats["duplicate"] += 1
                continue
            seen.add(host)
            lines = item.get("raw_lines", [])
            address = address_from_lines(item.get("area", ""), lines)
            phone = ""
            for line in lines:
                match = PHONE.search(line)
                if match:
                    phone = match.group(1)
                    break
            rows.append({
                "company_name": normalize_name(item.get("company_name", "")),
                "url": url,
                "address": address,
                "phone": phone,
                "maps_url": item.get("maps_url", ""),
                "area_hint": item.get("area", ""),
                "query": item.get("query", ""),
            })
    stats["kept"] = len(rows)

    fields = ["company_name", "url", "address", "phone", "maps_url", "area_hint", "query"]
    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(stats, ensure_ascii=False))
    print(f"output={OUTPUT}")


if __name__ == "__main__":
    main()
