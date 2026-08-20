# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../shared')
import sheets_io

EDITS = {
6: [
("""食品EC一本に絞ったうえで、楽天もAmazonも
Yahoo!もTikTok Shopも、公式のパートナー認定で
揃えておられるのを、一つずつ確かめてしまいました。""",
 """食品EC一本に絞り、楽天からTikTok Shopまで
公式パートナー認定を揃えておられる。
一つずつ確かめました。"""),
("""松屋フーズ様との合弁でモールハックを立ち上げ、
東京と福岡にフードLIVEスタジオまで構える。
特化とは、ここまでやることなのだと感じます。""",
 """松屋フーズ様との合弁、東京と福岡の
フードLIVEスタジオ。
特化とはここまでやることかと感じます。"""),
("""食品を扱う事業者様は実店舗をお持ちのことも多く、
売り場がモールの外にも広がっていくのだろうと、
拝読しながら考えていました。""",
 """食品を扱う事業者様は実店舗をお持ちのことも多く、
売り場はモールの外へ広がるのだろうと、
拝読しながら考えていました。"""),
],
528: [
("""『人間はひとくきの葦にすぎない。
だが、それは考える葦である』という言葉が、
社名と事業の両方を貫いている点に惹かれました。""",
 """『人間は考える葦である』という言葉が、
社名と事業の両方を貫いている。
その一貫性に惹かれました。"""),
("""戦略、マーケティング、制作、EC、メディアまでを横断し、
事業全体を考え抜いたうえで実装へつなげておられる。
その思考の深さが伝わります。""",
 """戦略から制作、EC、メディアまでを横断し、
事業全体を考え抜いて実装へつなげておられる。
その思考の深さが伝わります。"""),
],
531: [
("""自社の表現を前へ出すのではなく、
企業や人が持つ発想を実現するための道具として、
技術とクリエイティブを使っておられるのですね。""",
 """自社の表現を前に出すのではなく、
企業や人の発想を実現する道具として、
技術とクリエイティブを使っておられる。"""),
("""Web、広告、CG、動画を横断しながら、
アイデアを高品質な形へまとめる姿勢に、
同じ作り手として強く惹かれました。""",
 """Web、広告、CG、動画を横断しながら、
アイデアを形にまとめる姿勢に、
同じ作り手として惹かれました。"""),
],
}

ws = sheets_io.open_worksheet('https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit', 'SNS運用')
rows = sheets_io.read_rows(ws, want=['company_name','message'])

updates = []
for r in rows:
    if r['_row'] not in EDITS: continue
    msg = r.get('message') or ''
    orig_len = len(msg)
    ok = True
    for before, after in EDITS[r['_row']]:
        if before not in msg:
            print(f"  !! 行{r['_row']}: 置換元が見つかりません -> {before[:25]}...")
            ok = False; continue
        msg = msg.replace(before, after)
    status = "OK" if len(msg) <= 2000 else "★まだ超過"
    print(f"行{r['_row']} {r.get('company_name')}: {orig_len}字 -> {len(msg)}字 (削減{orig_len-len(msg)}字) {status}")
    if ok and len(msg) <= 2000:
        updates.append({'_row': r['_row'], 'message': msg})

print(f"\n書き戻し可能: {len(updates)}件")
if len(updates) == 3:
    n = sheets_io.write_cells(ws, updates, columns=['message'], overwrite=True)
    print(f"{n} セル書き込み完了")
else:
    print("3件揃わないため書き戻しは保留しました")
