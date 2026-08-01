import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_yahoo_sns as yahoo
import collect_bing_sns as base
from collect_ddg_partner import SECONDARY_CITIES


TERM_SETS = {
    "0": [
        "Webマーケティング会社", "SNS運用 支援会社", "Web広告 運用会社",
        "LINE公式 運用支援会社", "販売促進 デジタル会社", "地域広告代理店 Web",
        "Web制作 広告運用会社", "動画マーケティング会社", "店舗集客 支援会社",
        "中小企業 マーケティング支援会社",
    ],
    "1": [
        "飲食店 集客支援会社", "美容サロン SNS集客会社", "クリニック Web集客会社",
        "不動産 マーケティング会社", "工務店 集客支援会社", "学習塾 生徒募集 支援会社",
        "ホテル 観光プロモーション会社", "小売店 デジタル販促会社",
        "採用広報 SNS支援会社", "地域ブランディング会社",
    ],
    "2": [
        "Shopify パートナー 制作会社", "EC運営 マーケティング支援会社",
        "CRM 導入 マーケティング支援", "マーケティングオートメーション 導入支援",
        "予約システム 店舗集客支援", "LINEミニアプリ 販促支援会社",
        "顧客管理 リピーター支援会社", "Web解析 改善コンサル会社",
        "コンテンツマーケティング 支援会社", "デジタルキャンペーン 企画会社",
    ],
    "3": [
        "PR会社 SNS支援", "広報 コンテンツ制作会社", "広告企画会社 Web",
        "デザイン会社 SNS運用", "動画制作 Web広告会社", "写真撮影 SNS支援会社",
        "イベント企画 デジタルプロモーション", "販促デザイン Web制作会社",
        "採用マーケティング会社", "地域プロモーション会社",
    ],
    "4": [
        "Shopify パートナー 会社", "LINE公式 導入パートナー 会社",
        "HubSpot 導入支援会社", "Salesforce マーケティング 導入支援",
        "kintone CRM 導入支援会社", "ECコンサルティング 運用会社",
        "MAツール 導入支援会社", "店舗アプリ 開発 販促支援",
        "ロイヤルティプログラム 導入支援", "予約システム 導入 集客支援",
    ],
    "5": [
        "SNS運用 採用 株式会社", "Web広告運用 採用 株式会社",
        "デジタルマーケティング 採用 株式会社", "広告代理店 採用 Web",
        "Webマーケター 採用 制作会社", "SNSマーケター 採用 会社",
        "広告運用担当 採用 会社", "Webコンサルタント 採用 会社",
        "動画マーケティング 採用 会社", "地域プロモーション 採用 会社",
    ],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_csv")
    parser.add_argument("--lane", choices=list(TERM_SETS), required=True)
    args = parser.parse_args()
    lane = int(args.lane)
    if lane < 4:
        areas = SECONDARY_CITIES[lane * 35:(lane + 1) * 35]
    elif lane == 4:
        areas = SECONDARY_CITIES[:40]
    else:
        areas = SECONDARY_CITIES[70:110]
    tasks = [(area, term, 0) for area in areas for term in TERM_SETS[args.lane]]
    found = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(yahoo.search, task) for task in tasks]
        for index, future in enumerate(as_completed(futures), 1):
            found.extend(future.result())
            if index % 50 == 0:
                print(f"queries={index}/{len(tasks)} raw={len(found)}", flush=True)
    deduped, seen = [], set()
    for row in found:
        domain = base.host(row["url"])
        if domain in seen:
            continue
        seen.add(domain)
        deduped.append(row)
    fields = ["company_name", "url", "address", "phone", "maps_url", "area_hint", "query"]
    with Path(args.output_csv).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(deduped)
    print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
