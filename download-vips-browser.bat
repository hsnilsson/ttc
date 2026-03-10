@echo off
REM Open browser to download VIPS manually

echo ========================================
echo Download VIPS Manually via Browser
echo ========================================
echo.

echo Opening download page in your browser...
echo.

REM Open the GitHub releases page
start https://github.com/libvips/libvips/releases/download/v8.18.0/vips-dev-w64-all-8.18.0.zip

echo.
echo The download should start automatically.
echo.
echo INSTRUCTIONS:
echo ============
echo 1. Save the downloaded file as: vips-dev-w64-all-8.18.0.zip
echo 2. Place it in this directory: %CD%
echo 3. Run: install-vips-from-zip.bat
echo.

echo The file should be around 50-100 MB in size.
echo If it's only a few KB, the download failed.
echo.

echo Waiting for download...
echo Once downloaded, press any key to continue...
pause

if not exist "vips-dev-w64-all-8.18.0.zip" (
    echo ERROR: vips-dev-w64-all-8.18.0.zip not found
    echo Please download the file first
    pause
    exit /b 1
)

echo.
echo File found! Running installation...
call install-vips-from-zip.bat
