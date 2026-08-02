import argparse
import csv
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BAD_FORM = re.compile(r"(?:search|site-search|newsletter|mail.?magazine|subscribe|login|signin|password|cart|coupon)", re.I)
CONTACT_MARKER = re.compile(r"(?:contact|inquiry|inquire|toiawase|otoiawase|formrun|hubspot|wpcf7|mw_wp_form|snow-monkey-form|forminator|ninja-forms|gravityforms|wixforms|お問い合わせ|お問合せ|問い合わせ|ご相談|メッセージ)", re.I)
FORM_HOST = re.compile(r"(?:docs\.google\.com/forms|forms\.gle|formrun\.app|form\.kintoneapp\.com|hubspot|form-mailer\.jp|ssl\.form-mailer\.jp|tayori\.com|formzu\.net|formok\.com)", re.I)
thread_local = threading.local()


def session() -> requests.Session:
    if not hasattr(thread_local, "session"):
        value = requests.Session()
        value.headers["User-Agent"] = "Mozilla/5.0 (compatible; contact-form-audit/1.0)"
        thread_local.session = value
    return thread_local.session


def classify_form(form) -> tuple[bool, str]:
    signature = " ".join([
        form.get("id", ""), " ".join(form.get("class", [])), form.get("action", ""),
        form.get_text(" ", strip=True)[:600],
    ])
    if BAD_FORM.search(signature) and not CONTACT_MARKER.search(signature):
        return False, "non_contact_form"
    controls = form.select("input:not([type=hidden]), textarea, select")
    names = " ".join((node.get("name", "") + " " + node.get("placeholder", "") + " " + node.get("type", "")) for node in controls)
    has_message = bool(form.select("textarea") or re.search(r"message|comment|content|body|お問い合わせ内容|ご相談内容", names, re.I))
    has_identity = bool(re.search(r"name|email|mail|tel|phone|氏名|名前|メール|電話", names, re.I))
    has_submit = bool(form.select('button, input[type="submit"], input[type="image"]'))
    if len(controls) >= 2 and has_submit and (has_message or has_identity or CONTACT_MARKER.search(signature)):
        return True, f"html_form:controls={len(controls)}"
    return False, "insufficient_form_controls"


def audit(row: dict) -> dict:
    result = {"_row": row.get("_row", ""), "company_name": row.get("company_name", ""), "url": row.get("url", ""), "contact_url": row.get("contact_url", ""), "form_state": "", "form_evidence": "", "http_status": "", "final_url": "", "title": ""}
    target = (row.get("contact_url") or "").strip()
    if not target:
        result.update(form_state="invalid", form_evidence="blank_contact_url")
        return result
    try:
        response = session().get(target, timeout=(5, 20), allow_redirects=True)
    except requests.RequestException as exc:
        result.update(form_state="review", form_evidence=f"fetch_failed:{type(exc).__name__}")
        return result
    result["http_status"], result["final_url"] = str(response.status_code), response.url
    if response.status_code >= 400 or "html" not in response.headers.get("content-type", ""):
        result.update(form_state="review", form_evidence=f"http_or_content:{response.status_code}")
        return result
    soup = BeautifulSoup(response.text, "html.parser")
    result["title"] = soup.title.get_text(" ", strip=True) if soup.title else ""
    for form in soup.select("form"):
        valid, evidence = classify_form(form)
        if valid:
            result.update(form_state="valid", form_evidence=evidence)
            return result
    for iframe in soup.select("iframe[src]"):
        source = iframe.get("src", "")
        signature = " ".join([source, iframe.get("title", ""), iframe.get("name", "")])
        if FORM_HOST.search(source) or CONTACT_MARKER.search(signature):
            result.update(form_state="valid", form_evidence=f"form_iframe:{source[:180]}")
            return result
    markup = response.text
    if re.search(r"(?:hbspt\.forms\.create|formrun|wixforms|wpcf7-form|mw_wp_form|snow-monkey-form|forminator-ui|ninja-forms-form|gform_wrapper)", markup, re.I):
        result.update(form_state="dynamic", form_evidence="dynamic_form_marker")
        return result
    if FORM_HOST.search(response.url):
        result.update(form_state="valid", form_evidence="external_form_host")
        return result
    result.update(form_state="no_form", form_evidence="no_form_found")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()
    with Path(args.input_csv).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    output = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(audit, row): row for row in rows}
        for index, future in enumerate(as_completed(futures), 1):
            row = futures[future]
            try:
                output.append(future.result())
            except Exception as exc:
                output.append({"_row": row.get("_row", ""), "company_name": row.get("company_name", ""), "url": row.get("url", ""), "contact_url": row.get("contact_url", ""), "form_state": "review", "form_evidence": f"error:{type(exc).__name__}", "http_status": "", "final_url": "", "title": ""})
            if index % 50 == 0:
                counts = {state: sum(item["form_state"] == state for item in output) for state in ("valid", "dynamic", "no_form", "review", "invalid")}
                print(f"checked={index}/{len(rows)} {counts}", flush=True)
    output.sort(key=lambda item: int(item["_row"]))
    fields = ["_row", "company_name", "url", "contact_url", "form_state", "form_evidence", "http_status", "final_url", "title"]
    with Path(args.output_csv).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(output)
    counts = {state: sum(item["form_state"] == state for item in output) for state in ("valid", "dynamic", "no_form", "review", "invalid")}
    print(json.dumps({"total": len(output), **counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
