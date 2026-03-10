@echo off
setlocal enabledelayedexpansion
REM Reinstall VIPS library properly to fix corruption

echo ========================================
echo Reinstalling VIPS Library (Fix Corruption)
echo ========================================
echo.

echo The current VIPS installation shows corruption during extraction.
echo This is likely causing the DNG loading issues.
echo.

echo Removing corrupted VIPS installation...
if exist "C:\vips" (
    echo Removing C:\vips...
    rmdir /s /q "C:\vips"
    if exist "C:\vips" (
        echo ERROR: Could not remove C:\vips directory
        echo Please close any programs using VIPS and try again
        pause
        exit /b 1
    )
    echo Old VIPS installation removed.
) else (
    echo No existing VIPS installation found.
)

echo.
echo Downloading fresh VIPS library...
echo This may take a few minutes...

REM Download VIPS using curl (more reliable than PowerShell)
curl -L -o vips-dev-win64.zip "https://github.com/libvips/libvips/releases/download/v8.18.0/vips-dev-w64-all-8.18.0.zip" 2>nul

if not exist "vips-dev-win64.zip" (
    echo ERROR: Failed to download VIPS
    echo Please check your internet connection
    pause
    exit /b 1
)

echo VIPS downloaded successfully.
echo.

echo Extracting VIPS using 7-Zip (more reliable than PowerShell)...

REM Try 7-Zip first
7z x vips-dev-win64.zip -oC:\ >nul 2>&1

if not errorlevel 1 (
    echo VIPS extracted successfully with 7-Zip.
    goto test_vips
)

REM Fallback to PowerShell if 7-Zip not available
echo 7-Zip not available, trying PowerShell...
powershell -Command "Expand-Archive -Path 'vips-dev-win64.zip' -DestinationPath 'C:\' -Force"

if errorlevel 1 (
    echo ERROR: Failed to extract VIPS
    echo The ZIP file might be corrupted
    pause
    exit /b 1
)

:test_vips
echo.
echo Testing VIPS installation...

if not exist "C:\vips\bin\vips.exe" (
    echo ERROR: VIPS executable not found
    echo Installation failed
    pause
    exit /b 1
)

REM Test VIPS
C:\vips\bin\vips.exe --version

if errorlevel 1 (
    echo ERROR: VIPS test failed
    echo Installation corrupted
    pause
    exit /b 1
)

echo.
echo Checking VIPS library files...

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
echo Cleaning up...
del vips-dev-win64.zip

echo.
echo ========================================
echo VIPS Reinstallation Successful!
echo ========================================
echo.
echo VIPS has been properly installed without corruption.
echo The DNG loading issues should now be resolved.
echo.
echo You can now rebuild ttc.exe:
echo   build-w64devkit.bat
echo.

pause
