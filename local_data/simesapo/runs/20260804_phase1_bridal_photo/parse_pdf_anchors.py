from pathlib import Path
import re

src = Path(__file__).parent / "bridal_pdf_columns.txt"
lines = src.read_text(encoding="utf-8").splitlines()
rows = []
for i, line in enumerate(lines):
    if "URL：" not in line:
        continue
    context = [x.strip() for x in lines[max(0, i - 9):i + 2] if x.strip()]
    url = line.split("URL：", 1)[1].strip().replace(" ", "")
    rows.append(f"\n--- {len(rows)+1} ---\n" + "\n".join(context) + f"\nPARSED_URL={url}")
(Path(__file__).parent / "bridal_url_anchors.txt").write_text("\n".join(rows), encoding="utf-8")
print(f"anchors={len(rows)}")
