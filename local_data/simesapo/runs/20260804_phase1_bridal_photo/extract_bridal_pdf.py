from pathlib import Path
import pdfplumber

pdf = Path(__file__).parents[4] / "tmp" / "pdfs" / "bridal_fair_2026_exhibitors.pdf"
out = Path(__file__).parent / "bridal_pdf_columns.txt"
chunks = []
with pdfplumber.open(pdf) as doc:
    for page_no, page in enumerate(doc.pages[1:], 2):
        width, height = page.width, page.height
        for column in range(4):
            left = width * column / 4
            right = width * (column + 1) / 4
            text = page.crop((left, 0, right, height)).extract_text(x_tolerance=2, y_tolerance=3) or ""
            chunks.append(f"\n===== PAGE {page_no} COLUMN {column + 1} =====\n{text}")
out.write_text("\n".join(chunks), encoding="utf-8")
print(out)
