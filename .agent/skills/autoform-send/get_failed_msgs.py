import sys
sys.path.insert(0, '../../../shared')
import sheets_io

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'Webマーケ')
rows = sheets_io.read_rows(ws, want=['company_name','contact_url','message','status'])
target_rows = [6,8,9,11,12,13,14,15,16,18,20]
for r in rows:
    if r['_row'] in target_rows:
        with open(f"data/_wm_msg{r['_row']}.txt", 'w', encoding='utf-8') as f:
            f.write(r['message'])
        print(r['_row'], r['company_name'], '| len=', len(r['message']), '| url=', r['contact_url'])
