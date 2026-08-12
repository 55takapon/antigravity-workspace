import csv, json, sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
RUN = Path(__file__).parent
DIST = ROOT / ".agent/skills/simesapo-sales-skills-dist"
sys.path[:0] = [str(DIST / ".codex_pydeps"), str(DIST / "shared")]
from sheets_io import get_client

SHEET_ID = "1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ"
DATE = "2026-08-12"

def pad(row, n=16):
    return row + [""] * (n - len(row))

def domain(url):
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    host = (urlparse(url).hostname or "").lower().strip(".")
    return host[4:] if host.startswith("www.") else host

pref = list(csv.DictReader((RUN / "job30_prefiltered.data").open(encoding="utf-8-sig")))
aud = list(csv.DictReader((RUN / "job18_audited.data").open(encoding="utf-8-sig")))

manual = {
    "Ritz株式会社": ("送付対象", "https://ritz-inc.jp/contact/", "小規模組織でWebマーケティング・開業支援を受託し、店舗・医療・サービス業支援を明示"),
    "株式会社エイト": ("除外", "", "求人シグナルの公式サイトを取得できず、同名企業が多数あるため法人同一性と受託根拠を確定できない"),
    "株式会社TUKURO": ("除外", "", "公式サイト取得不能のため第三者向け受託内容と実在フォームを確定できない"),
    "株式会社ビジネスアシスト": ("除外", "", "地域店舗向けWeb・広告・SNS支援は確認できたが、実在するWeb問い合わせフォームを確認できない"),
    "株式会社オレンジゲート": ("除外", "https://www.orangegate.co.jp/contact/", "Googleビジネスプロフィール連携を既に自社提供しており、今回の外部GBP運用提案との補完余地が薄い"),
    "株式会社Giving First": ("除外", "https://g1st.co.jp/recruit/", "MEOを自社提供し、提携導線も同社Web制作を販売する代理店募集で当方への業務外注文脈と逆向き"),
}
for row in aud:
    if row["company_name"] in manual:
        decision, contact, reason = manual[row["company_name"]]
        row["classification"] = decision
        row["contact_url"] = contact
        row["contact_check"] = "manual_official_site_review"
        row["audit_reason"] = reason

send = [r for r in aud if r["classification"] == "送付対象"]
audit_ex = [r for r in aud if r["classification"] == "除外"]
existing = [r for r in pref if "既存または除外リスト一致" in r["prefilter_reason"]]
pre_ex = [r for r in pref if r["prefilter"] == "exclude" and "既存または除外リスト一致" not in r["prefilter_reason"]]

if (len(pref), len(existing), len(pre_ex), len(send), len(audit_ex)) != (30, 10, 2, 10, 8):
    raise SystemExit("STOP reconciliation " + repr((len(pref), len(existing), len(pre_ex), len(send), len(audit_ex))))

book = get_client(str(DIST / "shared/gcp_service_account.json")).open_by_key(SHEET_ID)
ws = book.worksheet("シート2")
exws = book.worksheet("除外リスト")
pws = book.worksheet("収集進捗管理")
sv = [pad(r) for r in ws.get("A1:P", value_render_option="FORMULA")]
ev = [pad(r) for r in exws.get("A1:P", value_render_option="FORMULA")]
first = next(i for i, r in enumerate(sv[1:], 2) if r[14].startswith("除外"))
if not all(r[14].startswith("除外") for r in sv[first - 1:]):
    raise SystemExit("STOP Sheet2 exclusion block")

live_domains = {domain(r[1]) for r in sv[1:] + ev[1:] if domain(r[1])}
duplicates = [r["company_name"] for r in send if domain(r["url"]) in live_domains]
if duplicates:
    raise SystemExit("STOP live duplicate " + json.dumps(duplicates, ensure_ascii=False))

with (RUN / "sheet2_before.data").open("w", encoding="utf-8-sig", newline="") as f:
    csv.writer(f).writerows(sv)
with (RUN / "exclusion_before.data").open("w", encoding="utf-8-sig", newline="") as f:
    csv.writer(f).writerows(ev)

def send_row(r):
    out = [""] * 16
    out[0], out[1], out[5] = r["company_name"], r["url"], r["contact_url"]
    out[12] = "Web・広告・SNS受託"
    out[14] = "送付対象｜A｜直近求人シグナル本監査"
    out[15] = f"【採用根拠】{r['audit_reason']}｜【窓口】実在フォーム確認済み：{r['contact_url']}｜【根拠URL】{r['url']}｜【監査日】{DATE}"
    return out

def exclusion_row(name, url, reason, contact="", check="事前機械判定"):
    out = [""] * 16
    out[0], out[1], out[5] = name, url, contact
    out[8], out[9], out[12] = "skip監査除外", reason, "直近求人シグナル本監査"
    out[14] = "除外｜直近求人シグナル本監査"
    out[15] = f"【除外根拠】{reason}｜【窓口確認】{check}｜【根拠URL】{url}｜【監査日】{DATE}"
    return out

ws.insert_rows([send_row(r) for r in send], row=first, value_input_option="RAW")
exclude_rows = [exclusion_row(r["company_name"], r["url"], r["prefilter_reason"]) for r in pre_ex]
exclude_rows += [exclusion_row(r["company_name"], r["url"], r["audit_reason"], r["contact_url"], r["contact_check"]) for r in audit_ex]
exws.append_rows(exclude_rows, value_input_option="RAW", table_range=f"A{len(ev)+1}:P")
pws.update(range_name="A88:F88", values=[["5", "NEXT-JOB-SIGNAL-001", "直近求人シグナル30社パイロット", "既存10／新規本監査20", "送付対象10・新規除外10（採用率33.3%）", "基準15社未達のため方式停止"]], value_input_option="RAW")
pws.update(range_name="A89:F89", values=[["進捗", "再計算完了", "純増874社", "8.74%", "有効基準9,115社", "残り9,126社"]], value_input_option="RAW")

sv2 = [pad(r) for r in ws.get("A1:P", value_render_option="FORMULA")]
ev2 = [pad(r) for r in exws.get("A1:P", value_render_option="FORMULA")]
first2 = next(i for i, r in enumerate(sv2[1:], 2) if r[14].startswith("除外"))
domains = [domain(r[1]) for r in sv2[1:] if domain(r[1])]
send_names = {r["company_name"] for r in send}
exclude_names = {r["company_name"] for r in pre_ex + audit_ex}
report = {
    "source_total": 30,
    "existing": 10,
    "send_written": 10,
    "exclude_written": 10,
    "reconciled": 30 == 10 + 10 + 10,
    "sheet2_before": len(sv),
    "sheet2_after": len(sv2),
    "exclusion_before": len(ev),
    "exclusion_after": len(ev2),
    "first_exclusion_row": first2,
    "exclusions_contiguous_bottom": all(r[14].startswith("除外") for r in sv2[first2 - 1:]),
    "sheet2_send_count": sum(r[14].startswith("送付対象") for r in sv2[1:]),
    "duplicate_domains_sheet2": len(domains) - len(set(domains)),
    "send_names_readback": sum(r[0] in send_names and r[14].startswith("送付対象") for r in sv2[1:]),
    "exclude_names_readback": sum(r[0] in exclude_names and r[14].startswith("除外｜直近求人") for r in ev2[1:]),
    "progress": pws.get("A88:F89"),
}
checks = (
    report["sheet2_after"] == len(sv) + 10
    and report["exclusion_after"] == len(ev) + 10
    and report["first_exclusion_row"] == first + 10
    and report["exclusions_contiguous_bottom"]
    and report["sheet2_send_count"] == 874
    and report["duplicate_domains_sheet2"] == 0
    and report["send_names_readback"] == 10
    and report["exclude_names_readback"] == 10
)
if not checks:
    raise SystemExit("STOP verification " + json.dumps(report, ensure_ascii=False))
(RUN / "publish_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
