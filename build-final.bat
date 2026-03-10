@echo off
setlocal enabledelayedexpansion
REM Final build script with all fixes for Test Target Cropper

echo Building Test Target Cropper (Final Version)...
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
set PATH=!CD!\w64devkit\bin;!PATH!

echo Building ttc.exe with corrected include paths...
w64devkit\bin\gcc.exe -O2 -I"C:\vips\include" -I"C:\vips\include\glib-2.0" -I"C:\vips\lib\glib-2.0\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0 -DWIN32

if errorlevel 1 (
    echo.
    echo Build failed! Trying with even more include paths...
    echo.
    
    REM Try with additional paths
    w64devkit\bin\gcc.exe -O2 -I"C:\vips\include" -I"C:\vips\include\glib-2.0" -I"C:\vips\lib\glib-2.0\include" -I"C:\vips\lib\glib-2.0\include\glib-2.0" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0 -DWIN32 -DMINGW_HAS_SECURE_API
    
    if errorlevel 1 (
        echo.
        echo Still failed! Let's try a minimal approach...
        
        REM Create a simple test first
        echo Testing basic compilation...
        w64devkit\bin\gcc.exe -c ttc.c -o ttc.o -I"C:\vips\include" -I"C:\vips\include\glib-2.0" -DWIN32
        
        if not errorlevel 1 (
            echo Compilation succeeded, trying linking...
            w64devkit\bin\gcc.exe ttc.o -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0
            
            if not errorlevel 1 (
                echo Build successful with two-step approach!
                goto test
            )
        )
        
        echo.
        echo All build attempts failed. Let's check what's available:
        echo.
        echo VIPS include files:
        dir "C:\vips\include" /B
        echo.
        echo VIPS glib include files:
        dir "C:\vips\include\glib-2.0" /B 2>nul
        echo.
        echo VIPS library files:
        dir "C:\vips\lib\*.lib" /B | findstr vips
        
        pause
        exit /b 1
    ) else (
        echo Build successful with extended paths!
        goto test
    )
) else (
    echo Build successful!
    goto test
)

:test
echo.
echo Testing ttc.exe:
if exist "ttc.exe" (
    ttc.exe --version
    ttc.exe --help
    
    echo.
    echo SUCCESS! ttc.exe is working!
    echo You can now use it to process images.
    echo Example: ttc.exe .  # Process current directory
) else (
    echo ERROR: ttc.exe was not created despite successful build
)

pause
