@echo off
setlocal enabledelayedexpansion
REM Download VIPS using multiple methods to avoid corruption

echo ========================================
echo Download VIPS (Reliable Method)
echo ========================================
echo.

echo Removing any existing corrupted VIPS installation...
if exist "C:\vips" (
    rmdir /s /q "C:\vips"
)

echo.
echo Downloading VIPS using curl with retry...
echo This may take a few minutes...

REM Try curl with different options
curl -L --retry 3 --retry-delay 5 -o vips-dev.zip "https://github.com/libvips/libvips/releases/download/v8.18.0/vips-dev-w64-all-8.18.0.zip"

if not exist "vips-dev.zip" (
    echo curl failed, trying PowerShell...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/libvips/libvips/releases/download/v8.18.0/vips-dev-w64-all-8.18.0.zip' -OutFile 'vips-dev.zip' -RetryIntervalSec 5 -MaximumRetryCount 3"
)

if not exist "vips-dev.zip" (
    echo ERROR: Failed to download VIPS
    echo Please check your internet connection
    pause
    exit /b 1
)

echo Download successful!
echo.

echo Checking file integrity...
for %%I in (vips-dev.zip) do set size=%%~zI
echo Downloaded file size: %size% bytes

if %size% LSS 1000000 (
    echo ERROR: Downloaded file is too small (%size% bytes)
    echo File is corrupted, please try again
    del vips-dev.zip
    pause
    exit /b 1
)

echo File size looks good.
echo.

echo Extracting VIPS...
mkdir C:\vips

REM Use Python's zipfile module (more reliable than PowerShell)
python -c "
import zipfile
import sys
try:
    with zipfile.ZipFile('vips-dev.zip', 'r') as zip_ref:
        zip_ref.extractall('C:\\')
    print('VIPS extracted successfully!')
except Exception as e:
    print(f'Extraction failed: {e}')
    sys.exit(1)
"

if errorlevel 1 (
    echo Python extraction failed, trying 7-Zip...
    7z x vips-dev.zip -oC:\ >nul 2>&1
    
    if not exist "C:\vips\bin\vips.exe" (
        echo 7-Zip failed, trying PowerShell...
        powershell -Command "Expand-Archive -Path 'vips-dev.zip' -DestinationPath 'C:\' -Force"
        
        if not exist "C:\vips\bin\vips.exe" (
            echo ERROR: All extraction methods failed
            del vips-dev.zip
            pause
            exit /b 1
        )
    )
)

echo.
echo Testing VIPS installation...
C:\vips\bin\vips.exe --version

if errorlevel 1 (
    echo ERROR: VIPS test failed
    del vips-dev.zip
    pause
    exit /b 1
)

echo.
echo Checking essential files...
if not exist "C:\vips\lib\libvips.lib" (
    echo ERROR: VIPS library missing
    del vips-dev.zip
    pause
    exit /b 1
)

echo.
echo Cleaning up...
del vips-dev.zip

echo.
echo ========================================
echo VIPS Installation Successful!
echo ========================================
echo.
echo Now rebuild ttc.exe:
echo   build-w64devkit.bat
echo.
echo Then test your DNG file:
echo   ./ttc-bash .
echo.

pause
