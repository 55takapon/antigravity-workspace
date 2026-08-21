import sys, datetime
sys.path.insert(0, '../../../shared')
import sheets_io

URL = 'https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ'
ws = sheets_io.open_worksheet(URL, 'SNS運用')
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

row = {
    '_row': 513,
    'status': 'skipped',
    'provider_used': 'playwright_mcp',
    'sent_at': now,
    'error_reason': '300字上限ありスキップ（本文1939字で大幅超過）',
}
sheets_io.write_cells(ws, [row], columns=['status', 'provider_used', 'sent_at', 'error_reason'], overwrite=True)
print('row513 recorded: skipped')
