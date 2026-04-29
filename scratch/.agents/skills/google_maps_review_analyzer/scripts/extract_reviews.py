"""
Googleマップ レビュー口コミ抽出スクリプト
=========================================
GoogleマップのURLからレビューを自動抽出する。
Playwrightを使用し、ステルスモードで全レビューをスクロール取得。

使用方法:
  python extract_reviews.py "https://maps.google.com/maps/place/..." [--output output.json] [--max-reviews 100]
"""

import asyncio
import json
import random
import re
import sys
import os
import datetime
from urllib.parse import quote, unquote
from argparse import ArgumentParser

# ============================================================
# URL変換ユーティリティ
# ============================================================

def extract_place_info_from_url(url: str) -> dict:
    """GoogleマップURLからplace_id / 店舗名 / CID等を抽出する"""
    info = {"original_url": url, "place_name": None, "cid": None, "ftid": None}
    
    # パターン1: /maps/place/PLACE_NAME/... 
    place_match = re.search(r'/maps/place/([^/]+)', url)
    if place_match:
        info["place_name"] = unquote(place_match.group(1)).replace('+', ' ')
    
    # パターン2: CID (0x...:0x...) を直接含む場合
    cid_match = re.search(r'(0x[0-9a-f]+:0x[0-9a-f]+)', url)
    if cid_match:
        info["cid"] = cid_match.group(1)
    
    # パターン3: ftid パラメータ
    ftid_match = re.search(r'ftid=(0x[0-9a-f]+:0x[0-9a-f]+)', url)
    if ftid_match:
        info["ftid"] = ftid_match.group(1)
        if not info["cid"]:
            info["cid"] = ftid_match.group(1)
    
    return info


def build_review_modal_url(place_info: dict) -> str:
    """Google検索のレビューモーダルを直接開くURLを構築する"""
    # CIDがある場合: Google検索のレビューモーダルを直接開く
    if place_info.get("cid"):
        cid = place_info["cid"]
        name = place_info.get("place_name", "")
        search_query = quote(name) if name else ""
        return f"https://www.google.com/search?q={search_query}#lrd={cid},1,,,"
    
    # CIDがない場合: 店舗名で検索してレビュータブを開く
    if place_info.get("place_name"):
        search_query = quote(place_info["place_name"])
        return f"https://www.google.com/maps/search/{search_query}"
    
    # フォールバック: 元URLをそのまま使う
    return place_info["original_url"]


# ============================================================
# レビュー抽出エンジン
# ============================================================

async def extract_reviews(url: str, max_reviews: int = 200) -> list[dict]:
    """Playwrightでレビューを抽出する"""
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: playwright がインストールされていません。")
        print("  pip install playwright && playwright install chromium")
        sys.exit(1)
    
    reviews = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
            viewport={"width": 1280, "height": 1024}
        )
        page = await context.new_page()
        
        # URL解析・変換
        place_info = extract_place_info_from_url(url)
        review_url = build_review_modal_url(place_info)
        
        print(f"[INFO] 店舗名: {place_info.get('place_name', '不明')}")
        print(f"[INFO] CID: {place_info.get('cid', '不明')}")
        print(f"[INFO] アクセスURL: {review_url}")
        
        try:
            # ======== Google Maps 直接アクセスの場合 ========
            is_maps_url = "maps" in review_url.lower() and "search" not in review_url.lower() or "maps/place" in review_url.lower()
            
            if "google.com/maps/place" in url or ("maps.app" in url):
                # Google Maps のプレイスページに直接アクセス
                print("[INFO] Google Maps プレイスページにアクセス中...")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(5, 8))
                
                # 「口コミ」タブをクリック
                review_tab_selectors = [
                    "button[aria-label*='クチコミ']",
                    "button[aria-label*='口コミ']",
                    "button[data-tab-id='reviews']",
                    "[role='tab']:has-text('クチコミ')",
                    "[role='tab']:has-text('口コミ')",
                ]
                for sel in review_tab_selectors:
                    tab = await page.query_selector(sel)
                    if tab:
                        await tab.click()
                        print(f"[INFO] 口コミタブをクリック: {sel}")
                        await asyncio.sleep(3)
                        break
                
                # Maps用スクロール対象
                scrollable = None
                maps_scroll_selectors = [
                    "div.m6QErb.DxyBCb.kA9KIf.dS8AEf",
                    "div.m6QErb.DxyBCb",
                    "div.m6QErb",
                    "[role='main']"
                ]
                for s in maps_scroll_selectors:
                    el = await page.query_selector(s)
                    if el:
                        scrollable = el
                        print(f"[INFO] スクロール領域検出: {s}")
                        break
                
                # Maps用レビュー要素セレクタ
                review_selector = "div.jftiEf, div[data-review-id]"
                name_selectors = [".d4r55", "div.d4r55 span"]
                text_selectors = [".wiI7pd", ".MyEned span"]
                rating_selectors = [".kvMYJc"]
                date_selectors = [".rsqaWe"]
                reply_selectors = [".CDe7pd"]
                
            else:
                # ======== Google検索レビューモーダルの場合 ========
                print("[INFO] Google検索レビューモーダルにアクセス中...")
                await page.goto(review_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(8, 12))
                
                scrollable = None
                search_scroll_selectors = [
                    ".review-dialog-list",
                    ".review-results",
                    "div.m6B62e",
                    "[role='main']"
                ]
                for s in search_scroll_selectors:
                    el = await page.query_selector(s)
                    if el:
                        scrollable = el
                        print(f"[INFO] スクロール領域検出: {s}")
                        break
                
                review_selector = ".jftiEf"
                name_selectors = [".d4r55", ".TSr39"]
                text_selectors = [".wiM73", ".Jtu6B"]
                rating_selectors = [".kvsyjd"]
                date_selectors = [".rsqawe"]
                reply_selectors = [".d4r55"]  # オーナー返信は別構造
            
            # ======== スクロールして全レビュー読み込み ========
            print("[INFO] レビューをスクロール読み込み中...")
            last_count = 0
            stale_rounds = 0
            
            for i in range(120):
                if scrollable:
                    scroll_amount = random.randint(400, 900)
                    await page.evaluate(f"(el) => el.scrollBy(0, {scroll_amount})", scrollable)
                else:
                    await page.mouse.wheel(0, random.randint(400, 900))
                
                await asyncio.sleep(random.uniform(1.5, 3.0))
                
                elements = await page.query_selector_all(review_selector)
                count = len(elements)
                
                if i % 5 == 0:
                    print(f"  スクロール {i}: {count} 件検出")
                
                if count >= max_reviews:
                    print(f"[INFO] 最大件数 {max_reviews} に到達")
                    break
                
                if count == last_count:
                    stale_rounds += 1
                    if stale_rounds >= 8:
                        print(f"[INFO] 新規レビューなし。全 {count} 件読み込み完了")
                        break
                else:
                    stale_rounds = 0
                last_count = count
            
            # ======== 「もっと見る」ボタンを展開 ========
            print("[INFO] 「もっと見る」ボタンを展開中...")
            more_buttons = await page.query_selector_all(
                "button[aria-label*='もっと見る'], "
                "button[aria-expanded='false'][jsaction*='review'], "
                "a[jsaction*='expand'], "
                ".w8nwRe.kXlcme"
            )
            for btn in more_buttons:
                try:
                    await btn.scroll_into_view_if_needed()
                    await btn.click()
                    await asyncio.sleep(random.uniform(0.05, 0.2))
                except:
                    continue
            print(f"[INFO] {len(more_buttons)} 件の展開ボタンを処理")
            
            # ======== レビューデータ抽出 ========
            print("[INFO] レビューデータを抽出中...")
            review_elements = await page.query_selector_all(review_selector)
            
            for idx, el in enumerate(review_elements):
                try:
                    # 投稿者名
                    name = "不明"
                    for sel in name_selectors:
                        name_el = await el.query_selector(sel)
                        if name_el:
                            name = (await name_el.inner_text()).strip()
                            break
                    
                    # レビュー本文
                    text = ""
                    for sel in text_selectors:
                        text_el = await el.query_selector(sel)
                        if text_el:
                            text = (await text_el.inner_text()).strip()
                            break
                    
                    # 星評価
                    rating = None
                    for sel in rating_selectors:
                        rating_el = await el.query_selector(sel)
                        if rating_el:
                            aria = await rating_el.get_attribute("aria-label")
                            if aria:
                                num_match = re.search(r'(\d)', aria)
                                if num_match:
                                    rating = int(num_match.group(1))
                            break
                    
                    # 投稿日
                    date_text = "不明"
                    for sel in date_selectors:
                        date_el = await el.query_selector(sel)
                        if date_el:
                            date_text = (await date_el.inner_text()).strip()
                            break
                    
                    # オーナー返信
                    owner_reply = None
                    reply_container = await el.query_selector(".CDe7pd")
                    if reply_container:
                        owner_reply = (await reply_container.inner_text()).strip()
                    
                    review_data = {
                        "id": idx + 1,
                        "name": name,
                        "rating": rating,
                        "date": date_text,
                        "text": text,
                        "has_owner_reply": owner_reply is not None,
                        "owner_reply": owner_reply
                    }
                    reviews.append(review_data)
                    
                except Exception as e:
                    continue
            
            print(f"[SUCCESS] {len(reviews)} 件のレビューを抽出完了")
            
        except Exception as e:
            print(f"[ERROR] 抽出中にエラー: {e}")
        
        await browser.close()
    
    return reviews


# ============================================================
# メイン
# ============================================================

def main():
    parser = ArgumentParser(description="Googleマップ レビュー口コミ抽出ツール")
    parser.add_argument("url", help="GoogleマップのURL")
    parser.add_argument("--output", "-o", default=None, help="出力ファイルパス (デフォルト: reviews_extracted_{timestamp}.json)")
    parser.add_argument("--max-reviews", "-m", type=int, default=200, help="最大取得件数 (デフォルト: 200)")
    args = parser.parse_args()
    
    # 出力パス
    if args.output is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"reviews_extracted_{timestamp}.json"
    
    # 抽出実行
    reviews = asyncio.run(extract_reviews(args.url, args.max_reviews))
    
    # 保存
    output_data = {
        "meta": {
            "source_url": args.url,
            "extracted_at": datetime.datetime.now().isoformat(),
            "total_count": len(reviews)
        },
        "reviews": reviews
    }
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"[OUTPUT] {args.output} に保存しました ({len(reviews)} 件)")
    return args.output


if __name__ == "__main__":
    main()
