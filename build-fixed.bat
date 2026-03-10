@echo off
setlocal enabledelayedexpansion
REM Fixed build script for Test Target Cropper

echo Building Test Target Cropper with fixed PATH...
echo.

REM Check if w64devkit is available
if not exist "w64devkit\bin\gcc.exe" (
    echo w64devkit not found. Please run download-w64devkit.bat first
    pause
    exit /b 1
)

REM Check if VIPS is installed
if not exist "C:\vips\include\vips\vips.h" (
    echo VIPS headers not found. Please run install-vips.bat first
    pause
    exit /b 1
)

if not exist "C:\vips\lib\libvips.lib" (
    echo VIPS library not found. Please run install-vips.bat first
    pause
    exit /b 1
)

echo All dependencies found!
echo.

REM Set up w64devkit environment
set PATH=!CD!\w64devkit\bin;!CD!\w64devkit\x86_64-w64-mingw32\bin;!PATH!

echo Building ttc.exe...
w64devkit\bin\gcc.exe -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0

if errorlevel 1 (
    echo.
    echo Build failed! Trying alternative approach...
    echo.
    
    REM Try with explicit paths
    w64devkit\bin\gcc.exe -O2 -I"C:\vips\include" -I"C:\vips\include\glib-2.0" -I"C:\vips\lib\glib-2.0\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0 -lintl
    
    if errorlevel 1 (
        echo.
        echo Still failed! Let's try with minimal linking...
        w64devkit\bin\gcc.exe -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips
        
        if errorlevel 1 (
            echo.
            echo Build failed completely. Let's check the compiler:
            w64devkit\bin\gcc.exe --version
            echo.
            echo Checking assembler:
            w64devkit\bin\as.exe --version
            echo.
            echo Please check the error messages above.
        ) else (
            echo Build successful with minimal linking!
            goto test
        )
    ) else (
        echo Build successful with alternative approach!
        goto test
    )
) else (
    echo Build successful!
    goto test
)

:test
echo.
echo Testing ttc.exe:
ttc.exe --version
ttc.exe --help

echo.
echo Success! You can now use ttc.exe to process images.
echo Example: ttc.exe .  # Process current directory

pause
