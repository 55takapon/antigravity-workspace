from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).parent

CONTACTS = [
    "https://form.run/@visca-hp", "https://www.dental-hp.net/info/contact.html",
    "https://z-it.jp/contact", "https://www.narcohm.co.jp/hp/inquiry/",
    "https://dental-web-atelier.com/#contact", "https://www.shirube365.com/contact",
    "https://clinic-first.com/contact/", "https://www.global-unity.jp/contact/",
    "https://www.hospital-hp.com/contact", "https://www.at-office.co.jp/contact.html",
    "https://shika-promotion.com/contact/", "https://www.iplus-web.co.jp/contact",
    "https://www.method-innovation.co.jp/contact/", "", "https://www.aisis.ne.jp/#contact",
    "https://docs.google.com/forms/d/e/1FAIpQLSdj9E46TOU2iveog0X2x9KBmohV0GC4v5CnpnrA_CtFPO8zlg/viewform",
    "https://homepage-tokyo.jp/inquiry/", "https://www.hospital-web.net/asking/index.html",
    "https://www.medicalwebstage.jp/contact/", "https://mc-net.jp/contact/",
    "https://www.trancefer-co.info/inq/", "", "https://hplus.jp/contact/",
    "https://www.medical-parks.com/contact/dairiten.html", "https://www.ortho-advance.com/contact.html",
    "https://www.nijimo.jp/company/contact/", "https://www.miraizu-inc.jp/contact/",
    "https://m-hands.net/contact/", "https://www.dental-smart.net/contact/",
    "https://medicalskip.com/contact/", "https://www.dam.co.jp/contact/",
    "https://clinicl.com/inquiry/", "https://www.colbo.co.jp/contact/",
    "https://hypex.jp/contact", "", "", "", "", "https://luminage.co.jp/contact/",
    "https://tahlab.net/contact/", "https://campaign.reacdesign.com/#asked",
    "https://adesign.jp/contact/index.html", "https://bau-marketing.jp/contact",
    "https://www.honepage.com/contact/index.html",
]

rows = list(csv.DictReader((HERE / "full_candidates_precontact.csv").open(encoding="utf-8-sig", newline="")))
assert len(rows) == len(CONTACTS), (len(rows), len(CONTACTS))
for row, contact in zip(rows, CONTACTS):
    row["contact_url"] = contact

with (HERE / "full_candidates_with_contacts.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(f"rows={len(rows)} contact={sum(bool(r['contact_url']) for r in rows)}")
