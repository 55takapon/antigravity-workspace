import asyncio
from playwright.async_api import async_playwright
import json
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ja-JP",
            viewport={"width": 1280, "height": 1024}
        )
        page = await context.new_page()
        
        # Google検索結果のクチコミダイアログを直接開くURL
        url = "https://www.google.com/search?q=Refine(%E3%83%AA%E3%83%95%E3%82%A1%E3%82%A4%E3%83%B3)+%E5%A7%AB%E8%B7%AF#lrd=0x3554e19574fcf3ef:0x8fd62496a7888795,1,,,"
        
        print(f"Navigating to Google Search Reviews...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(10)
            
            # クチコミ要素が出るまで待つ (Mapsと同じ .jftiEf が使われることが多い)
            try:
                await page.wait_for_selector(".jftiEf", timeout=15000)
            except:
                print("Selector .jftiEf not found. Image check...")
                await page.screenshot(path="debug_search_result.png")
            
            # スクロール対象 (検索のダイアログは別クラスの場合がある)
            scrollable = None
            # 検索のダイアログスクロール領域
            selectors = [".review-dialog-list", ".review-results", ".gws-localreviews__google-review", "div.m6B62e", "[role='main']"]
            for s in selectors:
                el = await page.query_selector(s)
                if el:
                    scrollable = el
                    print(f"Found scrollable: {s}")
                    break
            
            if scrollable:
                print("Starting scroll...")
                last_count = 0
                for i in range(40):
                    await page.evaluate("(el) => el.scrollBy(0, 10000)", scrollable)
                    await asyncio.sleep(3)
                    elements = await page.query_selector_all(".jftiEf")
                    print(f"Scroll {i}: {len(elements)} reviews")
                    if len(elements) >= 55: break
                    if len(elements) == last_count and i > 20: break
                    last_count = len(elements)

            # 抽出
            reviews_data = []
            final_elements = await page.query_selector_all(".jftiEf")
            print(f"Extracting {len(final_elements)} reviews...")
            
            for el in final_elements:
                try:
                    # 全文展開 (検索結果では jsaction="review.expand" など)
                    more = await el.query_selector("a[jsaction*='expand'], button[aria-label*='もっと見る']")
                    if more: await more.click(); await asyncio.sleep(0.1)

                    name = "Unknown"
                    name_el = await el.query_selector(".d4r55")
                    if name_el: name = await name_el.inner_text()
                    
                    text = ""
                    text_el = await el.query_selector(".wiM73")
                    if text_el: text = await text_el.inner_text()
                    
                    rating = "N/A"
                    rating_el = await el.query_selector(".kvsyjd")
                    if rating_el: rating = await rating_el.get_attribute("aria-label")
                    
                    date = "Unknown"
                    date_el = await el.query_selector(".rsqawe")
                    if date_el: date = await date_el.inner_text()
                    
                    reviews_data.append({
                        "name": name.strip(),
                        "rating": rating,
                        "text": text.strip(),
                        "date": date.strip()
                    })
                except: continue

            with open("reviews.json", "w", encoding="utf-8") as f:
                json.dump(reviews_data, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(reviews_data)} reviews.")
            await page.screenshot(path="debug_search_success.png")

        except Exception as e:
            print(f"Extraction failed: {e}")
            await page.screenshot(path="debug_search_error.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
