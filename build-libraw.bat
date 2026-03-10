@echo off
setlocal enabledelayedexpansion
REM Build Test Target Cropper with libraw and stb_image

echo ========================================
echo Building TTC with libraw + stb_image
echo ========================================
echo.

REM Check for w64devkit
if not exist "w64devkit\bin\gcc.exe" (
    echo ERROR: w64devkit not found!
    echo Please run: install-w64devkit.bat
    pause
    exit /b 1
)

REM Check for libraw
if not exist "C:\libraw\include\libraw\libraw.h" (
    echo ERROR: libraw not found!
    echo Download libraw from: https://www.libraw.org/download
    echo Extract to C:\libraw
    pause
    exit /b 1
)

echo Building ttc-libraw.exe...
echo.

REM Add compiler to PATH
set PATH=%CD%\w64devkit\bin;%PATH%

REM Build with libraw and stb_image
w64devkit\bin\gcc.exe -O2 ^
    -I"C:\libraw\include" ^
    -DLIBRAW_BUILDLIB ^
    -DWIN32 -DMINGW_HAS_SECURE_API ^
    -Wl,--subsystem,console ^
    ttc-libraw.c -o ttc-libraw.exe ^
    -L"C:\libraw\lib" ^
    -lraw -lstdc++ -lws2_32

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build successful! ttc-libraw.exe created.
echo.

if exist "ttc-libraw.exe" (
    echo Testing ttc-libraw.exe:
    ttc-libraw.exe --help
    echo.
    echo You can now run ttc-libraw.exe to process images
    echo Example: ttc-libraw.exe .  # Process current directory
)

pause
