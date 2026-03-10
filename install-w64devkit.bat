@echo off
setlocal enabledelayedexpansion
REM Install w64devkit - Portable C/C++ Development Kit for Windows
REM Downloads and sets up w64devkit for Test Target Cropper

echo Installing w64devkit for Test Target Cropper...
echo.

REM Check if w64devkit is already available
if exist "w64devkit\bin\gcc.exe" (
    echo w64devkit already available!
    w64devkit\bin\gcc.exe --version | findstr "gcc"
    echo.
    echo You can now build ttc using:
    echo   w64devkit\bin\gcc.exe -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0
    echo.
    echo Or add to PATH permanently:
    echo   set PATH=!PATH!;!CD!\w64devkit\bin
    pause
    exit /b 0
) else (
    echo w64devkit not found
)

echo Downloading w64devkit...
curl -L -o w64devkit.zip "https://github.com/skeeto/w64devkit/releases/download/v1.2.0/w64devkit-v1.2.0.zip"

if not exist "w64devkit.zip" (
    echo.
    echo Download failed. Please download manually:
    echo 1. Go to: https://github.com/skeeto/w64devkit/releases
    echo 2. Download w64devkit-v1.2.0.zip
    echo 3. Extract to w64devkit\ folder
    pause
    exit /b 1
)

echo Extracting w64devkit...
powershell -Command "Expand-Archive -Path 'w64devkit.zip' -DestinationPath '.' -Force"

if errorlevel 1 (
    echo Extraction failed. Please extract w64devkit.zip manually to w64devkit\ folder
    pause
    exit /b 1
)

echo Cleaning up...
del w64devkit.zip

echo Testing w64devkit installation...
w64devkit\bin\gcc.exe --version

if errorlevel 1 (
    echo.
    echo w64devkit installation failed.
    echo Please check that w64devkit\bin\gcc.exe exists.
    pause
    exit /b 1
)

echo.
echo w64devkit installation successful!
echo.
echo Building ttc.exe...
w64devkit\bin\gcc.exe -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0

if errorlevel 1 (
    echo.
    echo Build failed. Checking VIPS installation...
    if exist "C:\vips\include\vips\vips.h" (
        echo VIPS headers found
    ) else (
        echo ERROR: VIPS headers not found at C:\vips\include\vips\vips.h
        echo Please run install-vips.bat first
    )
    
    if exist "C:\vips\lib\vips.lib" (
        echo VIPS library found
    ) else (
        echo ERROR: VIPS library not found at C:\vips\lib\vips.lib
        echo Please run install-vips.bat first
    )
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
echo To use w64devkit in future, add to PATH:
echo   set PATH=!PATH!;!CD!\w64devkit\bin
echo.
echo Or run: w64devkit\bin\gcc.exe directly

pause
