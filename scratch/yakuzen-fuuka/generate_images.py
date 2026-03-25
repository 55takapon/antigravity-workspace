from PIL import Image, ImageDraw, ImageFont
import os
import random

# Ensure directory exists
output_dir = r"C:\Users\hangy\.gemini\antigravity\scratch\yakuzen-fuuka"
os.makedirs(output_dir, exist_ok=True)

def create_placeholder(filename, width, height, color, text, subtext=""):
    img = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(img)
    
    # Add some subtle noise/texture to make it look less flat
    for _ in range(width * height // 50):
        x = random.randint(0, width)
        y = random.randint(0, height)
        noise_color = (
            min(255, color[0] + random.randint(-10, 10)),
            min(255, color[1] + random.randint(-10, 10)),
            min(255, color[2] + random.randint(-10, 10))
        )
        draw.point((x, y), fill=noise_color)

    # Simple layout for text
    try:
        # Try to load a default font, otherwise default
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw Text centered
    text_bbox = draw.textbbox((0, 0), text, font=font_large)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    
    draw.text(((width - text_w) / 2, (height - text_h) / 2), text, font=font_large, fill=(255, 255, 255))
    
    if subtext:
        subtext_bbox = draw.textbbox((0, 0), subtext, font=font_small)
        sub_w = subtext_bbox[2] - subtext_bbox[0]
        draw.text(((width - sub_w) / 2, (height - text_h) / 2 + text_h + 20), subtext, font=font_small, fill=(200, 200, 200))

    save_path = os.path.join(output_dir, filename)
    img.save(save_path, "JPEG", quality=90)
    print(f"Generated {save_path}")

# Colors (Approximate based on CSS variables)
# Primary (Matcha): #5d6d39 -> (93, 109, 57)
# Accent (Gold): #b69b4c -> (182, 155, 76)
# Dark: #2c3e50 -> (44, 62, 80)
# Warm Grey: #e6e2d8 -> (230, 226, 216)

# Hero Image
create_placeholder("hero.jpg", 1920, 1080, (44, 62, 80), "SEASONAL YAKUZEN", "Hero Image")

# Concept Image
create_placeholder("concept.jpg", 800, 600, (230, 226, 216), "CONCEPT", "Atmosphere & Ingredients")

# Menu Images
create_placeholder("menu_course.jpg", 600, 400, (93, 109, 57), "SEASONAL COURSE", "Food Image")
create_placeholder("menu_pot.jpg", 600, 400, (182, 155, 76), "YAKUZEN HOT POT", "Food Image")
create_placeholder("menu_lunch.jpg", 600, 400, (230, 226, 216), "LUNCH SET", "Food Image")
