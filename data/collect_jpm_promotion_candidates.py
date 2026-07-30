import csv

from collect_jaaa_candidates import candidate_pages, fetch, find_address, find_phone


OUTPUT_PATH = "data/main_jpm_promotion_candidates_raw.csv"
CANDIDATES = [
    ("株式会社アクセスプログレス", "https://www.access-t.co.jp/pg/"),
    ("株式会社イーエムオー", "https://emo-sp.com/"),
    ("株式会社ADKクリエイティブ・ワン", "https://www.adkco.jp/"),
    ("株式会社エキスプレス社", "http://www.express-net.co.jp/"),
    ("株式会社OSKプランニング", "https://osk-planning.co.jp/"),
    ("株式会社Qoil", "https://www.qoil.co.jp/"),
    ("株式会社広研", "http://www.kouken.co.jp/"),
    ("株式会社コムズ・ファースト", "http://www.com-first.jp/"),
    ("株式会社コースト", "http://www.coast.ne.jp/"),
    ("株式会社三水社", "http://www.co-sansuisha.jp/"),
    ("株式会社スコープ・インターナショナル", "http://www.scope-int.co.jp/"),
    ("株式会社スピン", "http://www.spin-inc.co.jp/"),
    ("株式会社TMC", "http://www.tmc-network.co.jp/"),
    ("株式会社テー・オー・ダブリュー", "https://www.tow.co.jp/"),
    ("株式会社東具", "http://www.togu.co.jp/"),
    ("株式会社DOBIN", "https://www.sumgroup.co.jp/"),
    ("株式会社ノムラメディアス", "https://www.nomura-medias.co.jp/"),
    ("株式会社ヒロモリ", "http://www.hiromori.co.jp/"),
    ("PXC株式会社", "https://pxc.co.jp/"),
    ("株式会社フロンティアインターナショナル", "http://www.frontier-i.co.jp/"),
    ("株式会社八木クリエイティブ", "http://www.yagi-cr.co.jp/"),
    ("株式会社読広クロスコム", "http://www.yomiko-crosscom.co.jp/"),
    ("株式会社レイ", "https://www.ray.co.jp/"),
    ("株式会社レッグス", "http://www.legs.co.jp/"),
    ("ワヨー株式会社", "https://www.wayo.co.jp/"),
    ("株式会社アドインテ", "https://adinte.co.jp/"),
]


def main():
    rows = []
    for company_name, home_url in CANDIDATES:
        try:
            home_text, links = fetch(home_url)
        except Exception:
            continue
        combined_text = home_text
        for page_url in candidate_pages(home_url, links)[1:]:
            try:
                page_text, _ = fetch(page_url)
                combined_text += "\n" + page_text
            except Exception:
                continue
        address = find_address(combined_text)
        phone = find_phone(combined_text)
        if address and (phone or "問い合わせ" in combined_text):
            rows.append(
                {
                    "company_name": company_name,
                    "url": home_url,
                    "address": address,
                    "phone": phone,
                    "maps_url": "",
                    "status": "",
                }
            )
    with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["company_name", "url", "address", "phone", "maps_url", "status"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"candidates={len(CANDIDATES)} extracted={len(rows)} -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
