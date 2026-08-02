import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse


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
    parser.add_argument("source_csv")
    parser.add_argument("resolved_csv")
    parser.add_argument("browser_csv")
    parser.add_argument("exclusion_csv")
    parser.add_argument("out_dir")
    args = parser.parse_args()

    source_header, source_rows = read(args.source_csv)
    with Path(args.resolved_csv).open(encoding="utf-8-sig", newline="") as handle:
        resolved = {row["_row"]: row for row in csv.DictReader(handle)}
    with Path(args.browser_csv).open(encoding="utf-8-sig", newline="") as handle:
        browser = {row["_row"]: row for row in csv.DictReader(handle)}
    exclusion_header, exclusion_rows = read(args.exclusion_csv)
    exclusion_values = [row[1:14] for row in exclusion_rows]
    exclusion_keys = (
        {norm_name(row[1]) for row in exclusion_rows if norm_name(row[1])},
        {domain(row[2]) for row in exclusion_rows if domain(row[2])},
        {phone(row[4]) for row in exclusion_rows if phone(row[4])},
    )

    active, audit = [], []
    appended_exclusions = 0
    for row in source_rows:
        physical, base = row[0], row[1:17]
        primary = resolved[physical]
        final_url, state, evidence, reason = "", "", "", ""
        if physical == "149":
            state, reason = "excluded", "official_company_domain_mismatch"
        elif primary["contact_state"] == "valid":
            final_url, state, evidence = primary["resolved_contact_url"], "valid", primary["contact_evidence"]
        else:
            secondary = browser.get(physical, {})
            if secondary.get("browser_state") == "valid":
                final_url, state, evidence = secondary["browser_contact_url"], "valid", secondary["browser_evidence"]
            else:
                state, reason = "excluded", "general_contact_form_unconfirmed"

        if state == "valid":
            base[5] = final_url
            active.append(base)
            audit.append([physical, base[0], base[1], row[6], final_url, state, evidence])
            continue

        audit.append([physical, base[0], base[1], row[6], "", state, reason])
        n, d, p = norm_name(base[0]), domain(base[1]), phone(base[3])
        if (n and n in exclusion_keys[0]) or (d and d in exclusion_keys[1]) or (p and p in exclusion_keys[2]):
            continue
        excluded = base[:13]
        excluded[5] = ""
        excluded[9] = reason
        exclusion_values.append(excluded)
        if n:
            exclusion_keys[0].add(n)
        if d:
            exclusion_keys[1].add(d)
        if p:
            exclusion_keys[2].add(p)
        appended_exclusions += 1

    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    with (out / "sns_contact_verified.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(source_header[1:17]); writer.writerows(active)
    with (out / "exclusion_final.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(exclusion_header[1:14]); writer.writerows(exclusion_values)
    with (out / "contact_form_audit.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["_row", "company_name", "url", "old_contact_url", "final_contact_url", "state", "evidence_or_reason"]); writer.writerows(audit)
    summary = {"source": len(source_rows), "active_verified": len(active), "removed": len(source_rows) - len(active), "exclusion_appended": appended_exclusions, "exclusion_final": len(exclusion_values)}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
