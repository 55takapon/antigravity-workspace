from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "qualified.csv"
OUTPUT = Path(r"C:\Users\hangy\.gemini\antigravity\local_data\simesapo\runs\20260802_phase0_growth\hotel_candidate_pool.csv")
MASTER = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\custmize\enterprise_filter")

HEADERS = [
    "company_name", "url", "address", "phone", "maps_url", "contact_url",
    "message", "sent_at", "status", "error_reason", "screenshot_path",
    "provider_used", "提案区分", "H1", "区分", "検出ワード",
]

REPAIRS = {
    "https://www.sanwasystem.com/": "三和システム株式会社",
    "https://checkinn.jp/": "Check Inn株式会社",
    "https://www.489ban.net/": "株式会社キャディッシュ",
    "https://tabiii.co.jp/": "株式会社Tabiii",
    "https://www.sevenspirits.co.jp/": "株式会社SEVEN SPIRITS",
}
REMOVE = {"https://tripla.io/"}

MANUAL = [
    ("株式会社エアホスト", "https://airhost.jp/", "https://airhost.jp/en/contact-us", "宿泊施設向けPMS・運用代行"),
    ("株式会社アクティバリューズ", "https://talkappi.com/", "https://talkappi.com/contact/", "宿泊施設向け顧客体験プラットフォーム"),
    ("xxx株式会社", "https://www.hotelsmart.jp/", "https://www.hotelsmart.jp/contact/", "ホテル・旅館向けPMS・セルフチェックイン"),
    ("株式会社ホテル旅館経営研究所", "https://hrcc.jp/", "https://hrcc.jp/contact/", "ホテル・旅館の経営・運営支援"),
    ("株式会社PlanAct", "https://planact.co.jp/", "https://planact.co.jp/contact/", "ホテル・旅館の企画・運営支援"),
    ("株式会社ホテル結マネージメント", "https://h-y-m-operation.studio.site/", "https://h-y-m-operation.studio.site/", "ホテル・旅館の運営受託"),
    ("株式会社CORE", "https://corecompany.jp/", "https://corecompany.jp/#contact", "宿泊施設の運営・企画支援"),
    ("株式会社MooN", "https://mo-on.jp/", "https://mo-on.jp/#contact", "民泊・宿泊施設の運営代行"),
    ("株式会社ReFlow", "https://es-sense.jp/", "https://es-sense.jp/#contact", "ホテル・民泊のAI運営支援"),
    ("株式会社NEXSIA", "https://www.nexsia.co.jp/", "https://www.nexsia.co.jp/contact/", "民泊運営代行・清掃支援"),
    ("株式会社サンエル", "https://sunl.jp/", "https://sunl.jp/contact/", "ホテル清掃管理DX支援"),
    ("株式会社Hosty", "https://lp.ai-check-in.com/", "https://lp.ai-check-in.com/#contact", "宿泊施設向けAIチェックイン"),
    ("株式会社OMOTENASHI", "https://www.omotenashi.co.jp/", "https://www.omotenashi.co.jp/contact/", "宿泊施設の管理・運営支援"),
    ("株式会社土樹和", "https://ryokan.tokiwa1090.com/", "https://ryokan.tokiwa1090.com/#contact", "旅館・ホテルの改修・再生支援"),
    ("株式会社フォーセット", "https://hoteza.jp/", "https://hoteza.jp/#contact", "ホテル向け情報システム"),
    ("株式会社クリップサイト", "https://www.clipsite.co.jp/", "https://www.clipsite.co.jp/inquiry/contact/", "ホテル向けPMS・業務システム"),
    ("aipass株式会社", "https://aipass.jp/", "https://aipass.jp/contact/form/", "宿泊施設向けスマート運営支援"),
    ("株式会社タップ", "https://www.tap-ic.co.jp/", "https://www.tap-ic.co.jp/contact/", "ホテル・旅館向けITソリューション"),
    ("株式会社宿楽", "https://www.yadoraku.co.jp/", "https://www.yadoraku.co.jp/contact/", "ホテル・旅館のWeb集客・経営支援"),
    ("株式会社宿力", "https://yado-riki.com/", "https://yado-riki.com/contact/", "旅館・ホテルのWeb集客・経営支援"),
    ("株式会社コレリーアンドアトラクト", "https://www.collely-at.com/", "https://www.collely-at.com/contact/", "ホテル・旅館専門デジタルマーケティング"),
    ("株式会社宿研", "https://www.yadoken.net/", "https://www.yadoken.net/contact", "ホテル・旅館専門の集客コンサルティング"),
    ("株式会社SQUEEZE", "https://squeeze-inc.co.jp/", "https://squeeze-inc.co.jp/contact/", "ホテル運営・宿泊DX支援"),
    ("株式会社ホテルサポート", "https://www.hotel-support.co.jp/", "https://www.hotel-support.co.jp/contact/", "ホテル運営コンサルティング"),
]


def norm(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or "").lower())


def company_key(value: str) -> str:
    return re.sub(r"株式会社|有限会社|合同会社|合資会社|合名会社|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］:-]", "", norm(value))


def domain_key(value: str) -> str:
    host = urlparse(value if "://" in (value or "") else "https://" + (value or "")).hostname or ""
    return re.sub(r"^www\.", "", host.lower())


def load_rows(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))


def blank_row(company: str, url: str, contact: str, evidence: str) -> dict:
    row = {h: "" for h in HEADERS}
    row.update({
        "company_name": company,
        "url": url,
        "contact_url": contact,
        "区分": "S｜業界特化Web制作",
        "検出ワード": f"旅館・ホテル・観光特化支援：{evidence}",
    })
    return row


rows: list[dict] = []
for raw in load_rows(SOURCE):
    url = raw.get("url", "")
    if url in REMOVE:
        continue
    row = {h: raw.get(h, "") for h in HEADERS}
    if url in REPAIRS:
        row["company_name"] = REPAIRS[url]
    rows.append(row)

for company, url, contact, evidence in MANUAL:
    rows.append(blank_row(company, url, contact, evidence))

confirmed = load_rows(MASTER / "confirmed_enterprise_exclusions.csv")
allow = load_rows(MASTER / "enterprise_false_positive_allowlist.csv")
jpx = load_rows(MASTER / "jpx_listed_companies_20260630.csv")
groups = load_rows(MASTER / "major_group_rules.csv")
confirmed_names = {company_key(r.get("company_name", "")) for r in confirmed}
confirmed_domains = {domain_key(r.get("url", "") or r.get("domain", "")) for r in confirmed}
allow_pairs = {(company_key(r.get("company_name", "")), domain_key(r.get("url", "") or r.get("domain", ""))) for r in allow}
jpx_names = {company_key(r.get("company_name", "") or r.get("name", "") or r.get("銘柄名", "")) for r in jpx}
contains = [norm(r.get("match_value", "") or r.get("keyword", "") or r.get("判定語", "")) for r in groups]

kept: list[dict] = []
removed: list[tuple[str, str]] = []
seen_names: set[str] = set()
seen_domains: set[str] = set()
for row in rows:
    ck, dk = company_key(row["company_name"]), domain_key(row["url"])
    pair = (ck, dk)
    reason = ""
    if not ck or not dk or not row["contact_url"]:
        reason = "missing_required"
    elif ck in seen_names or dk in seen_domains:
        reason = "pool_duplicate"
    elif pair not in allow_pairs and (ck in confirmed_names or dk in confirmed_domains):
        reason = "confirmed_enterprise"
    elif pair not in allow_pairs and ck in jpx_names:
        reason = "jpx_name_review"
    elif pair not in allow_pairs and any(k and k in norm(row["company_name"]) for k in contains):
        reason = "major_group_review"
    if reason:
        removed.append((row["company_name"], reason))
        continue
    seen_names.add(ck)
    seen_domains.add(dk)
    kept.append(row)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerows(kept)

print({"source": len(rows), "kept": len(kept), "removed": removed, "output": str(OUTPUT)})
