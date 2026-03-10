@echo off
setlocal enabledelayedexpansion
REM Manual VIPS installation to fix corruption issues

echo ========================================
echo Manual VIPS Installation
echo ========================================
echo.

echo The automatic VIPS download is corrupted.
echo This script will guide you through manual installation.
echo.

echo Step 1: Download VIPS Manually
echo ==============================
echo.
echo Please open this URL in your browser:
echo https://github.com/libvips/libvips/releases/download/v8.18.0/vips-dev-w64-all-8.18.0.zip
echo.
echo Download the file and save it as: vips-dev-w64-all-8.18.0.zip
echo Place it in the current directory: %CD%
echo.

if not exist "vips-dev-w64-all-8.18.0.zip" (
    echo Waiting for you to download the file...
    echo.
    echo Once downloaded, press any key to continue...
    pause
)

if not exist "vips-dev-w64-all-8.18.0.zip" (
    echo ERROR: vips-dev-w64-all-8.18.0.zip not found
    echo Please download the file first
    pause
    exit /b 1
)

echo.
echo Step 2: Remove Old VIPS Installation
echo =====================================
if exist "C:\vips" (
    echo Removing old VIPS installation...
    rmdir /s /q "C:\vips"
)

echo.
echo Step 3: Extract VIPS
echo ===================
echo Extracting VIPS to C:\...

REM Try multiple extraction methods
echo Trying 7-Zip extraction...
7z x vips-dev-w64-all-8.18.0.zip -oC:\ >nul 2>&1

if exist "C:\vips\bin\vips.exe" (
    echo VIPS extracted successfully with 7-Zip!
    goto test_installation
)

echo 7-Zip failed, trying tar...
tar -xf vips-dev-w64-all-8.18.0.zip -C C:\

if exist "C:\vips\bin\vips.exe" (
    echo VIPS extracted successfully with tar!
    goto test_installation
)

echo tar failed, trying PowerShell...
powershell -Command "Expand-Archive -Path 'vips-dev-w64-all-8.18.0.zip' -DestinationPath 'C:\' -Force"

if exist "C:\vips\bin\vips.exe" (
    echo VIPS extracted successfully with PowerShell!
    goto test_installation
)

echo.
echo ERROR: All extraction methods failed
echo The ZIP file might be corrupted
echo Please try downloading it again
pause
exit /b 1

:test_installation
echo.
echo Step 4: Test VIPS Installation
echo ==============================
echo Testing VIPS...

C:\vips\bin\vips.exe --version

if errorlevel 1 (
    echo ERROR: VIPS test failed
    pause
    exit /b 1
)

echo.
echo Checking library files...

if not exist "C:\vips\lib\libvips.lib" (
    echo ERROR: VIPS library not found
    pause
    exit /b 1
)

if not exist "C:\vips\include\vips\vips.h" (
    echo ERROR: VIPS headers not found
    pause
    exit /b 1
)

echo.
echo Step 5: Clean Up
echo ==============
del vips-dev-w64-all-8.18.0.zip

echo.
echo ========================================
echo VIPS Manual Installation Complete!
echo ========================================
echo.
echo VIPS has been properly installed.
echo Now rebuild ttc.exe:
echo.
echo   build-w64devkit.bat
echo.
echo Then test with your DNG file:
echo.
echo   ./ttc-bash .
echo.

pause
