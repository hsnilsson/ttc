#!/usr/bin/env python3
"""
Test VIPS with PNG file
"""

import pyvips
import os

png_file = "./_DSC4190-_DSC4205.png"

print(f"Testing VIPS with PNG: {png_file}")

try:
    # Try to load with VIPS
    image = pyvips.Image.new_from_file(png_file)
    print(f"SUCCESS: VIPS loaded PNG {image.width}x{image.height}")
    print(f"Format: {image.format}")
    print(f"Bands: {image.bands}")
    print(f"Interpretation: {image.interpretation}")
    
except ImportError:
    print("pyvips not available - installing...")
    os.system("pip install pyvips")
    
except Exception as e:
    print(f"VIPS ERROR: {e}")
    import traceback
    traceback.print_exc()

# Also test with PIL
try:
    from PIL import Image
    print(f"\nTesting with PIL:")
    
    with Image.open(png_file) as img:
        print(f"PIL loaded PNG {img.size}")
        print(f"Format: {img.format}")
        print(f"Mode: {img.mode}")
        
except Exception as e:
    print(f"PIL ERROR: {e}")
