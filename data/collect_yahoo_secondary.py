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
    "6": [
        "Google広告 認定代理店", "Yahoo広告 運用代理店", "Meta広告 運用支援会社",
        "TikTok広告 運用会社", "Instagram広告 運用会社", "LINE広告 運用会社",
        "Web広告 クリエイティブ制作会社", "広告分析 改善支援会社",
        "デジタル広告 コンサルティング会社", "中小企業 広告運用支援",
    ],
    "7": [
        "士業 Web集客 マーケティング会社", "税理士 集客支援会社",
        "弁護士 Webマーケティング会社", "整骨院 集客支援会社",
        "介護施設 集客 採用支援", "自動車整備工場 集客支援",
        "中古車販売 Webマーケティング", "住宅展示場 集客支援",
        "スクール SNS集客支援", "地域店舗 販促支援会社",
    ],
    "8": [
        "ホテル SNS運用 支援会社", "旅館 Web集客 支援会社",
        "観光施設 デジタルマーケティング", "地域観光 プロモーション会社",
        "商店街 デジタル販促支援", "道の駅 集客支援会社",
        "飲食店 リピーター施策 支援", "小売店 SNS販促支援",
        "地域イベント Webプロモーション", "インバウンド SNSマーケティング会社",
    ],
    "9": [
        "店舗アプリ 販促支援会社", "会員アプリ マーケティング支援",
        "顧客エンゲージメント 支援会社", "CRM コンサルティング 中小企業",
        "LINE CRM 運用支援会社", "メールマーケティング 支援会社",
        "デジタル会員証 導入支援", "予約管理 集客システム 会社",
        "ロイヤルティマーケティング 支援会社", "店舗DX 集客支援会社",
    ],
    "10": [
        "地域広告 企画制作会社", "地元広告代理店 デジタル支援",
        "自治体 プロモーション 受託会社", "地域ブランディング 制作会社",
        "広報 PR 支援会社 中小企業", "プレスリリース 制作支援会社",
        "Web PR コンサルティング会社", "地域メディア 広告企画会社",
        "イベント SNS プロモーション会社", "販促キャンペーン 企画会社",
    ],
    "11": [
        "採用広報 支援会社 SNS", "採用サイト 運用支援会社",
        "採用マーケティング コンサル会社", "企業ブランディング 採用支援",
        "中小企業 採用 SNS支援", "求人広告 Web運用会社",
        "採用動画 SNS 制作会社", "Instagram 採用広報 支援",
        "人材採用 コンテンツ制作会社", "採用オウンドメディア 支援会社",
    ],
    "12": [
        "D2C マーケティング 支援会社", "ECサイト 集客運用 支援会社",
        "楽天市場 運営代行 会社", "Amazon 運用代行 マーケティング会社",
        "ECモール 広告運用会社", "通販 販促支援会社",
        "ネットショップ SNS運用支援", "EC CRM 支援会社",
        "食品通販 マーケティング支援", "地域産品 EC 販売支援会社",
    ],
    "13": [
        "医療 広告代理店 Web", "歯科 集客 マーケティング会社",
        "介護 採用マーケティング会社", "工務店 広告代理店 Web",
        "不動産 SNS運用 支援会社", "学習塾 広告運用会社",
        "美容業界 Web広告会社", "飲食店 Web広告 運用会社",
        "士業 ホームページ 集客支援会社", "自動車業界 デジタルマーケティング会社",
    ],
    "14": [
        "SNS運用代行 お問い合わせ 株式会社", "Instagram運用代行 会社概要",
        "Web広告運用 お問い合わせ 会社", "広告代理店 お問い合わせ Web",
        "販促支援 会社概要 Web", "デジタルマーケティング お問い合わせ",
        "採用SNS運用 お問い合わせ", "LINE公式運用支援 会社概要",
        "動画マーケティング お問い合わせ", "EC運用代行 お問い合わせ 株式会社",
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
    elif lane == 5:
        areas = SECONDARY_CITIES[70:110]
    elif lane == 6:
        areas = SECONDARY_CITIES[15:55]
    elif lane == 7:
        areas = SECONDARY_CITIES[55:95]
    elif lane == 8:
        areas = SECONDARY_CITIES[95:135]
    elif lane == 9:
        areas = SECONDARY_CITIES[30:70]
    elif lane == 10:
        areas = SECONDARY_CITIES[:40]
    elif lane == 11:
        areas = SECONDARY_CITIES[40:80]
    elif lane == 12:
        areas = SECONDARY_CITIES[80:120]
    elif lane == 13:
        areas = SECONDARY_CITIES[105:145]
    else:
        areas = SECONDARY_CITIES[5:45]
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
