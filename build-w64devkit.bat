@echo off
setlocal enabledelayedexpansion
REM Build ttc using w64devkit

echo Building Test Target Cropper with w64devkit...
echo.

REM Check if w64devkit is available
if not exist "w64devkit\bin\gcc.exe" (
    echo w64devkit not found. Please run install-w64devkit.bat first
    pause
    exit /b 1
)

REM Check if VIPS is installed
if not exist "C:\vips\include\vips\vips.h" (
    echo VIPS headers not found. Please run install-vips.bat first
    pause
    exit /b 1
)

if not exist "C:\vips\lib\libvips.lib" (
    echo VIPS library not found. Please run install-vips.bat first
    pause
    exit /b 1
)

echo Building ttc.exe with w64devkit...

REM Set up PATH for VIPS DLLs
set PATH=C:\vips\bin;!CD!\w64devkit\bin;!PATH!

REM Use the fixed version with proper libraries
w64devkit\bin\gcc.exe -O2 ^
    -I"C:\vips\include" ^
    -I"C:\vips\include\glib-2.0" ^
    -I"C:\vips\lib\glib-2.0\include" ^
    -I"C:\vips\lib\glib-2.0\include\glib-2.0" ^
    -DWIN32 -DMINGW_HAS_SECURE_API ^
    -Wl,--subsystem,console ^
    ttc-fixed.c -o ttc.exe ^
    -L"C:\vips\lib" ^
    -lvips -lglib-2.0 -lgobject-2.0 -lgio-2.0 -lgmodule-2.0 -lpng16 -lz1 -ljpeg -ltiff

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build successful! ttc.exe created.
echo.
echo Testing ttc.exe:
ttc.exe --version
ttc.exe --help

echo.
echo You can now run ttc.exe to process images!
echo Example: ttc.exe .  # Process current directory

pause
