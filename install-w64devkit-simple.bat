@echo off
setlocal enabledelayedexpansion
REM Simple w64devkit installation with manual download instructions

echo Installing w64devkit for Test Target Cropper...
echo.

REM Check if w64devkit is already available
if exist "w64devkit\bin\gcc.exe" (
    echo w64devkit already available!
    w64devkit\bin\gcc.exe --version | findstr "gcc"
    echo.
    echo Building ttc.exe...
    w64devkit\bin\gcc.exe -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0
    
    if not errorlevel 1 (
        echo.
        echo Build successful! ttc.exe created.
        ttc.exe --version
        ttc.exe --help
    )
    pause
    exit /b 0
)

echo w64devkit not found. Please download manually:
echo.
echo 1. Open browser and go to: https://github.com/skeeto/w64devkit/releases
echo 2. Download: w64devkit-v1.2.0.zip
echo 3. Extract the zip file to this folder (should create w64devkit\ folder)
echo 4. Run this script again
echo.
echo Alternative: Use PowerShell to download:
echo powershell -Command "Invoke-WebRequest -Uri 'https://github.com/skeeto/w64devkit/releases/download/v1.2.0/w64devkit-v1.2.0.zip' -OutFile 'w64devkit.zip'"
echo powershell -Command "Expand-Archive -Path 'w64devkit.zip' -DestinationPath '.'"
echo.

pause
