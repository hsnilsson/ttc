@echo off
setlocal enabledelayedexpansion
REM Build Test Target Cropper with stb_image (simple version)

echo ========================================
echo Building TTC with stb_image
echo ========================================
echo.

REM Check for w64devkit compiler
if not exist "w64devkit\bin\gcc.exe" (
    echo ERROR: w64devkit not found!
    echo Please run: download-w64devkit-7z.ps1
    pause
    exit /b 1
)

REM Check for stb headers
if not exist "stb_image.h" (
    echo ERROR: stb_image.h not found!
    echo Please run: install-stb.bat
    pause
    exit /b 1
)

if not exist "stb_image_write.h" (
    echo ERROR: stb_image_write.h not found!
    echo Please run: install-stb.bat
    pause
    exit /b 1
)

echo Building ttc-simple.exe with DNG support...
echo.

REM Add compiler to PATH
set PATH=%CD%\w64devkit\bin;%PATH%

REM Build with w64devkit and libraw
w64devkit\bin\gcc.exe -O2 ^
    -I"C:\libraw\include" ^
    -DLIBRAW_BUILDLIB ^
    -DWIN32 -DMINGW_HAS_SECURE_API ^
    -Wl,--subsystem,console ^
    ttc-simple.c -o ttc-simple.exe ^
    -L"C:\libraw\lib" ^
    -lraw -lstdc++ -lws2_32

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build successful! ttc-simple.exe created.
echo.

if exist "ttc-simple.exe" (
    echo Testing ttc-simple.exe:
    ttc-simple.exe --help
    echo.
    echo You can now run ttc-simple.exe to process images
    echo Example: ttc-simple.exe .  # Process current directory
    echo.
    echo Note: This version supports PNG, JPG, BMP, GIF, DNG, etc.
    echo DNG files are processed using libraw for full resolution support.
)

pause
