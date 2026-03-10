#!/usr/bin/env python3
"""
Convert DNG files to PNG using rawpy for C version compatibility
"""

import rawpy
import numpy as np
from PIL import Image
import glob
import os

def convert_dng_to_png(dng_file):
    """Convert a DNG file to PNG using rawpy"""
    try:
        print(f"Converting {dng_file} to PNG...")
        
        with rawpy.imread(dng_file) as raw:
            # Process like the Python version does
            rgb = raw.postprocess(
                output_bps=8,
                use_auto_wb=True,
                no_auto_bright=True,
                output_color=rawpy.ColorSpace.sRGB,
            )
            
            # Create PIL image
            img = Image.fromarray(rgb, mode="RGB")
            
            # Save as PNG
            png_file = os.path.splitext(dng_file)[0] + '.png'
            img.save(png_file, 'PNG')
            print(f"Saved: {png_file} ({img.size[0]}x{img.size[1]})")
            
            return png_file
            
    except Exception as e:
        print(f"ERROR converting {dng_file}: {e}")
        return None

if __name__ == '__main__':
    # Find all DNG files
    dng_files = glob.glob('*.dng')
    
    if not dng_files:
        print("No DNG files found")
    else:
        print(f"Found {len(dng_files)} DNG files")
        
        for dng_file in dng_files:
            png_file = convert_dng_to_png(dng_file)
            if png_file:
                print(f"✅ Converted: {dng_file} → {png_file}")
            else:
                print(f"❌ Failed: {dng_file}")
        
        print("\nNow you can use the C version with PNG files:")
        print("  ./ttc-bash --use-pngs-only .")
