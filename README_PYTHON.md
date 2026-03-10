# Test Target Cropper

Creates composite images from test target photos (DNG or PNG) for analyzing lens performance and optical setup quality. Extracts 4 corner crops and 1 center crop stitched together for easy scrutiny and sharing.

### Why use a test target like Vlads test targets?

- **Film flatness & optical quality:** Quickly assess how flat your film or sensor sits in the camera by comparing corner to center sharpness
- **Maximum resolution testing:** Measure the actual achievable resolution (lp/mm) of your complete setup—camera, lens, scanner, and film handling combined
- **F-stop optimization:** Easily compare multiple shots taken at different apertures side-by-side, making it simple to find the f-stop that gives your preferred balance of sharpness between corners and center

## Current Status

**✅ WORKING:** Python version (fully functional)
**❌ REMOVED:** C version (broken VIPS linking issues)

## Quick Start

```bash
# Install dependencies
pip install pillow rawpy numpy

# Run the tool
python ttc.py .
```

Or use the simple batch file:
```bash
run.bat
```

## Features

- ✅ DNG support (full resolution via rawpy)
- ✅ PNG support (via PIL/Pillow)
- ✅ Composite image generation
- ✅ Corner and center cropping
- ✅ Cross-platform compatibility

## Requirements

- Python 3.7+
- Pillow (`pip install pillow`)
- rawpy (`pip install rawpy`)
- numpy (`pip install numpy`)

## Usage

```bash
# Process current directory
python ttc.py .

# Process specific directory
python ttc.py /path/to/photos

# Custom output directory
python ttc.py . -o results
```

## Output

Creates a composite image with:
- Center crop (top position)
- Four corner crops (bottom row)
- High resolution for pixel peeping

## History

The C version was attempted but had fundamental VIPS library linking issues that prevented image loading. The Python version provides complete functionality and is the recommended solution.

## License

MIT License - see [LICENSE](LICENSE) file for details.
