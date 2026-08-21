import sys
sys.path.insert(0, '../../../shared')
import sheets_io

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','contact_url','message','status'])
for r in rows:
    if r['_row'] == 243:
        print('company_name=', r['company_name'])
        print('contact_url=', r['contact_url'])
        print('msglen=', len(r['message']))
        with open('data/_msg243.txt','w',encoding='utf-8') as f:
            f.write(r['message'])
