from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
OUT = ROOT / ".codex" / "simesapo" / "runs" / "20260812_sheet2_sort_exclusions" / "rescued_inventory_reconciliation.json"
CREDS = DIST / "shared" / "gcp_service_account.json"
SHEET_ID = "1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ"
sys.path.insert(0, str(DIST / ".codex_pydeps"))
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client  # noqa: E402


def nt(v):
    return re.sub(r"[\s\u3000]+", "", unicodedata.normalize("NFKC", v or "").strip().lower())


def nc(v):
    s = nt(v)
    s = re.sub(r"^(株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人|医療法人|社会福祉法人|学校法人)", "", s)
    s = re.sub(r"(株式会社|有限会社|合同会社|合資会社|合名会社)$", "", s)
    return re.sub(r"[^0-9a-z\u3040-\u30ff\u3400-\u9fff]+", "", s)


def nd(v):
    s = unicodedata.normalize("NFKC", v or "").strip()
    if not s:
        return ""
    if "://" not in s:
        s = "https://" + s
    host = (urlparse(s).hostname or "").lower().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def np(v):
    d = re.sub(r"\D", "", unicodedata.normalize("NFKC", v or ""))
    if d.startswith("81") and len(d) >= 10:
        d = "0" + d[2:]
    return d if len(d) >= 9 else ""


def records(ws):
    vals = ws.get_all_values()
    if not vals:
        return []
    h = [nt(x) for x in vals[0]]
    def ci(names):
        for name in names:
            if nt(name) in h:
                return h.index(nt(name))
        return None
    ix = {
        "company": ci(["company_name", "会社名"]), "url": ci(["url", "公式URL"]),
        "phone": ci(["phone", "電話番号"]), "status": ci(["status", "ステータス"]),
        "class": ci(["区分", "classification", "分類"]),
    }
    out = []
    for rn, row in enumerate(vals[1:], 2):
        if not any(x.strip() for x in row):
            continue
        def c(k):
            i = ix[k]
            return row[i].strip() if i is not None and i < len(row) else ""
        out.append({"row": rn, "company": c("company"), "company_n": nc(c("company")), "url": c("url"),
                    "domain": nd(c("url")), "phone": np(c("phone")), "status": c("status"), "class": c("class")})
    return out


book = get_client(str(CREDS)).open_by_key(SHEET_ID)
tabs = {ws.title: records(ws) for ws in book.worksheets()}
operational = ["シート1", "Webマーケ", "SNS運用", "251127作成", "251222作成", "Web幹事"]
fit_classes = {
    "シート1": {"Web制作会社", "周辺業種_Web付随", "Webマーケ・SNS運用"},
    "Webマーケ": {"Webマーケ・広告運用", "Web制作会社", "周辺業種_Web付随"},
    "SNS運用": {"SNS運用・SNS広告"},
}
historical = {"251127作成", "251222作成", "Web幹事"}
hard_status = {"送信不可", "skip営業NG", "営業NG業種違い", "営業不可", "excluded"}
ex = tabs["除外リスト"]
exd = {r["domain"] for r in ex if r["domain"]}
exc = {r["company_n"] for r in ex if r["company_n"]}
exp = {r["phone"] for r in ex if r["phone"]}

strategic = []
for tab in operational:
    for r in tabs[tab]:
        excluded = (r["domain"] and r["domain"] in exd) or (r["company_n"] and r["company_n"] in exc) or (r["phone"] and r["phone"] in exp)
        fit = (tab in fit_classes and r["class"] in fit_classes[tab]) or tab in historical
        if fit and not excluded and r["status"] not in hard_status:
            strategic.append(r)

sd = {r["domain"] for r in strategic if r["domain"]}
sc = {r["company_n"] for r in strategic if r["company_n"]}
sp = {r["phone"] for r in strategic if r["phone"]}
rescued = [r for r in tabs["シート2"] if r["class"].startswith("送付対象｜")]
overlap_operational = [r for r in rescued if (r["domain"] and r["domain"] in sd) or (r["company_n"] and r["company_n"] in sc) or (r["phone"] and r["phone"] in sp)]
overlap_exclusion = [r for r in rescued if (r["domain"] and r["domain"] in exd) or (r["company_n"] and r["company_n"] in exc) or (r["phone"] and r["phone"] in exp)]
net = [r for r in rescued if r not in overlap_operational and r not in overlap_exclusion]
net_domains = {r["domain"] for r in net if r["domain"]}

result = {
    "operational_strategic_rows": len(strategic),
    "operational_strategic_unique_domains": len(sd),
    "rescued_send_rows": len(rescued),
    "rescued_overlap_operational_any_key": len(overlap_operational),
    "rescued_overlap_exclusion_any_key": len(overlap_exclusion),
    "rescued_net_rows": len(net),
    "rescued_net_unique_domains": len(net_domains),
    "combined_active_unique_domains": len(sd | net_domains),
    "additional_10000_progress_count": len(net_domains),
    "additional_10000_progress_rate": len(net_domains) / 10000,
    "additional_10000_remaining": 10000 - len(net_domains),
    "overlap_operational_sample": [{"row": r["row"], "company": r["company"], "url": r["url"]} for r in overlap_operational[:20]],
    "overlap_exclusion_sample": [{"row": r["row"], "company": r["company"], "url": r["url"]} for r in overlap_exclusion[:20]],
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
