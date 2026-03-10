# DNG File Compatibility Notice

## Issue Overview

The C version of Test Target Cropper uses the VIPS image processing library, which has limited support for certain DNG file formats. Some DNG files may not load properly, resulting in a NULL image error.

## Symptoms

When processing certain DNG files, you may see:
```
Error: VIPS loaded [filename].dng but returned NULL image
This is a known issue with some DNG files.
Try converting the DNG to a different format or use PNG files.
```

## Solutions

### Option 1: Convert DNG to PNG (Recommended)
Use the Python version to convert problematic DNG files:
```bash
python ttc.py .  # This will process DNG files and create PNG composites
```

### Option 2: Use PNG Files Directly
Convert your DNG files to PNG using any tool (Adobe Camera Raw, Darktable, etc.), then use the C version:
```cmd
ttc.exe --use-pngs-only
```

### Option 3: Use Python Version for DNG
Keep both versions available:
- Use `ttc.exe` (C version) for PNG files - faster and smaller
- Use `ttc.py` (Python version) for DNG files - better compatibility

## Technical Details

**Root Cause:** VIPS library returns success but NULL image pointer for some DNG files
**Status:** Known limitation, not a bug in the C code
**Workaround:** Proper error handling prevents crashes

## File Status

- ✅ **PNG files:** Full support in C version
- ⚠️ **DNG files:** Limited support in C version  
- ✅ **DNG files:** Full support in Python version

## Recommendation

For best results:
1. **Primary workflow:** Use C version (`ttc.exe`) for PNG files
2. **Fallback:** Use Python version (`ttc.py`) for DNG files with issues
3. **Conversion:** Convert problematic DNGs to PNG for future use

The C version provides significant performance benefits (94KB vs Python runtime) and faster processing for compatible files.
