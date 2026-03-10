# Working Version Guide

## What Works Right Now

### ✅ Python Version (FULLY WORKING)
```bash
python ttc.py .
```
- ✅ DNG support via rawpy (full resolution)
- ✅ PNG support via PIL/Pillow
- ✅ All functionality working
- ✅ No setup required (just Python dependencies)

### ❌ C Version (BROKEN)
```bash
ttc.exe .
./ttc-bash .
```
- ❌ VIPS library linking issues
- ❌ Cannot load any images (DNG or PNG)
- ❌ Builds but doesn't work
- ❌ Requires expert C/Windows debugging

## Recommendation

**Use the Python version.** It works perfectly and has all the features you need.

The C version was a good attempt but has fundamental VIPS linking issues that are beyond current scope to fix.

## Python Setup

```bash
# Install dependencies (if needed)
pip install pillow rawpy numpy

# Run the tool
python ttc.py .
```

## Future C Version

The C version would need:
1. VIPS library linking expert
2. Windows development expertise  
3. Debug time and testing

Until then, the Python version provides the complete solution.
