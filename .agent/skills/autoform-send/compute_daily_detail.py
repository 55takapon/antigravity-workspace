import sys
sys.path.insert(0, '../../../shared')
import sheets_io
from collections import defaultdict

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','status','error_reason','provider_used','sent_at'])

for target_date in ('2026-08-20', '2026-08-21'):
    matched = [r for r in rows if (r.get('sent_at') or '')[:10] == target_date]
    if not matched:
        continue
    row_nums = [r['_row'] for r in matched]
    providers = defaultdict(int)
    statuses = defaultdict(int)
    for r in matched:
        providers[r.get('provider_used') or 'none'] += 1
        statuses[r.get('status') or 'none'] += 1
    print(f"=== {target_date} ===")
    print("row range:", min(row_nums), "-", max(row_nums), "count:", len(matched))
    print("providers:", dict(providers))
    print("statuses:", dict(statuses))
    print()
