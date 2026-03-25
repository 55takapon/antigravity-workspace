import asyncio
import json
import random
import os
import datetime
from playwright.async_api import async_playwright

# 環境変数をセッション内で再定義
os.environ["HOME"] = os.path.expanduser("~")
os.environ["USERPROFILE"] = os.path.expanduser("~")

async def main():
    async with async_playwright() as p:
        # 人間のブラウザを忠実に再現
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
            viewport={"width": 1280, "height": 1024},
            accept_downloads=True
        )
        
        page = await context.new_page()
        
        # 指示されたクチコミ直接表示URL (検索結果内のモーダル)
        url = "https://www.google.com/search?q=Refine(%E3%83%AA%E3%83%95%E3%82%A1%E3%82%A4%E3%83%B3)+%E5%A7%AB%E8%B7%AF#lrd=0x3554e19574fcf3ef:0x8fd62496a7888795,1,,,"
        
        print(f"[{datetime.datetime.now()}] Step 1: Opening Google Search Reviews Modal...")
        try:
            await page.goto(url, wait_until="load", timeout=90000)
            await asyncio.sleep(random.uniform(5, 10))
            await page.screenshot(path="manual_step1_open.png")
            
            # ロボット検知（CAPTCHA）の確認
            if await page.query_selector("iframe[title*='reCAPTCHA']"):
                print("CAPTCHA detected. Attempting to click checkbox (human-like motion)...")
                # reCAPTCHAのiframeの中を操作するのは難しいため、座標で試行するか一旦待つ
                # 通常、1回リフレッシュすると消える場合がある
                await page.reload()
                await asyncio.sleep(10)
            
            # クチコミのリスト領域を特定
            # 指示通り「1つずつ」処理するように、まず全件読み込む
            print(f"[{datetime.datetime.now()}] Step 2: Scrolling through the reviews list...")
            
            # スクロール可能なコンテナを動的に特定
            scrollable_selectors = [".review-dialog-list", ".review-results", "div.DxyBCb", "[role='main']"]
            scrollable = None
            for s in scrollable_selectors:
                el = await page.query_selector(s)
                if el:
                    scrollable = el
                    break

            last_count = 0
            for i in range(80): # 55件なら80回あれば十分
                if scrollable:
                    await page.evaluate(f"(el) => el.scrollBy(0, {random.randint(400, 800)})", scrollable)
                else:
                    await page.mouse.wheel(0, random.randint(400, 800))
                
                await asyncio.sleep(random.uniform(1.5, 3))
                
                # クチコミ要素数を確認
                elements = await page.query_selector_all(".jftiEf, .gws-localreviews__google-review")
                count = len(elements)
                print(f"Loaded {count} reviews...")
                
                if count >= 60: break
                if count > 0 and count == last_count and i > 40: break
                last_count = count
                
                if i % 10 == 0:
                    await page.screenshot(path=f"manual_step2_scroll_{i}.png")

            # 各クチコミを1つずつ「チェックしながらコピー」
            print(f"[{datetime.datetime.now()}] Step 3: Copying reviews one-by-one...")
            final_reviews = []
            review_elements = await page.query_selector_all(".jftiEf, .gws-localreviews__google-review")
            
            for idx, el in enumerate(review_elements):
                try:
                    # 「もっと見る」があれば展開
                    more = await el.query_selector("button[aria-label*='もっと見る'], a[jsaction*='expand']")
                    if more:
                        await more.scroll_into_view_if_needed()
                        await more.click()
                        await asyncio.sleep(random.uniform(0.1, 0.4))
                    
                    # データの読み取り
                    name_el = await el.query_selector(".d4r55, .TSr39")
                    name = await name_el.inner_text() if name_el else "Unknown"
                    
                    text_el = await el.query_selector(".wiM73, .Jtu6B")
                    text = await text_el.inner_text() if text_el else ""
                    
                    # ユーザー指示: コメントがあるものだけ
                    if not text.strip():
                        continue
                        
                    rating_el = await el.query_selector(".kvsyjd, .P9469e")
                    rating = await rating_el.get_attribute("aria-label") if rating_el else "N/A"
                    
                    date_el = await el.query_selector(".rsqawe, .P9469e")
                    date = await date_el.inner_text() if date_el else "Unknown"
                    
                    print(f"Copied review from {name}...")
                    final_reviews.append({
                        "id": idx,
                        "name": name.strip(),
                        "rating": rating,
                        "text": text.strip(),
                        "date": date.strip()
                    })
                    
                except Exception as e:
                    print(f"Skipping a review due to error: {e}")
                    continue

            # 保存
            with open("google_maps_final_copy.json", "w", encoding="utf-8") as f:
                json.dump(final_reviews, f, ensure_ascii=False, indent=2)
            
            print(f"DONE! Successfully copied {len(final_reviews)} reviews.")
            await page.screenshot(path="manual_step3_finished.png")

        except Exception as e:
            print(f"Fatal Error: {e}")
            await page.screenshot(path="manual_fatal_error.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
