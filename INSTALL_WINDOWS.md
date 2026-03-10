# Windows Installation Guide for Test Target Cropper (C Version)

## Quick Install Options

### Option 1: Visual Studio Build Tools (Recommended)
1. Download Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio
2. Run the installer
3. Select "C++ build tools" and check these components:
   - MSVC v143 - VS 2022 C++ x64/x86 build tools
   - Windows 10/11 SDK (latest)
4. Complete installation
5. Run `build.bat` in this directory

### Option 2: MinGW-w64
1. Download MinGW-w64: https://www.mingw-w64.org/downloads/
2. Get the x86_64-posix-seh version
3. Extract to `C:\mingw64`
4. Add `C:\mingw64\bin` to your PATH:
   - Press Win + R, type `sysdm.cpl`
   - Go to Advanced → Environment Variables
   - Edit PATH, add `C:\mingw64\bin`
5. Restart PowerShell/CMD
6. Run: `gcc -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0`

### Option 3: WSL (Windows Subsystem for Linux)
1. Install WSL: `wsl --install`
2. Open WSL terminal
3. Install dependencies: `sudo apt update && sudo apt install libvips-dev pkg-config gcc`
4. Build: `gcc -O2 $(pkg-config --cflags vips) ttc.c -o ttc $(pkg-config --libs vips)`

## Step-by-Step Setup

### 1. Install VIPS (Already Done!)
✅ VIPS is installed at `C:\vips`

### 2. Install C Compiler
Choose one of the options above.

### 3. Build the Application
```cmd
# With Visual Studio:
build.bat

# With MinGW:
gcc -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0

# Test the executable:
ttc.exe --version
ttc.exe --help
```

### 4. Test with Sample Data
```cmd
ttc.exe .  # Process current directory
```

## Troubleshooting

### "vips.h not found"
- Ensure VIPS is installed at `C:\vips`
- Check that `C:\vips\include\vips\vips.h` exists

### "Cannot find vips.lib"
- Ensure `C:\vips\lib\vips.lib` exists
- Update library path in build command

### "gcc not recognized"
- Add MinGW to PATH as described in Option 2
- Or use Visual Studio Build Tools

### "cl not recognized"
- Run `build.bat` (it sets up the environment)
- Or manually run VS Developer Command Prompt

## Verification
After installation, test with:
```cmd
ttc.exe --version
# Should output: Test Target Cropper 1.2.0

ttc.exe --help
# Should show usage instructions
```

## Next Steps
Once built, you can:
1. Test with actual image files
2. Compare output with Python version
3. Create a release build for distribution
