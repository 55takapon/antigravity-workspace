from PIL import Image, ImageDraw, ImageFont
import os

# 画像保存ディレクトリ
output_dir = r"c:\Users\hangy\.gemini\antigravity\scratch\torien\images"
os.makedirs(output_dir, exist_ok=True)

# 画像設定
images_config = [
    {"name": "hero.jpg", "size": (1920, 1080), "color": "#8B4513", "text": "炭火焼き鳥"},
    {"name": "menu-momo.jpg", "size": (800, 600), "color": "#D4AF37", "text": "地鶏もも串"},
    {"name": "menu-negima.jpg", "size": (800, 600), "color": "#8B4513", "text": "ねぎま串"},
    {"name": "menu-tsukune.jpg", "size": (800, 600), "color": "#D4AF37", "text": "つくね串"},
    {"name": "commitment-chicken.jpg", "size": (1200, 800), "color": "#FFB6C1", "text": "厳選地鶏"},
    {"name": "commitment-charcoal.jpg", "size": (1200, 800), "color": "#FF4500", "text": "備長炭"},
    {"name": "commitment-interior.jpg", "size": (1200, 800), "color": "#2C1810", "text": "店内の雰囲気"},
]

def create_placeholder_image(filename, size, color, text):
    """プレースホルダー画像を生成"""
    # 画像作成
    img = Image.new('RGB', size, color=color)
    draw = ImageDraw.Draw(img)
    
    # テキストを中央に配置
    try:
        # フォントサイズを画像サイズに応じて調整
        font_size = min(size[0], size[1]) // 10
        font = ImageFont.truetype("msgothic.ttc", font_size)
    except:
        # フォントが見つからない場合はデフォルトフォント
        font = ImageFont.load_default()
    
    # テキストのバウンディングボックスを取得
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 中央座標を計算
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    # テキストを描画（影付き）
    shadow_offset = 3
    draw.text((x + shadow_offset, y + shadow_offset), text, fill='#000000', font=font)
    draw.text((x, y), text, fill='#FFFFFF', font=font)
    
    # 画像を保存
    filepath = os.path.join(output_dir, filename)
    img.save(filepath, quality=95)
    print(f"Created: {filepath}")

# 全ての画像を生成
for config in images_config:
    create_placeholder_image(
        config["name"],
        config["size"],
        config["color"],
        config["text"]
    )

print(f"\n全ての画像を生成しました: {output_dir}")
