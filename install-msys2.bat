@echo off
setlocal enabledelayedexpansion
REM Install MSYS2 with GCC

echo ========================================
echo Installing MSYS2 (with GCC)
echo ========================================
echo.

set "downloadUrl=https://github.com/msys2/msys2-installer/releases/download/2023-05-26/msys2-x86_64-20230526.exe"

echo Downloading MSYS2 installer...
curl -L -o "msys2-installer.exe" "%downloadUrl%"

if not exist "msys2-installer.exe" (
    echo ERROR: Failed to download MSYS2
    pause
    exit /b 1
)

echo.
echo MSYS2 downloaded successfully!
echo.
echo IMPORTANT: You need to run the installer manually:
echo 1. Double-click: msys2-installer.exe
echo 2. Install to: C:\msys64
echo 3. After installation, run these commands in MSYS2:
echo    pacman -Syu
echo    pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-libraw
echo.
echo Then run: build-with-msys2.bat

pause
