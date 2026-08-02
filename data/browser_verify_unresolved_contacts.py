import argparse
import asyncio
import csv
import json
import re
from pathlib import Path
from urllib.parse import urljoin

from playwright.async_api import async_playwright

from resolve_general_contact_forms import BAD_PATH, BAD_PURPOSE, HARD_BAD_PURPOSE, GOOD, FORM_HOST, score_candidate


async def inspect_page(page, url: str) -> tuple[bool, str, str, list[tuple[str, str]]]:
    try:
        response = await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(2500)
    except Exception as exc:
        return False, f"browser_fetch:{type(exc).__name__}", "", []
    final_url = page.url
    title = await page.title()
    heading_locator = page.locator("h1,h2")
    heading_texts = await heading_locator.all_inner_texts() if await heading_locator.count() else []
    headings = " ".join(heading_texts[:5])
    purpose = f"{title} {headings}"
    if HARD_BAD_PURPOSE.search(purpose) or (BAD_PURPOSE.search(purpose) and not GOOD.search(purpose)) or BAD_PATH.search(final_url):
        return False, "wrong_purpose", final_url, []
    forms = page.locator("form")
    for index in range(await forms.count()):
        form = forms.nth(index)
        signature = " ".join(filter(None, [await form.get_attribute("id"), await form.get_attribute("class"), await form.get_attribute("action"), (await form.inner_text())[:800]]))
        controls = form.locator("input:not([type=hidden]), textarea, select")
        control_count = await controls.count()
        submits = form.locator('button, input[type="submit"], input[type="image"]')
        if control_count >= 2 and await submits.count() >= 1 and not re.search(r"(?:search|newsletter|subscribe|login|password|メルマガ)", signature, re.I):
            return True, f"browser_form:controls={control_count}", final_url, []
    for frame in page.frames[1:]:
        try:
            if FORM_HOST.search(frame.url) or await frame.locator("form").count():
                return True, "browser_form_iframe", final_url, []
        except Exception:
            pass
    links = []
    anchors = page.locator("a[href]")
    for index in range(min(await anchors.count(), 500)):
        anchor = anchors.nth(index)
        href = await anchor.get_attribute("href") or ""
        text = (await anchor.inner_text()).strip()
        target = urljoin(final_url, href)
        if GOOD.search(f"{text} {target}") or FORM_HOST.search(target):
            links.append((target, text))
    return False, "browser_no_form", final_url, links


async def verify(browser, row: dict, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        base, old = row["url"], row["old_contact_url"]
        candidates = [(old, "current")]
        ok, evidence, _, links = await inspect_page(page, base)
        candidates.extend(links)
        ranked, seen = [], set()
        for url, text in candidates:
            if not url or url in seen:
                continue
            seen.add(url)
            score = score_candidate(url, text, base, old)
            if score > 0:
                ranked.append((score, url))
        ranked.sort(reverse=True)
        attempts = []
        for _, candidate in ranked[:8]:
            valid, reason, final_url, nested = await inspect_page(page, candidate)
            attempts.append(f"{final_url or candidate}:{reason}")
            if valid:
                await context.close()
                return {**row, "browser_contact_url": final_url, "browser_state": "valid", "browser_evidence": reason, "browser_attempts": " | ".join(attempts)}
            for nested_url, nested_text in nested[:5]:
                if score_candidate(nested_url, nested_text, base, old) <= 0:
                    continue
                nested_valid, nested_reason, nested_final, _ = await inspect_page(page, nested_url)
                attempts.append(f"{nested_final or nested_url}:{nested_reason}")
                if nested_valid:
                    await context.close()
                    return {**row, "browser_contact_url": nested_final, "browser_state": "valid", "browser_evidence": nested_reason, "browser_attempts": " | ".join(attempts)}
        await context.close()
        return {**row, "browser_contact_url": "", "browser_state": "unresolved", "browser_evidence": "browser_general_form_unconfirmed", "browser_attempts": " | ".join(attempts)}


async def run(args) -> None:
    with Path(args.input_csv).open(encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["contact_state"] != "valid"]
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        semaphore = asyncio.Semaphore(args.workers)
        output = []
        tasks = [asyncio.create_task(verify(browser, row, semaphore)) for row in rows]
        for index, task in enumerate(asyncio.as_completed(tasks), 1):
            output.append(await task)
            if index % 10 == 0:
                print(f"checked={index}/{len(rows)} valid={sum(item['browser_state']=='valid' for item in output)}", flush=True)
        await browser.close()
    output.sort(key=lambda item: int(item["_row"]))
    fields = list(rows[0].keys()) + ["browser_contact_url", "browser_state", "browser_evidence", "browser_attempts"]
    with Path(args.output_csv).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(output)
    print(json.dumps({"total": len(output), "valid": sum(item["browser_state"] == "valid" for item in output), "unresolved": sum(item["browser_state"] != "valid" for item in output)}, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    asyncio.run(run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
