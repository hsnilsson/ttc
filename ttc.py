#!/usr/bin/env python3
"""
Test Target Cropper - Command Line Interface

Creates composite images from test target photos for pixel peeping analysis.
Generates 2x2 grid of corner crops with center overlay.

Perfect for analyzing lens sharpness, resolution, and optical performance.

Usage:
    ttc                    # Process current directory
    ttc ../photos          # Process parent directory
    ttc /path/to/photos    # Process absolute path
    ttc . -o results       # Custom output directory

Author: hsnilsson
License: MIT
Version: 1.3.0
"""

import argparse
import glob
import os
import sys
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from PIL import Image

# Try to import psutil for memory monitoring (optional)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Increase PIL's image size limit for large files
Image.MAX_IMAGE_PIXELS = None  # Disable the limit

__version__ = "1.3.0"

def _get_memory_usage():
    """Get current memory usage as percentage"""
    if not HAS_PSUTIL:
        return 0  # No monitoring available
    try:
        return psutil.virtual_memory().percent
    except Exception as e:
        print(f"Warning: Could not get memory usage: {e}")
        return 0

def _check_memory_limit(threshold=90):
    """Check if memory usage exceeds threshold"""
    if not HAS_PSUTIL:
        return False  # No monitoring, assume safe
    return _get_memory_usage() > threshold

@lru_cache(maxsize=128)
def _calculate_crop_coordinates(width, height):
    """Cache crop coordinate calculations for repeated use."""
    corner_height = int(height * 0.07)
    corner_width = corner_height
    
    center_crop_percent = {
        'x1': 0.58, 'y1': 0.37,
        'x2': 0.61, 'y2': 0.42
    }
    
    center_left = int(width * center_crop_percent['x1'])
    center_top = int(height * center_crop_percent['y1'])
    center_right = int(width * center_crop_percent['x2'])
    center_bottom = int(height * center_crop_percent['y2'])
    
    corner_positions = {
        'top_left': (0.095, 0.120),
        'top_right': (0.862, 0.143),
        'bottom_left': (0.078, 0.779),
        'bottom_right': (0.848, 0.801)
    }
    
    corner_positions_pixels = {}
    for name, (x_percent, y_percent) in corner_positions.items():
        x = int(width * x_percent)
        y = int(height * y_percent)
        corner_positions_pixels[name] = (x, y)
    
    return {
        'corner_width': corner_width,
        'corner_height': corner_height,
        'center_coords': (center_left, center_top, center_right, center_bottom),
        'corner_coords': corner_positions_pixels
    }

def _open_image(path):
    """Open image as PIL Image. For DNG, use rawpy for full resolution when available."""
    path_lower = path.lower()
    if path_lower.endswith(".dng"):
        try:
            import rawpy
            with rawpy.imread(path) as raw:
                # Use more memory-efficient settings for large RAW files
                rgb = raw.postprocess(
                    output_bps=8,
                    use_auto_wb=True,
                    no_auto_bright=True,
                    output_color=rawpy.ColorSpace.sRGB,
                    # Memory optimization settings
                    demosaic_algorithm=rawpy.DemosaicAlgorithm.LINEAR,  # Less memory intensive
                    user_flip=0,  # Don't auto-rotate to save memory
                    use_camera_wb=False,  # Skip camera WB calculation
                )
            # rgb is (height, width, 3) uint8
            return Image.fromarray(rgb, mode="RGB")
        except ImportError:
            print("Warning: rawpy not installed. DNG will be read as embedded preview (small). Install with: pip install rawpy")
            return Image.open(path).copy()
        except Exception as e:
            print(f"Warning: rawpy failed for {path}: {e}. Falling back to embedded preview.")
            return Image.open(path).copy()
    with Image.open(path) as im:
        return im.copy()

def create_composite_layout(input_png, output_prefix="composite", output_dir="crops"):
    """Create composite image with center crop on top and 4 corners below"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        img = _open_image(input_png)
        width, height = img.size
        print(f"Processing {input_png}")
        print(f"Original image size: {width}x{height}")
        
        # Use cached coordinate calculations
        coords = _calculate_crop_coordinates(width, height)
        corner_width = coords['corner_width']
        corner_height = coords['corner_height']
        
        # Crop regions using pre-calculated coordinates
        center_crop = img.crop(coords['center_coords'])
        
        corner_crops = {}
        for name, (x, y) in coords['corner_coords'].items():
            crop_box = (x, y, x + corner_width, y + corner_height)
            corner_crops[name] = img.crop(crop_box)
        
        # Create composite layout
        composite_width = 2 * corner_width
        composite_height = 2 * corner_height
        
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
        
        # Clean up memory explicitly
        img.close()
        for crop in corner_crops.values():
            crop.close()
        center_crop.close()
        composite.close()
            
    except Exception as e:
        print(f"Error processing {input_png}: {e}")

def _process_single_file(file_info):
    """Process a single file - designed for parallel execution."""
    file_path, output_dir = file_info
    
    # Check memory before processing
    if _check_memory_limit(90):
        if HAS_PSUTIL:
            print(f"Warning: High memory usage ({_get_memory_usage():.1f}%). Waiting before processing {os.path.basename(file_path)}...")
        else:
            print(f"Warning: Memory check triggered. Waiting before processing {os.path.basename(file_path)}...")
        gc.collect()  # Force garbage collection
        if _check_memory_limit(90):
            if HAS_PSUTIL:
                print(f"Memory still high ({_get_memory_usage():.1f}%). Skipping {os.path.basename(file_path)} to prevent exhaustion.")
            else:
                print(f"Memory check still triggered. Skipping {os.path.basename(file_path)} to prevent exhaustion.")
            return file_path
    
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_prefix = f"{base_name}_composite"
    create_composite_layout(file_path, output_prefix, output_dir)
    
    # Force cleanup after processing
    gc.collect()
    return file_path

def process_all_files(input_dir=".", output_dir=None, use_pngs_only=False, max_workers=None):
    """Process all image files in specified directory with parallel processing."""
    
    if output_dir is None:
        output_dir = os.path.join(input_dir, "crops")
    
    # Find all image files
    search_patterns = [
        os.path.join(input_dir, "*.png"),
        os.path.join(input_dir, "*.dng")
    ]
    print(f"Searching for files with patterns: {search_patterns}")
    
    all_files = []
    for pattern in search_patterns:
        found_files = glob.glob(pattern)
        print(f"Pattern '{pattern}' found {len(found_files)} files")
        all_files.extend(found_files)
    
    # Filter out existing composites and crop files
    exclude_patterns = ["composite", "_crops_"]
    
    def excluded(filename):
        return any(p in filename for p in exclude_patterns)
    
    candidates = [f for f in all_files if not excluded(os.path.basename(f))]
    png_files = [f for f in candidates if f.lower().endswith(".png")]
    dng_files = [f for f in candidates if f.lower().endswith(".dng")]
    
    if use_pngs_only:
        input_files = png_files
    else:
        if dng_files:
            input_files = dng_files
        elif png_files:
            response = input("No DNG files found. Process PNG files instead? [y/N] ").strip().lower()
            if response not in ("y", "yes"):
                print("Skipping.")
                return
            input_files = png_files
        else:
            input_files = []
    
    if not input_files:
        print(f"No image files found to process in '{input_dir}'.")
        return
    
    print(f"Found {len(input_files)} image files to process:")
    for file in input_files:
        print(f"  - {file}")
    print(f"Output directory: {output_dir}")
    
    # Set adaptive number of workers based on available memory and cores
    if max_workers is None:
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        mem_usage = _get_memory_usage()
        
        if not HAS_PSUTIL:
            # No memory monitoring - use conservative default
            max_workers = min(4, max(1, cpu_count // 2))
            print(f"Processing with {max_workers} parallel workers (no memory monitoring)...")
        else:
            # Reduce workers if memory is already high
            if mem_usage > 80:
                max_workers = max(1, min(2, cpu_count // 4))  # Very conservative
            elif mem_usage > 60:
                max_workers = max(1, min(4, cpu_count // 2))  # Conservative
            else:
                max_workers = max(1, cpu_count - 1)  # Use all cores except one (avoid 100% CPU)
            
            print(f"Processing with {max_workers} parallel workers (memory: {mem_usage:.1f}% used)...")
    print()
    
    # Process files in parallel
    file_info_list = [(file, output_dir) for file in input_files]
    
    if len(input_files) == 1:
        # Single file - no need for threading overhead
        _process_single_file(file_info_list[0])
    else:
        # Multiple files - use ThreadPoolExecutor with memory monitoring
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(_process_single_file, file_info): file_info[0] 
                for file_info in file_info_list
            }
            
            # Process completed tasks as they finish
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    future.result()  # Get the result or raise exception
                    
                    # Check memory after each completion
                    if _check_memory_limit(90):
                        if HAS_PSUTIL:
                            print(f"Memory usage high ({_get_memory_usage():.1f}%). Pausing to allow cleanup...")
                        else:
                            print("Memory check triggered. Pausing to allow cleanup...")
                        gc.collect()
                        
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    print(f"\nProcessing complete! Check the '{output_dir}' directory for results.")

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Create composite images from Vlad's test target photos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ttc                    # Process current directory
  ttc ../test_photos     # Process parent directory
  ttc /path/to/photos    # Process absolute path
  ttc . -o results       # Custom output directory
        """
    )
    parser.add_argument(
        "input_dir", 
        nargs="?", 
        default=".",
        help="Directory containing PNG/DNG files (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_dir",
        help="Output directory for composite images (default: INPUT_DIR/crops)"
    )
    parser.add_argument(
        "--use-pngs-only", "--use-pngs",
        dest="use_pngs_only",
        action="store_true",
        help="Only process PNG files; default is to prefer DNG and fall back to PNG only after asking"
    )
    parser.add_argument(
        "-j", "--jobs",
        dest="max_workers",
        type=int,
        help="Number of parallel workers (default: CPU count)"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Test Target Cropper {__version__}"
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
    
    process_all_files(args.input_dir, args.output_dir, args.use_pngs_only, args.max_workers)
    return 0

if __name__ == "__main__":
    sys.exit(main())
