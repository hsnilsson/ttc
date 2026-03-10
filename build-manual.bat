@echo off
echo Manual build instructions for Test Target Cropper
echo.

echo Step 1: Download w64devkit
echo   1. Open: https://github.com/skeeto/w64devkit/releases/latest
echo   2. Download: w64devkit-v1.2.0.zip (or latest)
echo   3. Extract to this folder (creates w64devkit\ folder)
echo.

echo Step 2: Check VIPS installation
if exist "C:\vips\include\vips\vips.h" (
    echo   VIPS headers: FOUND
) else (
    echo   VIPS headers: NOT FOUND - run install-vips.bat first
)

if exist "C:\vips\lib\vips.lib" (
    echo   VIPS library: FOUND
) else (
    echo   VIPS library: NOT FOUND - run install-vips.bat first
)

echo.

echo Step 3: Build when ready
if exist "w64devkit\bin\gcc.exe" (
    echo   Building ttc.exe...
    w64devkit\bin\gcc.exe -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0
    
    if not errorlevel 1 (
        echo   Build successful!
        echo.
        echo   Testing ttc.exe:
        ttc.exe --version
        ttc.exe --help
    ) else (
        echo   Build failed!
    )
) else (
    echo   w64devkit not found yet.
    echo   Please download and extract w64devkit first.
)

echo.
pause
