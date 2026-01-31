import numpy as np
from PIL import Image
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.simple_halftone import rgb_to_cmyk, ordered_dither, generate_white_layer

# Create test image
print("Creating test image...")
test_img = np.zeros((200, 300, 3), dtype=np.uint8)
test_img[50:150, 50:150] = [255, 0, 0]    # Red square
test_img[50:150, 150:250] = [0, 255, 0]   # Green square

# Test CMYK conversion
print("Testing RGB to CMYK conversion...")
cmyk = rgb_to_cmyk(test_img)
print(f"CMYK shape: {cmyk.shape}, dtype: {cmyk.dtype}")
print(f"CMYK ranges - C: {cmyk[:,:,0].min()}-{cmyk[:,:,0].max()}")
print(f"            - M: {cmyk[:,:,1].min()}-{cmyk[:,:,1].max()}")

# Test white layer
print("\nTesting white layer generation...")
white = generate_white_layer(test_img)
print(f"White shape: {white.shape}")
print(f"White unique values: {np.unique(white)}")

# Test halftoning
print("\nTesting ordered dithering...")
cyan_halftoned = ordered_dither(cmyk[:,:,0])
print(f"Cyan halftoned shape: {cyan_halftoned.shape}")
print(f"Cyan values (0/255 only): {np.unique(cyan_halftoned)}")

# Save visual results
print("\nSaving test results...")
Image.fromarray(test_img).save("test_original.png")
Image.fromarray(cyan_halftoned).save("test_cyan_halftoned.png")
Image.fromarray(white).save("test_white_layer.png")

print("\n✅ CORE ALGORITHMS WORKING!")
print("Check files: test_original.png, test_cyan_halftoned.png, test_white_layer.png")
