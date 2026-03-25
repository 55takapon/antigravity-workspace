from PIL import Image, ImageDraw, ImageFont
import os

# Ensure directory exists
os.makedirs('luxury_salon/images', exist_ok=True)

def create_placeholder(filename, width, height, color, text):
    img = Image.new('RGB', (width, height), color=color)
    d = ImageDraw.Draw(img)
    
    # Text settings
    # For simplicity, using default font since loading system fonts can be tricky cross-platform without knowing exact paths
    # Just center the text roughly
    text_color = (255, 255, 255)
    
    # Draw a border
    d.rectangle([0, 0, width-1, height-1], outline=text_color, width=2)
    
    # Draw text (very basic centering without font metrics)
    # Since we can't easily rely on a specific font file being present or load default fonts perfectly in this env
    # We will just save the colored block which is better than broken image
    
    img.save(os.path.join('luxury_salon/images', filename))
    print(f"Created {filename}")

# Define images to create
images = [
    ('hero_bg.jpg', 1920, 1080, '#2c3e50', 'Hero Image'),
    ('concept.jpg', 600, 800, '#8e44ad', 'Concept Image'),
    ('gallery1.jpg', 400, 400, '#16a085', 'Gallery 1'),
    ('gallery2.jpg', 400, 400, '#27ae60', 'Gallery 2'),
    ('gallery3.jpg', 400, 400, '#2980b9', 'Gallery 3'),
    ('gallery4.jpg', 400, 400, '#8e44ad', 'Gallery 4'),
    ('gallery5.jpg', 400, 400, '#f39c12', 'Gallery 5'),
    ('gallery6.jpg', 400, 400, '#d35400', 'Gallery 6'),
    ('map.jpg', 800, 450, '#95a5a6', 'Map Area')
]

for filename, w, h, color, text in images:
    create_placeholder(filename, w, h, color, text)
