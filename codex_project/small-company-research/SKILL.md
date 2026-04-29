---
name: small-company-research
description: Research and structure proposal candidate lists for small companies from portals, search results, and official websites. Use when Codex needs to collect company names and official URLs, avoid duplicates by normalized domain, extract representative names, capital, employee count, business/service descriptions, keyword matches, contact form URLs, source URLs, and extraction status for later spreadsheet filtering.
---

# Small Company Research

Use this skill to build proposal candidate lists for small companies. Treat it as a reusable core workflow: industry targeting is controlled by keyword profiles, not by creating a separate skill for every industry.

## Core Principle

Collect broadly, extract conservatively, and avoid early exclusion.

Do not decide too aggressively whether a company qualifies during collection. Save extracted values, source URLs, keyword matches, and status fields so the final filtering can happen in a spreadsheet or downstream system.

## Recommended Architecture

Keep one core skill for shared mechanics:

- Candidate collection from portals, search results, directories, and comparison articles
- Official site resolution
- Duplicate detection by normalized domain
- Company profile page discovery
- Profile field extraction
- Business and service keyword matching
- Contact form URL discovery
- Extraction status labeling
- CSV/JSON export

Keep industry-specific differences in a profile file such as `references/vertical-profiles.md`:

- Web production companies
- Web marketing companies
- Professional service and consulting firms
- Store or local business consulting firms
- Any future vertical with different inclusion, exclusion, and keyword rules

Do not fork this skill unless the data source, compliance constraints, or extraction workflow becomes materially different.

## Workflow

### 1. Load Inputs

Accept these inputs when available:

- Existing proposal candidate list for duplicate exclusion
- Portal URLs, search result exports, or seed company lists
- Target vertical profile name
- Inclusion keywords
- Exclusion keywords
- Required output format

If no vertical profile is provided, infer the closest profile from the user request and state the assumption.

### 2. Build Duplicate Index

Use normalized official domains as the primary duplicate key.

Normalize URLs before comparison:

- Lowercase host
- Remove protocol
- Remove leading `www.`
- Remove paths, query strings, fragments, and trailing slash
- Normalize obvious index pages such as `/index.html`

Examples:

```text
https://www.example.co.jp/
http://example.co.jp/company/
https://example.co.jp/contact?ref=portal
```

All become:

```text
example.co.jp
```

Prefer this minimum duplicate model:

```text
duplicate_status:
  new
  duplicate
  unknown

duplicate_reason:
  domain_match
  no_official_url
  none
```

Do not add company-name fuzzy matching unless the user explicitly needs it. Company-name matching adds false positives and is usually not worth the complexity for this use case.

### 3. Collect Candidate Companies

Use portals, category directories, comparison articles, and search results as candidate sources.

For each candidate, collect only lightweight seed data:

```json
{
  "seed_source_url": "",
  "seed_source_name": "",
  "company_name": "",
  "listed_category": "",
  "candidate_official_url": ""
}
```

Use portal information as a discovery hint, not as the final data source. Prefer official company websites for representative name, capital, employee count, service descriptions, and contact form URLs.

Respect site terms, robots.txt, rate limits, and legal/commercial restrictions. If a portal prohibits collection, bulk storage, or reuse beyond ordinary service use, do not rely on it as a bulk source without user approval.

### 4. Resolve Official Site

Confirm the official site before detailed extraction.

High-confidence signals:

- Company name appears in page title, header, footer, or company profile page
- Site has company profile, contact, privacy policy, or service pages
- Address, representative, or phone number matches portal hints
- Domain is not a marketplace, SNS, map listing, job board, or comparison site

If the official site is uncertain, set:

```text
official_url_status = uncertain
duplicate_status = unknown
```

Do not spend extraction budget on uncertain official sites unless the user asked for aggressive enrichment.

### 5. Precheck Duplicates

As soon as an official domain is known, compare it against the existing duplicate index.

If the domain matches, mark the row as duplicate and stop deeper extraction unless the user asked to refresh existing records.

Recommended behavior:

```text
domain match -> duplicate, skip profile crawl
no domain match -> new, continue extraction
no official URL -> unknown, keep seed row
```

### 6. Discover Profile Pages

Search the official site for profile pages using links and common path patterns.

Useful link texts:

```text
会社概要
企業情報
会社案内
About
Company
Profile
Outline
```

Useful path patterns:

```text
/company
/about
/profile
/outline
/corporate
/company-profile
/company/outline
```

Prioritize pages with tables, definition lists, or headings around company profile information. Avoid crawling blogs, news archives, case studies, and large article sets unless needed for service keyword matching.

### 7. Extract Company Fields

Extract fields as text first, then optionally normalize numeric values.

Target fields:

```json
{
  "company_name": "",
  "representative_name": "",
  "capital_text": "",
  "capital_amount_jpy": null,
  "employee_text": "",
  "employee_count": null,
  "address": "",
  "business_description": "",
  "service_description": "",
  "source_urls": []
}
```

Good source structures:

- HTML tables
- Definition lists
- Company profile sections
- Footer company blocks
- About pages
- Service overview pages

Use deterministic extraction first. Use AI only when text is ambiguous, fragmented, or classification requires judgment.

### 8. Match Industry Keywords

Check whether business and service descriptions contain target keywords from the chosen vertical profile.

Store keyword results as evidence, not as final qualification.

Recommended fields:

```json
{
  "matched_keywords": [],
  "negative_keywords": [],
  "keyword_status": "matched | not_matched | unknown"
}
```

Do not filter out `not_matched` or `unknown` rows during extraction. Save them so the user can review and filter later.

### 9. Find Contact Form URL

Find contact, inquiry, estimate, consultation, and request form pages.

Useful link texts:

```text
お問い合わせ
お問合せ
無料相談
相談する
見積もり
お見積り
資料請求
CONTACT
Contact
Inquiry
Request
```

Useful path patterns:

```text
/contact
/inquiry
/form
/estimate
/request
/consultation
```

Save the contact URL and status:

```text
contact_status:
  found
  not_found
  uncertain
```

Do not submit forms. This skill is for proposal candidate research and list preparation only.

### 10. Label Extraction Status

For each key field, record whether it was extracted.

Use these status values:

```text
extracted
not_found
ambiguous
not_checked
```

Recommended status fields:

```text
capital_status
employee_status
representative_status
business_status
service_status
contact_status
official_url_status
```

The output should make it easy to filter later:

- Extracted and likely target
- Extracted but likely outside target
- Not enough data to judge
- Duplicate
- Needs manual review

### 11. Export

Prefer CSV for spreadsheet workflows and JSON for downstream automation.

Recommended CSV columns:

```csv
company_name,
official_url,
normalized_domain,
duplicate_status,
duplicate_reason,
source_portal_url,
profile_page_url,
representative_name,
representative_status,
capital_text,
capital_amount_jpy,
capital_status,
employee_text,
employee_count,
employee_status,
business_description,
service_description,
matched_keywords,
negative_keywords,
keyword_status,
contact_form_url,
contact_status,
official_url_status,
source_urls,
notes,
retrieved_at
```

## AI Usage Policy

Use AI search or LLM extraction only for gaps and ambiguity:

- Official site cannot be confidently resolved
- Profile fields are embedded in messy text
- Employee count is implied but not clearly structured
- Business/service classification needs judgment
- Contact form is hidden behind non-obvious navigation

Do not send full websites or large pages to the model. Extract the relevant text block first, then pass only the compact snippet and requested schema.

## Practical Defaults

Default duplicate key:

```text
normalized_domain
```

Default extraction stance:

```text
extract_and_statusize
```

Default filtering stance:

```text
do_not_drop_non_duplicates
```

Default use of public registries:

```text
skip national corporate number and government enrichment unless the user explicitly asks
```

For this workflow, official websites are usually more useful than government registries because the target companies are small and the desired data is proposal-oriented, not legal identity verification.

## Quality Bar

Before finishing, check:

- Duplicate rows were removed or flagged by normalized domain
- Official site URLs are not portal, SNS, job board, or comparison pages
- Contact form URLs are actual company pages where possible
- Every important value has a source URL
- Missing data is represented with status fields, not silently blank
- No early filter removed uncertain but potentially useful candidates

