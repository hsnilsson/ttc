#!/usr/bin/env python3
"""
Test if VIPS can load the DNG file directly
"""

import sys
import os

try:
    import pyvips
    print("pyvips available")
    print(f"VIPS version: {pyvips.version(1)}")
    
    dng_file = "./_DSC4190-_DSC4205.dng"
    if os.path.exists(dng_file):
        print(f"Testing DNG file: {dng_file}")
        try:
            image = pyvips.Image.new_from_file(dng_file)
            print(f"SUCCESS: Loaded image {image.width}x{image.height}")
            print(f"Format: {image.format}")
            print(f"Bands: {image.bands}")
        except Exception as e:
            print(f"ERROR: {e}")
    else:
        print("DNG file not found")
        
except ImportError:
    print("pyvips not available - this confirms Python version uses PIL/Pillow")

# Test with PIL/Pillow (what the Python version uses)
try:
    from PIL import Image
    print("\nTesting with PIL/Pillow:")
    
    dng_file = "./_DSC4190-_DSC4205.dng"
    if os.path.exists(dng_file):
        try:
            with Image.open(dng_file) as img:
                print(f"SUCCESS: PIL loaded image {img.size}")
                print(f"Format: {img.format}")
                print(f"Mode: {img.mode}")
        except Exception as e:
            print(f"PIL ERROR: {e}")
            
except ImportError:
    print("PIL not available")
