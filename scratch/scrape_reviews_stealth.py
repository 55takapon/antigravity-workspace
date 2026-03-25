import asyncio
import json
import random
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # 人間のブラウザのように設定
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            # 本物のブラウザに近い言語・ロケール
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
            viewport={"width": 1280, "height": 1024}
        )
        
        page = await context.new_page()
        
        # Google検索結果のクチコミダイアログを直接開くURL (Mapサイドバーを避ける)
        url = "https://www.google.com/search?q=Refine(%E3%83%AA%E3%83%95%E3%82%A1%E3%82%A4%E3%83%B3)+%E5%A7%AB%E8%B7%AF#lrd=0x3554e19574fcf3ef:0x8fd62496a7888795,1,,,"
        
        print(f"Opening Google Search Reviews Modal...")
        try:
            # ページ読み込み
            await page.goto(url, wait_until="domcontentloaded", timeout=90000)
            await asyncio.sleep(random.uniform(8, 12))
            
            # クチコミ要素が出るまで待つ
            # 検索のダイアログスクロール領域を特定
            selectors = [".review-dialog-list", ".review-results", ".gws-localreviews__google-review", "div.m6B62e", "[role='main']"]
            scrollable = None
            
            for _ in range(6):
                for s in selectors:
                    scrollable = await page.query_selector(s)
                    if scrollable and await scrollable.query_selector(".jftiEf"):
                        print(f"Found scrollable area: {s}")
                        break
                if scrollable: break
                print("Waiting for reviews to load in modal...")
                await asyncio.sleep(5)
            
            if not scrollable:
                print("Modal/Scrollable not found. Trying coordinate scroll as fallback.")
                await page.screenshot(path="debug_modal_not_found.png")
            
            print("Starting slow human-like scroll in modal...")
            
            last_count = 0
            for i in range(80): 
                if scrollable:
                    scroll_amount = random.randint(500, 900)
                    await page.evaluate(f"(el) => el.scrollBy(0, {scroll_amount})", scrollable)
                else:
                    await page.mouse.wheel(0, random.randint(500, 900))
                
                await asyncio.sleep(random.uniform(2, 4))
                
                current_reviews = await page.query_selector_all(".jftiEf")
                count = len(current_reviews)
                print(f"Iteration {i}: Loaded {count} reviews...")
                
                if count >= 60: break
                if count > 0 and count == last_count and i > 40:
                    break
                last_count = count

            # 各クチコミの「もっと見る」をクリックして展開
            print("Expanding 'More' buttons...")
            more_buttons = await page.query_selector_all("a[jsaction*='expand'], button[aria-label*='もっと見る']")
            for btn in more_buttons:
                try:
                    await btn.scroll_into_view_if_needed()
                    await btn.click()
                    await asyncio.sleep(random.uniform(0.1, 0.4))
                except:
                    continue

            # 抽出
            final_reviews = []
            review_elements = await page.query_selector_all(".jftiEf")
            print(f"Extracting {len(review_elements)} reviews...")
            
            for el in review_elements:
                try:
                    name_el = await el.query_selector(".d4r55")
                    name = await name_el.inner_text() if name_el else "Unknown"
                    
                    text_el = await el.query_selector(".wiM73")
                    text = await text_el.inner_text() if text_el else ""
                    
                    if not text.strip():
                        continue
                        
                    rating_el = await el.query_selector(".kvsyjd")
                    rating = await rating_el.get_attribute("aria-label") if rating_el else "N/A"
                    
                    date_el = await el.query_selector(".rsqawe")
                    date = await date_el.inner_text() if date_el else "Unknown"
                    
                    final_reviews.append({
                        "name": name.strip(),
                        "rating": rating,
                        "text": text.strip(),
                        "date": date.strip()
                    })
                except:
                    continue

            with open("direct_reviews.json", "w", encoding="utf-8") as f:
                json.dump(final_reviews, f, ensure_ascii=False, indent=2)
            
            print(f"Done. Extracted {len(final_reviews)} reviews.")
            await page.screenshot(path="debug_direct_final.png")

        except Exception as e:
            print(f"Error during extraction: {e}")
            await page.screenshot(path="debug_direct_error.png")

        await browser.close()

if __name__ == "__main__":
    # jsの評価で random が使えない可能性があるので修正
    import random as py_random
    # page.evaluate の中で pythonの random は使えない
    asyncio.run(main())
