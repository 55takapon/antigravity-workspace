import sys
sys.path.insert(0, '../../../shared')
import sheets_io

url = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
ws = sheets_io.open_worksheet(url, "Webマーケ")
rows = sheets_io.read_rows(ws, want=["company_name","contact_url","message"])
target = [23,25,29,30,32,35,39,42,45,46]
for r in rows:
    if r["_row"] in target:
        print(r["_row"], "|", r.get("company_name"), "|", r.get("contact_url"))
        msg = r.get("message","")
        print("   msglen:", len(msg))
        open(f"data/_wm_msg{r['_row']}.txt", "w", encoding="utf-8").write(msg)
