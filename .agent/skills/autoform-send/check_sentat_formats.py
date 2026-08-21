import sys
sys.path.insert(0, '../../../shared')
import sheets_io
from collections import Counter

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'SNS運用')
rows = sheets_io.read_rows(ws, want=['status','sent_at','provider_used'])

date_counts = Counter()
for r in rows:
    sent_at = (r.get('sent_at') or '').strip()
    if sent_at:
        date_counts[sent_at[:10]] += 1

for d, c in sorted(date_counts.items()):
    print(d, c)

print("total rows:", len(rows))
print("total with sent_at:", sum(date_counts.values()))
