import sys
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Webマーケ")
rows = sheets_io.read_rows(ws, want=["company_name","screenshot_path","sent_at","status","error_reason"])
for r in rows:
    if r["_row"] == 23:
        print(r)
