import sys
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Webマーケ")
rows = sheets_io.read_rows(ws, want=["company_name","contact_url","message","status","error_reason"])
for r in rows:
    if r["_row"] == 16:
        print("company:", r.get("company_name"))
        print("url:", r.get("contact_url"))
        print("status:", r.get("status"))
        print("error_reason:", r.get("error_reason"))
        msg = r.get("message","")
        print("msglen:", len(msg))
        open("data/_wm_msg16.txt", "w", encoding="utf-8").write(msg)
