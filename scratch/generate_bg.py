from PIL import Image, ImageDraw, ImageFilter
import random
import math

def create_luxury_bg(width, height, filename):
    # Create base image with warm beige/grey
    img = Image.new('RGB', (width, height), color='#1e1e1e') # Dark base
    draw = ImageDraw.Draw(img)

    # Add soft gradients
    for i in range(20):
        x = random.randint(0, width)
        y = random.randint(0, height)
        radius = random.randint(200, 600)
        opacity = random.randint(20, 50)
        color = (197, 160, 89, opacity) # Gold-ish with alpha
        
        # Draw a soft circle (simulated by layering)
        # PIL doesn't support radial gradients easily without numpy/skimage, 
        # so we'll just draw semi-transparent circles and blur heavily
        
    # Better approach with pure PIL for a "luxury" look:
    # distinct abstract shapes
    
    # 1. Background gradient (simulating by drawing lines)
    for y in range(height):
        r = int(30 + (y/height) * 10)
        g = int(30 + (y/height) * 10)
        b = int(30 + (y/height) * 15)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 2. Add some "gold dust" or subtle light leaks
    layer = Image.new('RGBA', (width, height), (0,0,0,0))
    ldraw = ImageDraw.Draw(layer)
    
    for _ in range(5):
        # Large soft gold orbs
        x = random.randint(-200, width+200)
        y = random.randint(-200, height+200)
        r = random.randint(300, 800)
        
        # distinct circle? no, enable blur
        ldraw.ellipse((x-r, y-r, x+r, y+r), fill=(197, 160, 89, 40))

    # Blur the layer to make it soft
    layer = layer.filter(ImageFilter.GaussianBlur(100))
    
    # Composite
    img.paste(layer, (0, 0), layer)
    
    # Save
    img.save(filename)
    print(f"Generated {filename}")

if __name__ == "__main__":
    create_luxury_bg(1920, 1080, "luxury-salon-website/assets/hero_bg.png")
