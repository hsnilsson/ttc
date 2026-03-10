@echo off
setlocal enabledelayedexpansion
REM Final Release Build Script for Test Target Cropper (C Version)
REM This script creates the production-ready ttc.exe

echo ========================================
echo Building Test Target Cropper (C Version)
echo ========================================
echo.

REM Check dependencies
echo Checking dependencies...

if not exist "w64devkit\bin\gcc.exe" (
    echo ERROR: w64devkit not found
    echo Please run: download-w64devkit.bat
    pause
    exit /b 1
)

if not exist "C:\vips\include\vips\vips.h" (
    echo ERROR: VIPS not found
    echo Please run: install-vips.bat
    pause
    exit /b 1
)

echo All dependencies found!
echo.

REM Set up environment
set PATH=C:\vips\bin;!CD!\w64devkit\bin;!PATH!

echo Building ttc.exe (Production Version)...

REM Create Windows-compatible version
powershell -Command "(Get-Content ttc-fixed.c) -replace 'mkdir\(output_dir\);', 'mkdir(output_dir);' | Set-Content ttc_release.c"

REM Build with optimizations
w64devkit\bin\gcc.exe -O3 ^
    -I"C:\vips\include" ^
    -I"C:\vips\include\glib-2.0" ^
    -I"C:\vips\lib\glib-2.0\include" ^
    -I"C:\vips\lib\glib-2.0\include\glib-2.0" ^
    -DWIN32 -DMINGW_HAS_SECURE_API ^
    -Wl,--subsystem,console ^
    -Wl,--strip-all ^
    ttc_release.c -o ttc.exe ^
    -L"C:\vips\lib" ^
    -lvips -lglib-2.0 -lgobject-2.0

if errorlevel 1 (
    echo ERROR: Build failed!
    del ttc_release.c 2>nul
    pause
    exit /b 1
)

del ttc_release.c

echo.
echo ========================================
echo Build Successful!
echo ========================================
echo.

echo Testing ttc.exe...
echo.

REM Test the executable
ttc.exe --version
echo.
ttc.exe --help
echo.

echo File information:
dir ttc.exe | findstr ttc.exe

echo.
echo ========================================
echo Installation Instructions
echo ========================================
echo.
echo 1. Copy ttc.exe to your desired location
echo 2. Ensure C:\vips\bin is in your PATH
echo    OR copy required VIPS DLLs to the same directory
echo.
echo Required VIPS DLLs:
echo   - libvips-42.dll
echo   - libglib-2.0-0.dll  
echo   - libgobject-2.0-0.dll
echo   - (and dependencies)
echo.
echo Usage:
echo   ttc.exe                    # Process current directory
echo   ttc.exe --help             # Show help
echo   ttc.exe --version          # Show version
echo.

echo ========================================
echo Build Complete! Ready for Release
echo ========================================

pause
