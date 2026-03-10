#!/usr/bin/env python3
"""
Test rawpy DNG loading
"""

import rawpy
import numpy as np
from PIL import Image

dng_file = "./_DSC4190-_DSC4205.dng"

print(f"Testing DNG with rawpy: {dng_file}")

try:
    with rawpy.imread(dng_file) as raw:
        print("Raw data loaded successfully")
        
        # Process like the Python version does
        rgb = raw.postprocess(
            output_bps=8,
            use_auto_wb=True,
            no_auto_bright=True,
            output_color=rawpy.ColorSpace.sRGB,
        )
        
        print(f"Processed RGB shape: {rgb.shape}")
        print(f"RGB dtype: {rgb.dtype}")
        
        # Create PIL image
        img = Image.fromarray(rgb, mode="RGB")
        print(f"PIL image size: {img.size}")
        print(f"PIL image mode: {img.mode}")
        
        print("SUCCESS: rawpy can load full DNG!")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
