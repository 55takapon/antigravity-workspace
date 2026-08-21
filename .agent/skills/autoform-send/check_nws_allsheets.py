import sys
sys.path.insert(0, '../../../shared')
import sheets_io

client = sheets_io.get_client()
sh = client.open_by_url('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ')
print("Worksheets:", [w.title for w in sh.worksheets()])

for w in sh.worksheets():
    vals = w.get_all_values()
    if not vals:
        continue
    header = vals[0]
    # find company name col
    for i, row in enumerate(vals[1:], start=2):
        joined = ' '.join(row)
        if 'NWS' in joined:
            print(w.title, "row", i, row[:6])
