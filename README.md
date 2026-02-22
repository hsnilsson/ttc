# Vlad's Test Target Cropper

A Python script to create composite images from Vlad's test target photos for pixel peeping analysis.

## Purpose

This script processes photos of Vlad's test targets and creates compact composite images containing:

- 4 corner crops (square, 7% of image height)
- 1 center crop (resolution chart area)
- All crops arranged in a 2x2 grid with center overlay

Perfect for analyzing lens sharpness, resolution, and optical performance from test target photos.

## Features

- **Pixel-perfect output**: No compression, no interpolation artifacts
- **Configurable positions**: Easy adjustment of crop coordinates via percentages
- **Batch processing**: Processes all PNG files in directory
- **Large image support**: Handles high-resolution outputs
- **Flexible input/output**: Specify any directory for input and output
- **Smart output placement**: By default, creates output in input directory

## Requirements

- Python 3.7+
- Pillow (PIL) imaging library

```bash
pip install Pillow
```

## Usage

### Basic Usage (current directory)

```bash
ttc
```

### Specify Input Directory

```bash
ttc /path/to/test_photos
```

### Custom Output Directory

```bash
ttc /path/to/test_photos -o /path/to/output
```

### Examples

```bash
# Process test photos in current directory (output: ./crops)
ttc

# Process test photos in parent directory (output: ../crops)
ttc ..

# Process test photos with custom output directory
ttc ../test_photos -o ./results

# Process test photos with absolute paths
ttc "C:\Users\Name\Pictures\Test_Targets" -o "C:\Users\Name\Results"
```

## Configuration

Adjust crop positions by modifying the percentage values in the script:

```python
# Corner positions (x%, y% from top-left)
corner_positions = {
    'top_left': (0.095, 0.120),
    'top_right': (0.862, 0.143),
    'bottom_left': (0.078, 0.779),
    'bottom_right': (0.848, 0.801)
}

# Center crop (x1%, y1%, x2%, y2% from top-left)
center_crop_percent = {
    'x1': 0.58, 'y1': 0.37,
    'x2': 0.61, 'y2': 0.42
}
```

## Output

Each input PNG generates one composite image:

- `filename_composite.png` in the specified output directory
- **Default location**: `INPUT_DIR/crops/` (inside input directory)
- Maintains original image quality (no compression)
- Square corner crops for consistent analysis
- Center overlay covering resolution chart area

## Command Line Options

```
usage: ttc [-h] [-o OUTPUT] [input_dir]

Create composite images from Vlad's test target photos

positional arguments:
  input_dir             Directory containing PNG files (default: current directory)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory for composite images (default: INPUT_DIR/crops)

Examples:
  ttc                    # Process current directory
  ttc ../test_photos     # Process parent directory
  ttc /path/to/photos    # Process absolute path
  ttc . -o results       # Custom output directory
```

## License

MIT License

## TODO List

### Future Improvements

- [ ] **Make squares adjustable by input**
  - Add command-line parameter to specify corner crop size (currently fixed at 7% of image height)
  - Allow both percentage and absolute pixel values
  - Example: `--corner-size 0.1` or `--corner-size 500px`

- [ ] **Make squares not having to be squares**
  - Add option to specify bottom-right corner for one of the corner crops
  - Allow rectangular corner crops instead of forcing square aspect ratio
  - Could be implemented as `--corner-shape rectangular` or individual corner dimensions

- [ ] **Same for middle (center crop)**
  - Add command-line parameters to specify center crop coordinates
  - Allow override of hardcoded percentages (58%-61% H, 37%-42% V)
  - Example: `--center-crop 0.55,0.35,0.65,0.45` or `--center-crop pixels:10524,3188,12438,4463`

### Implementation Ideas

```bash
# Future command line interface might look like:
python create_composite.py ../png_files \
  --corner-size 0.08 \
  --corner-shape rectangular \
  --center-crop 0.56,0.34,0.63,0.44 \
  -o ./results
```

These improvements would make the script much more flexible for different test targets and use cases.
