import csv
from collections import Counter, defaultdict
from pathlib import Path

CSV_PATH = Path(__file__).with_name("sent_tabs_enterprise_audit_20260802.csv")
FINAL_PATH = Path(r"C:\Users\hangy\.gemini\antigravity\local_data\simesapo\audits\sent_tabs_enterprise_audit_final_20260802.csv")

# Candidate site/domain confirmed as the listed company or controlled major-group company.
EXCLUDE = {
    "送信済み251127|561", "送信済み251127|647", "送信済み251127|652", "送信済み251127|654",
    "送信済み251222|174", "送信済み251222|643",
    "Web幹事済み|104", "Web幹事済み|264", "Web幹事済み|275", "Web幹事済み|285",
    "Web幹事済み|468", "Web幹事済み|618", "Web幹事済み|645", "Web幹事済み|732",
    "Web幹事済み|787", "Web幹事済み|983", "Web幹事済み|1252", "Web幹事済み|1256",
    "Web幹事済み|1497", "Web幹事済み|2972", "Web幹事済み|3078",
    "Web幹事済み|3126", "Web幹事済み|3200", "Web幹事済み|3268", "Web幹事済み|3287",
    "Web幹事済み|3419", "Web幹事済み|3426", "Web幹事済み|3542", "Web幹事済み|3577",
    "Web幹事済み|3663", "Web幹事済み|3683", "Web幹事済み|3716", "Web幹事済み|3742",
    "Web幹事済み|3749", "Web幹事済み|3929", "Web幹事済み|3964",
}

# Name/keyword collision; candidate domain is a different legal entity from the JPX/group match.
ALLOW = {
    "送信済み251127|56", "送信済み251127|118", "送信済み251127|347", "送信済み251127|445",
    "送信済み251127|790", "送信済み251222|19", "送信済み251222|52", "送信済み251222|819",
    "送信済み251222|989", "Web幹事済み|63", "Web幹事済み|193", "Web幹事済み|393",
    "Web幹事済み|506", "Web幹事済み|675", "Web幹事済み|743", "Web幹事済み|798",
    "Web幹事済み|1153", "Web幹事済み|1336", "Web幹事済み|1350", "Web幹事済み|1362",
    "Web幹事済み|1394", "Web幹事済み|1543", "Web幹事済み|1629", "Web幹事済み|1681",
    "Web幹事済み|1929", "Web幹事済み|1967", "Web幹事済み|2124", "Web幹事済み|2707", "Web幹事済み|2785",
    "Web幹事済み|2957", "Web幹事済み|3019", "Web幹事済み|3029", "Web幹事済み|3128",
    "Web幹事済み|3262", "Web幹事済み|3552", "Web幹事済み|3854", "Web幹事済み|3969", "Web幹事済み|4184",
    "Web幹事済み|4265",
}

rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig", newline="")))
pending = []
for row in rows:
    if not row["classification"].startswith("review_"):
        continue
    key = f'{row["worksheet"]}|{row["row_number"]}'
    if key in EXCLUDE:
        row["classification"] = "exclude_confirmed_enterprise"
        row["reason"] = "候補URLの公式情報・公式ドメイン照合により、上場会社または大手グループ会社との同一性を確認。"
    elif key in ALLOW:
        row["classification"] = "allow_confirmed_same_name_other_entity"
        row["reason"] = "名称・判定語は一致するが、候補URLは上場会社または大手グループ会社とは別法人。"
    else:
        pending.append(key)

if pending:
    raise SystemExit(f"unresolved={pending}")

FINAL_PATH.parent.mkdir(parents=True, exist_ok=True)
with FINAL_PATH.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

totals = Counter(r["classification"] for r in rows)
by_tab = defaultdict(Counter)
for r in rows:
    by_tab[r["worksheet"]][r["classification"]] += 1
print("TOTAL", dict(totals))
for tab, counts in by_tab.items():
    print(tab, dict(counts), "flagged", sum(counts.values()))
