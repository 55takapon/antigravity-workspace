import sys
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Webマーケ")
rows = sheets_io.read_rows(ws, want=["company_name","contact_url","status","error_reason","provider_used"])
for r in rows:
    if 76 <= r["_row"] <= 100:
        print(r["_row"], "|", r.get("company_name"), "|", r.get("status"), "|", r.get("provider_used"), "|", r.get("error_reason"))
