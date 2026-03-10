#!/usr/bin/env python3
"""
Test Target Cropper - Python Version
Legacy version - use C version for better performance
"""

import argparse
import glob
import os
import sys
from PIL import Image

# Increase PIL's image size limit for large files
Image.MAX_IMAGE_PIXELS = None

__version__ = "1.2.0"

def _open_image(path):
    """Open image as PIL Image. For DNG, use rawpy for full resolution when available."""
    path_lower = path.lower()
    if path_lower.endswith(".dng"):
        try:
            import rawpy
            with rawpy.imread(path) as raw:
                rgb = raw.postprocess(
                    output_bps=8,
                    use_auto_wb=True,
                    no_auto_bright=True,
                    output_color=rawpy.ColorSpace.sRGB,
                )
            return Image.fromarray(rgb, mode="RGB")
        except ImportError:
            print("Warning: rawpy not installed. Install with: pip install rawpy")
            return Image.open(path).copy()
        except Exception as e:
            print(f"Warning: rawpy failed for {path}: {e}. Falling back to embedded preview.")
            return Image.open(path).copy()
    with Image.open(path) as im:
        return im.copy()

def create_composite_layout(input_png, output_prefix="composite", output_dir="crops"):
    """Create composite image with center crop on top and 4 corners below"""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Open the source image
        img = _open_image(input_png)
        width, height = img.size
        print(f"Processing {input_png}")
        print(f"Original image size: {width}x{height}")
        
        # Calculate crop sizes (maintain aspect ratio)
        crop_size = min(width // 2, height // 2)
        
        # Calculate positions
        center_x = width // 2
        center_y = height // 2
        
        # Extract crops
        center_crop = img.crop((
            center_x - crop_size // 2,
            center_y - crop_size // 2,
            center_x + crop_size // 2,
            center_y + crop_size // 2
        ))
        
        # Corner crops (smaller)
        corner_size = crop_size // 2
        corners = [
            img.crop((0, 0, corner_size, corner_size)),  # top-left
            img.crop((width - corner_size, 0, width, corner_size)),  # top-right
            img.crop((0, height - corner_size, corner_size, height)),  # bottom-left
            img.crop((width - corner_size, height - corner_size, width, height))  # bottom-right
        ]
        
        # Create composite
        composite_width = center_crop.width + corner_size * 2
        composite_height = center_crop.height + corner_size * 2
        
        composite = Image.new('RGB', (composite_width, composite_height))
        
        # Place center crop at top
        composite.paste(center_crop, (corner_size, 0))
        
        # Place corners at bottom
        composite.paste(corners[0], (0, center_crop.height))  # top-left -> bottom-left
        composite.paste(corners[1], (center_crop.width + corner_size, center_crop.height))  # top-right -> bottom-right
        composite.paste(corners[2], (0, center_crop.height + corner_size))  # bottom-left -> bottom-left
        composite.paste(corners[3], (center_crop.width + corner_size, center_crop.height + corner_size))  # bottom-right -> bottom-right
        
        # Save composite
        base_name = os.path.splitext(os.path.basename(input_png))[0]
        output_path = os.path.join(output_dir, f"{base_name}_composite.png")
        composite.save(output_path, 'PNG')
        
        print(f"Created composite: {output_path}")
        print(f"Composite size: {composite.width}x{composite.height}")
        print(f"Center crop: {center_crop.width}x{center_crop.height}")
        print(f"Corner crops: {corner_size}x{corner_size}")
        print("-" * 50)
        
    except Exception as e:
        print(f"Error processing {input_png}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Create composite images from test target photos for pixel peeping analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ttc                     Process current directory
  ttc ../photos           Process parent directory
  ttc /path/to/photos     Process absolute path
  ttc . -o results        Custom output directory
        """
    )
    
    parser.add_argument("input_dir", nargs="?", default=".", 
                       help="Directory containing PNG/DNG files (default: current directory)")
    parser.add_argument("-o", "--output", default=None,
                       help="Output directory for composite images (default: INPUT_DIR/crops)")
    parser.add_argument("-p", "--use-pngs-only", action="store_true",
                       help="Only process PNG files; default is to prefer DNG")
    parser.add_argument("-v", "--version", action="version", version=f"ttc {__version__}")
    
    args = parser.parse_args()
    
    input_dir = os.path.abspath(args.input_dir)
    
    if not os.path.isdir(input_dir):
        print(f"Error: Directory '{input_dir}' not found")
        return 1
    
    # Set output directory
    if args.output:
        output_dir = os.path.abspath(args.output)
    else:
        output_dir = os.path.join(input_dir, "crops")
    
    print(f"Searching for files in '{input_dir}'")
    
    # Find image files
    patterns = []
    if not args.use_pngs_only:
        patterns.append(os.path.join(input_dir, "*.dng"))
    patterns.append(os.path.join(input_dir, "*.png"))
    
    image_files = []
    for pattern in patterns:
        image_files.extend(glob.glob(pattern))
    
    if not image_files:
        print("No image files found to process.")
        return 0
    
    print(f"Found {len(image_files)} image files to process:")
    for img_file in sorted(image_files):
        print(f"  - {os.path.relpath(img_file, input_dir)}")
    
    print(f"Output directory: {output_dir}")
    print()
    
    # Process each image
    for img_file in sorted(image_files):
        create_composite_layout(img_file, output_dir=output_dir)
    
    print()
    print("Processing complete! Check the output directory for results.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
