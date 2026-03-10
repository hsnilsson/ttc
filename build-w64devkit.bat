@echo off
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

if not exist "C:\vips\lib\vips.lib" (
    echo VIPS library not found. Please run install-vips.bat first
    pause
    exit /b 1
)

echo Building ttc.exe...
w64devkit\bin\gcc.exe -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0

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
