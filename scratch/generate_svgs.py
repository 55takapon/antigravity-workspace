import os

# Ensure directory exists
os.makedirs('luxury_salon/images', exist_ok=True)

def create_svg(filename, width, height, color, text):
    svg_content = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="{color}"/>
  <text x="50%" y="50%" font-family="serif" font-size="24" fill="white" text-anchor="middle" dominant-baseline="middle">{text}</text>
</svg>'''
    
    with open(os.path.join('luxury_salon/images', filename), 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"Created {filename}")

# Define images to create
images = [
    ('hero_bg.svg', 1920, 1080, '#2c3e50', 'Hero Image'),
    ('concept.svg', 600, 800, '#8e44ad', 'Concept Image'),
    ('gallery1.svg', 400, 400, '#16a085', 'Gallery 1'),
    ('gallery2.svg', 400, 400, '#27ae60', 'Gallery 2'),
    ('gallery3.svg', 400, 400, '#2980b9', 'Gallery 3'),
    ('gallery4.svg', 400, 400, '#8e44ad', 'Gallery 4'),
    ('gallery5.svg', 400, 400, '#f39c12', 'Gallery 5'),
    ('gallery6.svg', 400, 400, '#d35400', 'Gallery 6'),
    ('map.svg', 800, 450, '#95a5a6', 'Map Area')
]

for filename, w, h, color, text in images:
    create_svg(filename, w, h, color, text)
