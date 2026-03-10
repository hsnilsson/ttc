# DNG File Compatibility Notice

## Issue Overview

The C version of Test Target Cropper uses the VIPS image processing library. While VIPS command-line tools work correctly, there are **linking issues** between the C implementation and VIPS library that prevent proper image loading.

**Current Status:**

- **Python version:** Works perfectly with DNG (uses rawpy/LibRaw)
- **VIPS command-line:** Works correctly with all formats
- **C version:** VIPS library linking issues prevent image loading

## Symptoms

When processing any image files (DNG or PNG) with the C version, you may see:

```
Error: VIPS loaded [filename] but returned NULL image
This is a known issue with some DNG files.
Try converting the DNG to a different format or use PNG files.
```

**Note:** This error message is misleading - the issue affects all image formats, not just DNG files.

## Root Cause

The issue is **not** with the DNG files themselves, but with VIPS library linking in the C implementation:

- VIPS command-line tools work: `vips.exe thumbnail input.png output.png 100`
- Python VIPS bindings work (if available)
- C code linking to VIPS library fails to load images properly

## Solutions

### Option 1: Use Python Version (Recommended for DNG)

The Python version has full DNG support via rawpy:

```bash
python ttc.py .  # Process DNG files with full resolution
```

### Option 2: Use VIPS Command-Line for PNG

Convert images with VIPS command-line, then use C version:

```cmd
# Convert DNG to PNG using Python (full resolution)
python convert-dng-to-png.py

# Or use VIPS command-line directly
C:\vips\bin\vips.exe thumbnail input.dng output.png 1000

# Then use C version for PNG files
ttc.exe --use-pngs-only .
```

### Option 3: Fix VIPS Linking (Advanced)

The C version needs VIPS library linking fixes:

- Ensure proper VIPS library dependencies are linked
- Check for version compatibility between VIPS headers and libraries
- May require rebuilding VIPS from source

## Technical Details

**Python Version Architecture:**

- DNG files: rawpy → LibRaw → full resolution (19136x12752)
- PNG files: PIL/Pillow → standard image processing

**C Version Architecture:**

- All files: VIPS library → linking issues → NULL image pointer

**VIPS Command-Line:**

- All formats: VIPS CLI → works correctly
- Example: `vips.exe thumbnail input.dng output.png 1000`

## Recommendations

1. **For DNG files:** Use Python version (has rawpy support)
2. **For PNG files:** Use Python version or fix C version VIPS linking
3. **For development:** Focus on fixing VIPS library linking in C version

## Future Work

The C version VIPS linking issue needs to be resolved for:

- Native C performance benefits
- Standalone executable without Python dependency
- Cross-platform compatibility

Until then, the Python version provides the most reliable image processing.
