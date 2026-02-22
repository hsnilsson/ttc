# Test Target Cropper - No Python Installation Required

## Option 1: Use with Existing Python

If you have Python installed (even Python 2.7), you can run ttc directly:

```cmd
# Run the script directly
python ttc.py --help

# Or with Python 3 if available
python3 ttc.py --help

# Or with py launcher
py -3 ttc.py --help
```

## Option 2: Portable Python (No Installation)

Download a portable Python version:

1. **Download portable Python:**
   - Go to https://www.python.org/downloads/windows/
   - Download "Windows embeddable package" (zip file)
   - Extract to `C:\portable-python\`

2. **Run with portable Python:**
```cmd
# Extract and run
C:\portable-python\python.exe ttc.py --help
```

## Option 3: Online Tools

Use online image processing tools that don't require installation:

1. **Photopea.com** - Free online photo editor
2. **Canva.com** - Basic image cropping
3. **GIMP.org** - Download portable version

## Option 4: Browser Extension

Create a simple web version that runs in browser:

1. Open `ttc.html` in any browser
2. Upload images
3. Get composite crops

## Option 5: Mobile App

Future development could create mobile apps:
- iOS App Store version
- Android Play Store version
- No Python required

## Recommendation

**For now: Use `python ttc.py` directly** - it works with any Python version and requires no installation.

**For future: We can create a standalone .exe** using PyInstaller.
