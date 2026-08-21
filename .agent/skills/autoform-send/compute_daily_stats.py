import sys
sys.path.insert(0, '../../../shared')
import sheets_io
from collections import defaultdict

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','status','error_reason','provider_used','sent_at'])

stats = defaultdict(lambda: {'processed':0,'completed':0,'failed':0,'skipped':0})

for r in rows:
    sent_at = (r.get('sent_at') or '').strip()
    if not sent_at:
        continue
    date_part = sent_at[:10]  # YYYY-MM-DD
    if date_part not in ('2026-08-20', '2026-08-21'):
        continue
    status = (r.get('status') or '').strip()
    stats[date_part]['processed'] += 1
    if status == 'completed':
        stats[date_part]['completed'] += 1
    elif status == 'failed':
        stats[date_part]['failed'] += 1
    elif status == 'skipped':
        stats[date_part]['skipped'] += 1

for d in sorted(stats.keys()):
    s = stats[d]
    print(d, s)

# also check overall min/max row range touched those two days
