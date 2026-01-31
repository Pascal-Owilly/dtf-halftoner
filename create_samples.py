# create_samples.py
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def create_test_images():
    """Create sample test images"""
    samples_dir = "sample_images"
    os.makedirs(samples_dir, exist_ok=True)
    
    # 1. Gradient test
    gradient = np.zeros((500, 500, 3), dtype=np.uint8)
    for i in range(500):
        gradient[:, i] = int(i / 500 * 255)
    Image.fromarray(gradient).save(f"{samples_dir}/gradient.jpg")
    
    # 2. Color bars
    color_bars = np.zeros((400, 600, 3), dtype=np.uint8)
    colors = [
        (255, 0, 0),     # Red
        (0, 255, 0),     # Green  
        (0, 0, 255),     # Blue
        (255, 255, 0),   # Yellow
        (255, 0, 255),   # Magenta
        (0, 255, 255),   # Cyan
    ]
    bar_width = 600 // len(colors)
    for i, color in enumerate(colors):
        color_bars[:, i*bar_width:(i+1)*bar_width] = color
    Image.fromarray(color_bars).save(f"{samples_dir}/color_bars.jpg")
    
    # 3. Text sample
    img = Image.new('RGB', (800, 400), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 50), "DTF Test Pattern", fill=(0, 0, 0), font=font)
    draw.text((50, 120), "Color: RGB", fill=(255, 0, 0), font=font)
    draw.text((50, 180), "Gradient: Smooth", fill=(0, 128, 0), font=font)
    draw.text((50, 240), "Detail: High", fill=(0, 0, 255), font=font)
    
    # Add some shapes
    draw.rectangle([400, 50, 550, 200], fill=(255, 255, 0))
    draw.ellipse([600, 50, 750, 200], fill=(255, 0, 255))
    
    img.save(f"{samples_dir}/text_sample.jpg")
    
    print(f"Sample images created in {samples_dir}/")

if __name__ == "__main__":
    create_test_images()