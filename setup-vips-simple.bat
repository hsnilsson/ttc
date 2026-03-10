@echo off
setlocal enabledelayedexpansion
REM Simple VIPS setup script

echo ========================================
echo VIPS Setup (Simple Version)
echo ========================================
echo.

set "version=v8.18.0"
set "downloadUrl=https://github.com/libvips/build-win64-mxe/releases/download/v8.18.0/vips-dev-w64-all-8.18.0.zip"

echo Downloading VIPS !version!...
curl -L -o "vips-dev-w64-all-!version!.zip" "!downloadUrl!"

if not exist "vips-dev-w64-all-!version!.zip" (
    echo ERROR: Download failed
    pause
    exit /b 1
)

echo Download successful!
for %%I in ("vips-dev-w64-all-!version!.zip") do set size=%%~zI
echo File size: !size! bytes

if !size! LSS 1000000 (
    echo ERROR: File too small
    del "vips-dev-w64-all-!version!.zip"
    pause
    exit /b 1
)

echo File size OK
echo.

echo Removing old VIPS...
if exist "C:\vips" rmdir /s /q "C:\vips"

echo Extracting VIPS...
python -c "import zipfile; zipfile.ZipFile('vips-dev-w64-all-!version!.zip').extractall('C:\\')"

if exist "C:\vips\bin\vips.exe" (
    echo VIPS installed successfully!
    C:\vips\bin\vips.exe --version
    del "vips-dev-w64-all-!version!.zip"
    echo.
    echo SUCCESS! You can now build ttc.exe:
    echo   build-w64devkit.bat
) else (
    echo ERROR: Installation failed
)

pause
