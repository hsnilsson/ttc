#!/usr/bin/env python3
"""
Vlad's Test Target Cropper

Creates composite images from Vlad's test target photos for pixel peeping analysis.
Generates 2x2 grid of corner crops with center overlay.

Perfect for analyzing lens sharpness, resolution, and optical performance.

Author: Vlad's Test Target Cropper
License: MIT
Version: 1.0.0
"""

import argparse
import glob
import os
import sys
from PIL import Image

# Increase PIL's image size limit for large files
Image.MAX_IMAGE_PIXELS = None  # Disable the limit

__version__ = "1.0.0"

def create_composite_layout(input_png, output_prefix="composite", output_dir="crops"):
    """Create composite image with center crop on top and 4 corners below"""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Open the source image
        with Image.open(input_png) as img:
            width, height = img.size
            print(f"Processing {input_png}")
            print(f"Original image size: {width}x{height}")
            
            # Calculate crop dimensions
            corner_height = int(height * 0.07)  # 7% of image height
            corner_width = corner_height  # Make square
            
            # Center crop by percentage (adjust these as needed)
            center_crop_percent = {
                'x1': 0.58, 'y1': 0.37,  # top-left corner
                'x2': 0.61, 'y2': 0.42   # bottom-right corner
            }
            
            # Convert center crop percentages to pixel coordinates
            center_left = int(width * center_crop_percent['x1'])
            center_top = int(height * center_crop_percent['y1'])
            center_right = int(width * center_crop_percent['x2'])
            center_bottom = int(height * center_crop_percent['y2'])
            
            # Hardcoded corner positions by percentage (adjust these as needed)
            corner_positions = {
                'top_left': (0.095, 0.120),      # x%, y% from top-left
                'top_right': (0.862, 0.143),    # x%, y% from top-left
                'bottom_left': (0.078, 0.779),   # x%, y% from top-left
                'bottom_right': (0.848, 0.801)  # x%, y% from top-left
            }
            
            # Convert percentage positions to pixel coordinates
            corner_positions_pixels = {}
            for name, (x_percent, y_percent) in corner_positions.items():
                x = int(width * x_percent)
                y = int(height * y_percent)
                corner_positions_pixels[name] = (x, y)
            
            # Crop regions without any processing
            center_crop = img.crop((center_left, center_top, center_right, center_bottom))
            
            corner_crops = {}
            for name, (x, y) in corner_positions_pixels.items():
                crop_box = (x, y, x + corner_width, y + corner_height)
                corner_crops[name] = img.crop(crop_box)
            
            # Create composite layout
            composite_width = 2 * corner_width
            composite_height = 2 * corner_height
            
            # Create composite image with same mode as original
            composite = Image.new(img.mode, (composite_width, composite_height))
            
            # Place corners in 2x2 grid (base layer)
            composite.paste(corner_crops['top_left'], (0, 0))
            composite.paste(corner_crops['top_right'], (corner_width, 0))
            composite.paste(corner_crops['bottom_left'], (0, corner_height))
            composite.paste(corner_crops['bottom_right'], (corner_width, corner_height))
            
            # Calculate center position for overlay
            center_overlay_x = (composite_width - center_crop.width) // 2
            center_overlay_y = (composite_height - center_crop.height) // 2
            
            # Paste center crop on top
            composite.paste(center_crop, (center_overlay_x, center_overlay_y))
            
            # Save composite image with maximum quality settings
            output_file = os.path.join(output_dir, f"{output_prefix}.png")
            composite.save(output_file, compress_level=0, optimize=False)
            
            print(f"Created composite: {output_file}")
            print(f"Composite size: {composite_width}x{composite_height}")
            print(f"Center crop: {center_crop.width}x{center_crop.height}")
            print(f"Corner crops: {corner_width}x{corner_height}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error processing {input_png}: {e}")

def process_all_files(input_dir=".", output_dir=None):
    """Process all PNG files in specified directory"""
    
    # Set default output directory to be inside input directory
    if output_dir is None:
        output_dir = os.path.join(input_dir, "crops")
    
    # Find all PNG files (excluding existing composites)
    search_pattern = os.path.join(input_dir, "*.png")
    png_files = glob.glob(search_pattern)
    exclude_patterns = ["composite", "_crops_"]
    
    # Filter out existing composite and crop files
    input_files = []
    for png_file in png_files:
        filename = os.path.basename(png_file)
        should_exclude = False
        for pattern in exclude_patterns:
            if pattern in filename:
                should_exclude = True
                break
        if not should_exclude:
            input_files.append(png_file)
    
    if not input_files:
        print(f"No PNG files found to process in '{input_dir}'.")
        return
    
    print(f"Found {len(input_files)} PNG files to process:")
    for file in input_files:
        print(f"  - {file}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Process each file
    for png_file in input_files:
        # Create output prefix from filename
        base_name = os.path.splitext(os.path.basename(png_file))[0]
        output_prefix = f"{base_name}_composite"
        
        create_composite_layout(png_file, output_prefix, output_dir)
    
    print(f"\nProcessing complete! Check the '{output_dir}' directory for results.")

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Create composite images from Vlad's test target photos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_composite.py                    # Process current directory
  python create_composite.py ../test_photos     # Process parent directory
  python create_composite.py /path/to/photos    # Process absolute path
  python create_composite.py . -o results       # Custom output directory
        """
    )
    parser.add_argument(
        "input_dir", 
        nargs="?", 
        default=".",
        help="Directory containing PNG files (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_dir",
        help="Output directory for composite images (default: INPUT_DIR/crops)"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Vlad's Test Target Cropper {__version__}"
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.isdir(args.input_dir):
        print(f"Error: Directory '{args.input_dir}' does not exist.")
        return 1
    
    # Set default output directory if not specified
    if args.output_dir is None:
        args.output_dir = os.path.join(args.input_dir, "crops")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    process_all_files(args.input_dir, args.output_dir)
    return 0

if __name__ == "__main__":
    exit(main())
