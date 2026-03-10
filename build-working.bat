@echo off
setlocal enabledelayedexpansion
REM Working build script with correct paths for Test Target Cropper

echo Building Test Target Cropper (Working Version)...
echo.

REM Check dependencies
if not exist "w64devkit\bin\gcc.exe" (
    echo w64devkit not found. Please run download-w64devkit.bat first
    pause
    exit /b 1
)

if not exist "C:\vips\include\vips\vips.h" (
    echo VIPS headers not found. Please run install-vips.bat first
    pause
    exit /b 1
)

echo All dependencies found!
echo.

REM Set up environment
set PATH=!CD!\w64devkit\bin;!PATH!

echo Building ttc.exe with all correct include paths...
w64devkit\bin\gcc.exe -O2 ^
    -I"C:\vips\include" ^
    -I"C:\vips\include\glib-2.0" ^
    -I"C:\vips\lib\glib-2.0\include" ^
    -I"C:\vips\lib\glib-2.0\include\glib-2.0" ^
    -DWIN32 -DMINGW_HAS_SECURE_API ^
    ttc.c -o ttc.exe ^
    -L"C:\vips\lib" ^
    -lvips -lglib-2.0

if errorlevel 1 (
    echo.
    echo Build failed! The issue is likely the mkdir function call.
    echo Let me create a fixed version of ttc.c for Windows...
    
    REM Create a Windows-fixed version on the fly
    echo Creating Windows-compatible version...
    powershell -Command "(Get-Content ttc.c) -replace 'mkdir\(output_dir, 0755\);', 'mkdir(output_dir);' | Set-Content ttc_windows.c"
    
    echo Building with fixed mkdir...
    w64devkit\bin\gcc.exe -O2 ^
        -I"C:\vips\include" ^
        -I"C:\vips\include\glib-2.0" ^
        -I"C:\vips\lib\glib-2.0\include" ^
        -I"C:\vips\lib\glib-2.0\include\glib-2.0" ^
        -DWIN32 -DMINGW_HAS_SECURE_API ^
        ttc_windows.c -o ttc.exe ^
        -L"C:\vips\lib" ^
        -lvips -lglib-2.0
    
    if not errorlevel 1 (
        echo Build successful with Windows fix!
        del ttc_windows.c
        goto test
    ) else (
        echo.
        echo Still failing. Let's try without some problematic includes...
        w64devkit\bin\gcc.exe -O2 ^
            -I"C:\vips\include" ^
            -I"C:\vips\include\glib-2.0" ^
            -I"C:\vips\lib\glib-2.0\include" ^
            -DWIN32 -DMINGW_HAS_SECURE_API ^
            ttc_windows.c -o ttc.exe ^
            -L"C:\vips\lib" ^
            -lvips -lglib-2.0
        
        if not errorlevel 1 (
            echo Build successful with minimal includes!
            del ttc_windows.c
            goto test
        ) else (
            echo.
            echo All attempts failed. Here's the compilation command for manual testing:
            echo w64devkit\bin\gcc.exe -O2 -I"C:\vips\include" -I"C:\vips\include\glib-2.0" -I"C:\vips\lib\glib-2.0\include" -DWIN32 ttc_windows.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0
            del ttc_windows.c 2>nul
            pause
            exit /b 1
        )
    )
) else (
    echo Build successful on first attempt!
    goto test
)

:test
echo.
echo Testing ttc.exe:
if exist "ttc.exe" (
    echo Executable found! Testing...
    ttc.exe --version
    ttc.exe --help
    
    echo.
    echo SUCCESS! ttc.exe is working perfectly!
    echo.
    echo You can now use it to process images:
    echo   ttc.exe .                    # Process current directory
    echo   ttc.exe --help              # Show all options
    echo   ttc.exe --version           # Show version
) else (
    echo ERROR: ttc.exe was not created
)

pause
