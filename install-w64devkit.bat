@echo off
setlocal enabledelayedexpansion
REM Install w64devkit C compiler

echo ========================================
echo Installing w64devkit
echo ========================================
echo.

set "downloadUrl=https://github.com/skeeto/w64devkit/releases/download/v1.2.0/w64devkit-1.2.0.tar.gz"

echo Downloading w64devkit...
echo.

REM Download w64devkit using curl
curl -L -H "Accept: application/octet-stream" -o "w64devkit.tar.gz" "%downloadUrl%"

if not exist "w64devkit.tar.gz" (
    echo ERROR: Failed to download w64devkit
    echo Trying manual download...
    echo Please visit: https://github.com/skeeto/w64devkit/releases/tag/v1.2.0
    echo Download: w64devkit-1.2.0.tar.gz
    echo Save to: %CD%
    pause
    exit /b 1
)

echo.
echo Download successful!
echo.

echo Extracting w64devkit...
tar -xf "w64devkit.tar.gz"

if not exist "w64devkit\bin\gcc.exe" (
    echo ERROR: w64devkit installation failed
    echo Checking what was extracted...
    dir /b
    pause
    exit /b 1
)

echo.
echo w64devkit installed successfully!
echo.

echo Testing compiler...
w64devkit\bin\gcc.exe --version

echo.
echo Cleaning up...
del "w64devkit.tar.bz2"

echo.
echo SUCCESS! w64devkit has been installed
echo.

pause
