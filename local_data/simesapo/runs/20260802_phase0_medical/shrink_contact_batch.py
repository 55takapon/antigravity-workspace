import json, re
from pathlib import Path

p = Path(__file__).parent
pages = json.loads((p / "full_contact_batch.json").read_text(encoding="utf-8"))
pat = re.compile(r"contact|inquiry|toiawase|otoiawase|お問い合わせ|問合せ|ご相談|相談|資料請求|フォーム|partner|協業|提携", re.I)
for page in pages:
    selected = []
    seen = set()
    for link in page.get("links", []):
        blob = " ".join(str(link.get(k, "")) for k in ("href", "text", "alt_title"))
        if pat.search(blob) and link.get("href") not in seen:
            selected.append(link)
            seen.add(link.get("href"))
    page["links"] = selected[:40]
for i in range(0, len(pages), 15):
    (p / f"full_contact_batch_{i//15+1}.json").write_text(json.dumps(pages[i:i+15], ensure_ascii=False), encoding="utf-8")
print(len(pages), [len(x.get("links", [])) for x in pages])
