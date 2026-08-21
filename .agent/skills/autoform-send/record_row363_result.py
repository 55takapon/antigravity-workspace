import sys, datetime
sys.path.insert(0, '../../../shared')
import sheets_io

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'SNS運用')
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

row = {
    '_row': 363,
    'status': 'completed',
    'provider_used': 'playwright_mcp',
    'sent_at': now,
    'error_reason': '',
}
sheets_io.write_cells(ws, [row], columns=['status', 'provider_used', 'sent_at', 'error_reason'], overwrite=True)
print('row363 recorded: completed')
