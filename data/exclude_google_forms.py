import argparse
import csv
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse


GOOGLE_FORM = re.compile(r"(?:forms\.gle|docs\.google\.com/forms)", re.I)


def read(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader), list(reader)


def norm_name(value):
    value = unicodedata.normalize("NFKC", value or "").lower()
    value = re.sub(r"株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人", "", value)
    return re.sub(r"[^0-9a-z一-龠々ぁ-んァ-ヶ]", "", value)


def domain(value):
    try:
        return urlparse(value if "://" in value else "https://" + value).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def phone(value):
    return re.sub(r"\D", "", value or "")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sns_csv")
    parser.add_argument("exclusion_csv")
    parser.add_argument("sns_output")
    parser.add_argument("exclusion_output")
    args = parser.parse_args()
    sns_header, sns_rows = read(args.sns_csv)
    exclusion_header, exclusion_rows = read(args.exclusion_csv)
    names = {norm_name(row[0]) for row in exclusion_rows if norm_name(row[0])}
    domains = {domain(row[1]) for row in exclusion_rows if domain(row[1])}
    phones = {phone(row[3]) for row in exclusion_rows if phone(row[3])}
    kept, removed, appended = [], [], 0
    for row in sns_rows:
        if not GOOGLE_FORM.search(row[5]):
            kept.append(row)
            continue
        removed.append(row)
        n, d, p = norm_name(row[0]), domain(row[1]), phone(row[3])
        if (n and n in names) or (d and d in domains) or (p and p in phones):
            continue
        item = row[:13]
        item[5] = ""
        item[9] = "google_form_not_supported_by_policy"
        exclusion_rows.append(item)
        if n:
            names.add(n)
        if d:
            domains.add(d)
        if p:
            phones.add(p)
        appended += 1
    for path, header, rows in ((args.sns_output, sns_header, kept), (args.exclusion_output, exclusion_header, exclusion_rows)):
        with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle); writer.writerow(header); writer.writerows(rows)
    print(f"sns_before={len(sns_rows)} google_forms={len(removed)} sns_after={len(kept)} exclusion_appended={appended} exclusion_after={len(exclusion_rows)}")


if __name__ == "__main__":
    main()
