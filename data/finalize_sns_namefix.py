import argparse
import csv
import html
import re
from pathlib import Path
from urllib.parse import urlparse


TRUSTED_SOURCES = {"existing_confirmed", "labeled"}
LEGAL = re.compile(r"株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人")


def norm_name(value: str) -> str:
    value = LEGAL.sub("", value.lower())
    return re.sub(r"[^0-9a-z一-龠々ぁ-んァ-ヶ]", "", value)


def norm_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def domain(value: str) -> str:
    try:
        parsed = urlparse(value if "://" in value else "https://" + value)
        return parsed.netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def clean_existing(value: str) -> str:
    value = html.unescape(value or "").replace("\u200b", "").strip()
    value = re.sub(r"^(?:社名(?:（商号）)?|会社名|商号)\s*[：:]\s*", "", value)
    # Remove only clearly appended readings, English names, or descriptions.
    value = re.split(r"[（(【]|[～~]|(?:英語|英文)表記", value, maxsplit=1)[0]
    return value.strip(" ,.:：;；-｜|")


def clean_labeled(value: str) -> str:
    value = html.unescape(value or "").replace("\u200b", "").strip()
    value = re.split(r"(?:英語|英文)(?:表記|社名)|[（(【]", value, maxsplit=1)[0]
    return value.strip(" ,.:：;；-｜|")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("main_csv")
    parser.add_argument("removed_csv")
    args = parser.parse_args()

    with Path(args.input_csv).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = list(reader)

    base_header = header[1:17]
    extra_header = header[17:]
    kept, removed = [], []
    seen_domains, seen_names, seen_phones = set(), set(), set()

    for row in rows:
        physical_row = row[0]
        source, state = row[18], row[20]
        reason = ""
        if state == "skip":
            reason = "blank_contact_url"
        elif state != "confirmed":
            reason = row[21] or "official_name_unconfirmed"
        elif source not in TRUSTED_SOURCES:
            reason = f"untrusted_name_source:{source}"

        if not reason:
            resolved = clean_existing(row[1]) if source == "existing_confirmed" else clean_labeled(row[17])
            d = domain(row[2])
            n = norm_name(resolved)
            p = norm_phone(row[4])
            duplicate_by = []
            if d and d in seen_domains:
                duplicate_by.append("domain")
            if n and n in seen_names:
                duplicate_by.append("company_name")
            if p and p in seen_phones:
                duplicate_by.append("phone")
            if duplicate_by:
                reason = "duplicate:" + "+".join(duplicate_by)
            else:
                row[1] = resolved
                kept.append(row[1:17])
                if d:
                    seen_domains.add(d)
                if n:
                    seen_names.add(n)
                if p:
                    seen_phones.add(p)

        if reason:
            removed.append([physical_row, reason, *row[1:17], *row[17:]])

    with Path(args.main_csv).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(base_header)
        writer.writerows(kept)
    with Path(args.removed_csv).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["_row", "removal_reason", *base_header, *extra_header])
        writer.writerows(removed)

    print(f"main={len(kept)} removed={len(removed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
