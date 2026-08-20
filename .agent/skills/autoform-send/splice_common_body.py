# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

# 新共通本文を読み込み
lines = open('../../../shared/common_body@SNS運用ver2(2000字制限対応).md', encoding='utf-8').read().split('\n')
s = next(i for i,l in enumerate(lines) if l.strip() == '---本文ここから---')
e = next(i for i,l in enumerate(lines) if l.strip() == '---本文ここまで---')
new_body = '\n'.join(lines[s+1:e])

ANCHOR = '貴社の取り組みを拝見する中で、'
TARGET_STATUS = {'failed', 'skipped', ''}

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['message','status'])

to_update = []
skipped_no_anchor = []
for r in rows:
    msg = (r.get('message') or '')
    status = (r.get('status') or '').strip()
    if not msg.strip():
        continue
    if status not in TARGET_STATUS:
        continue
    idx = msg.find(ANCHOR)
    if idx == -1:
        skipped_no_anchor.append(r['_row'])
        continue
    opener = msg[:idx]
    new_msg = opener + new_body
    to_update.append({'_row': r['_row'], 'message': new_msg, '_old_len': len(msg), '_new_len': len(new_msg)})

print(f"更新対象: {len(to_update)}件")
print(f"アンカー未検出（手動確認要）: {len(skipped_no_anchor)}件 -> {skipped_no_anchor[:20]}")

# サンプル確認（先頭3件）
for x in to_update[:3]:
    print(f"  行{x['_row']}: {x['_old_len']}字 -> {x['_new_len']}字（削減{x['_old_len']-x['_new_len']}字）")

import json
with open('_splice_preview.json', 'w', encoding='utf-8') as f:
    json.dump([{'_row': x['_row'], 'message': x['message']} for x in to_update], f, ensure_ascii=False)
print(f"\nプレビューを _splice_preview.json に保存（{len(to_update)}件）")
