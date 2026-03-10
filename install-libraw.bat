@echo off
setlocal enabledelayedexpansion
REM Install libraw for Windows

echo ========================================
echo Installing libraw
echo ========================================
echo.

set "version=0.21.2"
set "downloadUrl=https://github.com/LibRaw/LibRaw/releases/download/%version%/LibRaw-%version%-win.zip"

echo Downloading libraw %version%...
echo.

REM Remove any existing libraw
if exist "C:\libraw" (
    echo Removing existing libraw...
    rmdir /s /q "C:\libraw"
)

REM Download libraw
echo Downloading from: %downloadUrl%
curl -L --retry 3 --retry-delay 10 --show-error -o "libraw-%version%-win.zip" "%downloadUrl%"

if not exist "libraw-%version%-win.zip" (
    echo ERROR: Failed to download libraw
    echo.
    echo Manual download required:
    echo 1. Visit: https://github.com/LibRaw/LibRaw/releases/tag/%version%
    echo 2. Download: LibRaw-%version%-win.zip
    echo 3. Save to: %CD%
    echo 4. Run this script again
    pause
    exit /b 1
)

echo.
echo Download successful!
echo.

echo Extracting libraw...
powershell -Command "Expand-Archive -Path 'libraw-%version%-win.zip' -DestinationPath 'C:\' -Force"

if not exist "C:\libraw\include\libraw\libraw.h" (
    echo ERROR: libraw installation failed
    echo Could not find: C:\libraw\include\libraw\libraw.h
    pause
    exit /b 1
)

echo.
echo libraw installed successfully!
echo.

echo Verifying installation...
if exist "C:\libraw\lib\raw.lib" (
    echo Found: C:\libraw\lib\raw.lib
) else (
    echo WARNING: raw.lib not found, trying raw_r.lib
    if exist "C:\libraw\lib\raw_r.lib" (
        echo Found: C:\libraw\lib\raw_r.lib
    ) else (
        echo ERROR: No libraw library files found
        pause
        exit /b 1
    )
)

echo.
echo Cleaning up...
del "libraw-%version%-win.zip"

echo.
echo SUCCESS! libraw %version% has been installed to C:\libraw
echo.
echo Next steps:
echo 1. Build ttc-libraw.exe:    build-libraw.bat
echo 2. Test with DNG:           ttc-libraw.exe .
echo.

pause
