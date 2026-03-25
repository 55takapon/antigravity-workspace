import asyncio
import json
import random
import os
from playwright.async_api import async_playwright

# 環境変数をセッション内で強制設定
os.environ["HOME"] = os.path.expanduser("~")

async def main():
    async with async_playwright() as p:
        # モバイルエミュレーション (よりシンプルなUIとボット検知回避)
        device = p.devices['iPhone 14']
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            **device,
            locale="ja-JP",
            timezone_id="Asia/Tokyo"
        )
        
        page = await context.new_page()
        
        # ステルスJSの注入 (ボット検知回避)
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => False });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['ja-JP', 'ja', 'en-US', 'en'] });
        """)
        
        # 直接のクチコミURL (Google Maps版)
        url = "https://www.google.com/maps/place/Refine+(%E3%83%AA%E3%83%95%E3%82%A1%E3%82%A4%E3%83%B3)/@34.8219504,134.6811466,17z/data=!4m8!3m7!1s0x3554e19574fcf3ef:0x8fd62496a7888795!8m2!3d34.8219504!4d134.6837215!9m1!1b1!16s%2Fg%2F1tj_9631?hl=ja"
        
        print(f"Opening direct Maps reviews for Refine Himeji...")
        try:
            await page.goto(url, wait_until="load", timeout=90000)
            await asyncio.sleep(10)
            
            # 「アプリを試す」モーダルの回避
            web_btn = await page.query_selector("text='ウェブに戻る'")
            if web_btn:
                print("Dismissing app promotion modal...")
                await web_btn.click()
                await asyncio.sleep(5)
            
            await page.screenshot(path="maps_opened.png")
            
            # クチコミボタンを探してクリック
            print("Accessing reviews list...")
            review_btn = await page.query_selector("text='クチコミ'")
            if review_btn:
                await review_btn.click()
                await asyncio.sleep(random.uniform(5, 8))
            
            print("Loading all 55 reviews (scrolling)...")
            all_data = []
            last_count = 0
            
            for i in range(150):
                scroll_y = random.randint(400, 800)
                await page.mouse.wheel(0, scroll_y)
                await asyncio.sleep(random.uniform(2, 4))
                
                reviews = await page.query_selector_all(".jftiEf, .gws-localreviews__google-review")
                curr_count = len(reviews)
                if i % 10 == 0:
                    print(f"Scroll iteration {i}: Found {curr_count} review elements...")
                
                # ユーザー依頼の55件に達するか、読み込みが止まるまで
                if curr_count >= 65: break 
                if curr_count > 0 and curr_count == last_count and i > 60:
                    break
                last_count = curr_count

            print(f"Extraction started for {len(reviews)} elements...")
            for el in reviews:
                try:
                    # 「もっと見る」の展開
                    more = await el.query_selector("button[aria-label*='もっと見る'], a[jsaction*='expand']")
                    if more: 
                        await more.scroll_into_view_if_needed()
                        await more.click()
                        await asyncio.sleep(random.uniform(0.2, 0.5))
                    
                    name_el = await el.query_selector(".d4r55, .TSr39")
                    name = await name_el.inner_text() if name_el else "Unknown"
                    
                    text_el = await el.query_selector(".wiM73, .Jtu6B")
                    text = await text_el.inner_text() if text_el else ""
                    
                    # コメントありレビューのみ
                    if not text.strip(): continue
                    
                    rating_el = await el.query_selector(".kvsyjd, .P9469e")
                    rating = await rating_el.get_attribute("aria-label") if rating_el else "N/A"
                    
                    date_el = await el.query_selector(".rsqawe, .P9469e")
                    date = await date_el.inner_text() if date_el else "Unknown"
                    
                    all_data.append({
                        "name": name.strip(),
                        "rating": rating,
                        "text": text.strip(),
                        "date": date.strip()
                    })
                except: continue

            # 重複削除
            unique_reviews = list({f"{r['name']}-{r['text'][:30]}": r for r in all_data}.values())
            
            with open("refine_himeji_reviews.json", "w", encoding="utf-8") as f:
                json.dump(unique_reviews, f, ensure_ascii=False, indent=2)
            
            print(f"Success! Captured {len(unique_reviews)} reviews for Refine Himeji.")
            await page.screenshot(path="refine_himeji_complete.png")

        except Exception as e:
            print(f"Final error: {e}")
            await page.screenshot(path="debug_final_fatal.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
