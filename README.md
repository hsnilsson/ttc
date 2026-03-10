# Test Target Cropper (C Version)

Creates composite images from test target photos (PNG/JPG) for analyzing lens performance and optical setup quality. Extracts 4 corner crops and 1 center crop stitched together for easy scrutiny and sharing.

### Why use a test target like Vlads test targets?

- **Film flatness & optical quality:** Quickly assess how flat your film or sensor sits in the camera by comparing corner to center sharpness
- **Maximum resolution testing:** Measure the actual achievable resolution (lp/mm) of your complete setup—camera, lens, scanner, and film handling combined
- **F-stop optimization:** Easily compare multiple shots taken at different apertures side-by-side, making it simple to find the f-stop that gives your preferred balance of sharpness between corners and center

## Current Status

**✅ WORKING:** C version with stb_image (PNG/JPG/BMP/GIF support)
**🔧 IN PROGRESS:** libraw integration for DNG support (code ready, compiler issue)

## Quick Start

```bash
# Build the C version
build-simple.bat

# Run the tool
ttc-simple.exe .
```

## Features

- ✅ Native C performance
- ✅ Small executable (~50KB)
- ✅ No external dependencies (stb_image is header-only)
- ✅ PNG, JPG, BMP, GIF support (via stb_image)
- 🔧 DNG support (libraw integration ready)
- ✅ Cross-platform compatible

## Requirements

- Windows
- w64devkit (C compiler)
- No external image libraries needed!

## Installation

1. **Install Compiler:**

   ```cmd
   install-w64devkit.bat
   ```

2. **Install Dependencies:**

   ```cmd
   install-stb.bat
   install-libraw-source.bat  # For DNG support (when compiler issue resolved)
   ```

3. **Build:**

   ```cmd
   build-simple.bat
   ```

## Usage

```cmd
# Process current directory
ttc-simple.exe

# Process specific directory
ttc-simple.exe ../photos

# Custom output directory
ttc-simple.exe . -o results

# Only process PNG files
ttc-simple.exe --use-pngs-only
```

## Output

Creates a composite image with:

- Center crop (top position)
- Four corner crops (bottom row)
- High resolution for pixel peeping

## File Formats

### C Version (ttc-simple.exe)

- ✅ PNG, JPG, BMP, GIF, TGA, etc. (via stb_image)
- 🔧 DNG (libraw integration ready, pending compiler fix)

## Current Limitations

- **DNG support:** Code is implemented but requires working compiler setup
- **Compiler:** w64devkit download issues need resolution
- **Alternative:** TCC compiler missing POSIX directory functions

## Performance

- **C version:** ~50KB executable, native performance
- **DNG processing:** Full resolution via libraw
- **Memory usage:** Minimal, no runtime dependencies

## License

MIT License - see [LICENSE](LICENSE) file for details.
