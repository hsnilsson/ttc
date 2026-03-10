# Test Target Cropper (C Version)

Creates composite images from test target photos (DNG or PNG) for analyzing lens performance and optical setup quality. Extracts 4 corner crops and 1 center crop stitched together for easy scrutiny and sharing.

### Why use a test target like Vlads test targets?

- **Film flatness & optical quality:** Quickly assess how flat your film or sensor sits in the camera by comparing corner to center sharpness
- **Maximum resolution testing:** Measure the actual achievable resolution (lp/mm) of your complete setup—camera, lens, scanner, and film handling combined
- **F-stop optimization:** Easily compare multiple shots taken at different apertures side-by-side, making it simple to find the f-stop that gives your preferred balance of sharpness between corners and center

## Current Status

**✅ C Version:** Native performance, small executable
**⚠️ VIPS Issues:** Currently has VIPS library linking problems

## Quick Start

```bash
# Install VIPS library
install-vips.bat

# Build the executable
build-w64devkit.bat

# Run the tool
ttc.exe .
```

## Features

- ✅ Native C performance
- ✅ Small executable (~94KB)
- ✅ No Python dependency
- ⚠️ VIPS linking issues (needs debugging)

## Requirements

- Windows
- VIPS image processing library
- w64devkit (C compiler)

## Installation

1. **Install VIPS:**
   ```cmd
   install-vips.bat
   ```

2. **Install Compiler:**
   ```cmd
   install-w64devkit.bat
   ```

3. **Build:**
   ```cmd
   build-w64devkit.bat
   ```

## Usage

```cmd
# Process current directory
ttc.exe

# Process specific directory
ttc.exe ../photos

# Custom output directory
ttc.exe . -o results

# Only process PNG files
ttc.exe --use-pngs-only
```

## Troubleshooting

The C version currently has VIPS library linking issues. See [DNG_COMPATIBILITY.md](DNG_COMPATIBILITY.md) for details.

## License

MIT License - see [LICENSE](LICENSE) file for details.
