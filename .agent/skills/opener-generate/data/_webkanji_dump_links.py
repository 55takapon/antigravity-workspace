from playwright.sync_api import sync_playwright
import sys

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(sys.argv[1], wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    print(page.locator("a").evaluate_all(
        "els => els.map(e => ({text:(e.innerText||'').trim(), href:e.href||''}))"
        ".filter(x => x.text || x.href.startsWith('mailto:'))"
    ))
    browser.close()
