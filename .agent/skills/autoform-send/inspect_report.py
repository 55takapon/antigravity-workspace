import sys
sys.path.insert(0, '../../../shared')
import sheets_io

client = sheets_io.get_client()
sh = client.open_by_url('https://docs.google.com/spreadsheets/d/1AYcp48D-6reZakByytlq3Dh_pZOxCo107cjjWxOtIfI/edit?usp=sharing')
print("Worksheets:", [ws.title for ws in sh.worksheets()])
for ws in sh.worksheets():
    print("---", ws.title, "---")
    vals = ws.get_all_values()
    print("rows:", len(vals))
    for row in vals[:15]:
        print(row)
