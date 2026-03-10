#!/usr/bin/env python3
"""
Create a smaller test image
"""

from PIL import Image

# Disable the limit
Image.MAX_IMAGE_PIXELS = None

# Open the large PNG
with Image.open('_DSC4190-_DSC4205.png') as img:
    print(f"Original size: {img.size}")
    
    # Create a smaller version for testing
    small_img = img.resize((1000, 666), Image.LANCZOS)
    small_img.save('_DSC4190-_DSC4205_small.png')
    print(f"Created small version: {small_img.size}")

# Test VIPS with the small image
try:
    import pyvips
    small_vips = pyvips.Image.new_from_file('_DSC4190-_DSC4205_small.png')
    print(f"VIPS loaded small image: {small_vips.width}x{small_vips.height}")
except Exception as e:
    print(f"VIPS error with small image: {e}")
