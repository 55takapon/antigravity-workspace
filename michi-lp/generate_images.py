"""
michi-lp 用プレースホルダー画像生成スクリプト
Pillowがインストールされていれば、実際の写真に差し替えしやすい
カラーコーディネートされたプレースホルダー画像を生成します。
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def make_placeholder(filename, width, height, bg_color, label, text_color=(255,255,255)):
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 交互の格子柄で質感を出す
    step = 40
    for i in range(0, width + height, step * 2):
        draw.line([(i, 0), (0, i)], fill=(*bg_color[:2], max(bg_color[2]-20, 0)), width=1)

    # 中央のラベル枠
    margin = 30
    draw.rectangle([margin, margin, width-margin, height-margin],
                   outline=(*text_color, 180), width=2)

    # テキストをセンタリング
    try:
        font_large = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", size=max(30, height//10))
        font_small = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", size=max(18, height//20))
    except Exception:
        font_large = ImageFont.load_default()
        font_small = font_large

    # ファイル名ラベル（差し替え用の目印）
    file_label = f"【差し替え用】\n{filename}"
    bbox = draw.textbbox((0, 0), label, font=font_large)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((width - tw) // 2, height // 2 - th // 2 - 20),
              label, fill=text_color, font=font_large)

    bbox2 = draw.textbbox((0, 0), file_label, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((width - tw2) // 2, height // 2 + th // 2 + 10),
              file_label, fill=(*text_color[:3],), font=font_small)

    out_path = os.path.join(OUTPUT_DIR, filename)
    img.save(out_path, "JPEG", quality=90)
    print(f"  生成: {out_path}  ({width}x{height})")

# =============================================
# 各セクション用画像の定義
# 差し替え時は同名JPGをimagesフォルダに上書きするだけでOK
# =============================================
images = [
    # (ファイル名,     幅,    高さ,  背景色(RGB),           ラベル)
    ("hero.jpg",      1600,  900,  (60, 40, 30),          "ヒーロー画像\nお好み焼きの鉄板イメージ"),
    ("concept.jpg",   1200,  700,  (80, 60, 45),          "コンセプト画像\n夫婦・店内温かみ"),
    ("menu01.jpg",    600,   450,  (140, 70, 30),         "豚玉"),
    ("menu02.jpg",    600,   450,  (160, 90, 40),         "ミックス玉"),
    ("menu03.jpg",    600,   450,  (130, 80, 50),         "モダン焼き"),
    ("menu04.jpg",    600,   450,  (120, 75, 35),         "焼きそば"),
    ("gallery01.jpg", 600,   450,  (70, 60, 55),          "店内写真①\nカウンター・テーブル"),
    ("gallery02.jpg", 600,   450,  (80, 65, 55),          "店内写真②\n鉄板・厨房"),
    ("gallery03.jpg", 600,   450,  (75, 62, 50),          "店内写真③\n外観・入口"),
    ("gallery04.jpg", 600,   450,  (85, 68, 58),          "店内写真④\n季節・雰囲気"),
    ("owner.jpg",     800,   800,  (90, 75, 65),          "店主イメージ\n夫婦の写真"),
]

print("=== michi-lp プレースホルダー画像生成 ===")
for args in images:
    make_placeholder(*args)
print("\n完了！images/ フォルダを確認してください。")
print("実際の写真に差し替える場合は、同名のJPGファイルを images/ に上書き保存してください。")
