import csv
import json
import re
from collections import Counter
from pathlib import Path

LABEL_OTHER = "\u696d\u7a2e\u9055\u3044"

FILES = [
    ("778_800", "webmarketing_A778_O800.csv", 778, 800),
    ("801_900", "webmarketing_A801_O900.csv", 801, 900),
    ("901_1000", "webmarketing_A901_O1000.csv", 901, 1000),
    ("1001_1076", "webmarketing_A1001_O1076.csv", 1001, 1076),
]

PRODUCTION_TERMS = [
    "\u30db\u30fc\u30e0\u30da\u30fc\u30b8\u5236\u4f5c",
    "\u30db\u30fc\u30e0\u30da\u30fc\u30b8\u4f5c\u6210",
    "\u30db\u30fc\u30e0\u30da\u30fc\u30b8\u306e\u5236\u4f5c",
    "Web\u5236\u4f5c",
    "WEB\u5236\u4f5c",
    "web\u5236\u4f5c",
    "Web\u30b5\u30a4\u30c8\u5236\u4f5c",
    "WEB\u30b5\u30a4\u30c8\u5236\u4f5c",
    "\u30b5\u30a4\u30c8\u5236\u4f5c",
    "\u30b5\u30a4\u30c8\u69cb\u7bc9",
    "\u30a6\u30a7\u30d6\u5236\u4f5c",
    "LP\u5236\u4f5c",
    "EC\u30b5\u30a4\u30c8",
    "WEB\u30c7\u30b6\u30a4\u30f3",
    "Web\u30c7\u30b6\u30a4\u30f3",
]

MARKETING_TERMS = [
    "\u30de\u30fc\u30b1\u30c6\u30a3\u30f3\u30b0",
    "SEO",
    "MEO",
    "\u5e83\u544a",
    "\u30ea\u30b9\u30c6\u30a3\u30f3\u30b0",
    "SNS",
    "\u96c6\u5ba2",
    "\u30d7\u30ed\u30e2\u30fc\u30b7\u30e7\u30f3",
    "\u30d6\u30e9\u30f3\u30c7\u30a3\u30f3\u30b0",
    "\u8ca9\u4fc3",
    "\u904b\u7528\u4ee3\u884c",
    "\u89e3\u6790",
    "\u30b3\u30f3\u30b5\u30eb\u30c6\u30a3\u30f3\u30b0",
]

THIRD_PARTY_TERMS = [
    "PRONI",
    "\u30a2\u30a4\u30df\u30c4",
    "\u30cb\u30e5\u30fc\u30b9",
    "\u6c42\u4eba",
    "\u63a1\u7528\u30b5\u30a4\u30c8",
    "\u5e97\u8217\u691c\u7d22",
    "\u9ad8\u6821",
    "GitHub",
    "\u516c\u5f0f\u30db\u30fc\u30e0\u30da\u30fc\u30b8",
    "\u88dc\u52a9\u91d1",
    "\u52a9\u6210\u91d1",
    "\u8cc7\u91d1\u8abf\u9054\u30ca\u30d3",
    "\u30a4\u30d9\u30f3\u30c8",
    "Doorkeeper",
    "dtn\u691c\u7d22",
    "\u502b\u7406\u6cd5\u4eba\u4f1a",
    "\u5c31\u6d3b",
    "\u8fb2\u697d\u91cc",
    "\u4e00\u89a7",
]

HARD_MISMATCH_TERMS = [
    "PRONI",
    "\u30a2\u30a4\u30df\u30c4",
    "\u30cb\u30e5\u30fc\u30b9",
    "PRTIMES",
    "Doorkeeper",
    "Jobsora",
    "dtn\u691c\u7d22",
    "GitHub",
    "\u516c\u5f0f\u30db\u30fc\u30e0\u30da\u30fc\u30b8",
    "\u516c\u5f0f\u5c31\u8077",
    "\u5c31\u6d3b",
    "\u8cc7\u91d1\u8abf\u9054\u30ca\u30d3",
    "\u502b\u7406\u6cd5\u4eba\u4f1a",
    "\u901a\u4fe1\u5236\u9ad8\u6821",
    "\u5e97\u8217\u691c\u7d22",
]

NON_TARGET_TERMS = [
    "\u901a\u4fe1\u5236\u9ad8\u6821",
    "\u4eba\u6750\u6d3e\u9063",
    "\u30b1\u30fc\u30d6\u30eb\u30c6\u30ec\u30d3",
    "\u5c31\u52b4\u7d99\u7d9a\u652f\u63f4",
    "\u91d1\u5c5e\u8cb7\u53d6",
    "\u6587\u5177",
    "\u753b\u6750",
    "\u9152\u985e",
    "\u846c\u5100",
    "\u30db\u30c6\u30eb",
    "\u30ec\u30b9\u30c8\u30e9\u30f3",
    "\u96fb\u5b50\u90e8\u54c1",
    "\u7406\u5316\u5b66",
    "\u4ecb\u8b77",
    "\u8fb2\u696d",
    "\u8fb2\u5c71\u6f01\u6751",
]


def normalize_name(value):
    value = (value or "").lower()
    for old in [
        "\u682a\u5f0f\u4f1a\u793e",
        "\u6709\u9650\u4f1a\u793e",
        "\u5408\u540c\u4f1a\u793e",
        "\u516c\u5f0f",
        "\u30b5\u30a4\u30c8",
        " ",
        "\u3000",
        "\u30fb",
        "\uff08",
        "\uff09",
        "(",
        ")",
        "\u3231",
        ".",
        ",",
        "\uff0c",
        "\u3002",
        "\uff5c",
        "|",
        "-",
    ]:
        value = value.replace(old, "")
    return value


def contains_any(text, terms):
    return any(term in text for term in terms)


def classify(record):
    title_meta = " ".join([record.get("title", ""), record.get("meta", "")])
    text = " ".join(
        [
            record.get("keywords", ""),
            record.get("title", ""),
            record.get("meta", ""),
            record.get("text", "")[:500],
        ]
    )
    name_key = normalize_name(record["name"])
    surface = normalize_name(title_meta[:700])
    name_seen = len(name_key) >= 4 and name_key in surface

    third_party = contains_any(title_meta, THIRD_PARTY_TERMS) and not name_seen
    non_target = contains_any(title_meta, NON_TARGET_TERMS)
    prod = contains_any(text, PRODUCTION_TERMS)
    mark = contains_any(text, MARKETING_TERMS)

    hard_mismatch = contains_any(title_meta, HARD_MISMATCH_TERMS) and not name_seen

    if hard_mismatch:
        label = LABEL_OTHER
    elif non_target and not (prod and mark):
        label = LABEL_OTHER
    elif prod and mark:
        label = "hybrid"
    elif mark:
        label = "web_marketing"
    elif prod:
        label = "web_production"
    else:
        label = LABEL_OTHER

    flag = ""
    if third_party:
        flag = "third_party_or_mismatch"
    elif not name_seen:
        flag = "name_not_seen"
    return label, flag


def main():
    probes = {
        (record["sheet_row"], record["name"]): record
        for record in json.loads(
            Path("site_probe_webmarketing_778_1076.json").read_text(encoding="utf-8")
        )
    }
    all_records = []
    outputs = {}
    for tag, csv_path, start, end in FILES:
        labels = []
        with open(csv_path, encoding="utf-8-sig", newline="") as handle:
            for sheet_row, row in enumerate(csv.reader(handle), start):
                key = (sheet_row, row[2] if len(row) > 2 else "")
                record = probes.get(key, {})
                if not record:
                    record = {
                        "sheet_row": sheet_row,
                        "name": row[2] if len(row) > 2 else "",
                        "url": row[4] if len(row) > 4 else "",
                        "keywords": row[12] if len(row) > 12 else "",
                    }
                label, flag = classify(record)
                record["label"] = label
                record["flag"] = flag
                labels.append(label)
                all_records.append(record)
        outputs[tag] = labels
        Path(f"column_O_webmarketing_{tag}.tsv").write_text(
            "\n".join(labels) + "\n", encoding="utf-8"
        )

    summary = {
        tag: dict(Counter(labels)) for tag, labels in outputs.items()
    }
    flagged = [
        {
            "sheet_row": r["sheet_row"],
            "name": r["name"],
            "url": r.get("url", ""),
            "label": r["label"],
            "flag": r["flag"],
            "title": r.get("title", "")[:140],
        }
        for r in all_records
        if r.get("flag") in {"third_party_or_mismatch", "name_not_seen"}
    ]
    Path("webmarketing_778_1076_classification_review.json").write_text(
        json.dumps({"summary": summary, "flagged": flagged}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("flagged", len(flagged))


if __name__ == "__main__":
    main()
