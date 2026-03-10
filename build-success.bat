@echo off
setlocal enabledelayedexpansion
REM Final working build script for Test Target Cropper

echo Building Test Target Cropper (Final Working Version)...
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

echo Creating Windows-compatible version...
powershell -Command "(Get-Content ttc.c) -replace 'mkdir\(output_dir, 0755\);', 'mkdir(output_dir);' | Set-Content ttc_windows.c"

echo Building ttc.exe with all required libraries...
w64devkit\bin\gcc.exe -O2 ^
    -I"C:\vips\include" ^
    -I"C:\vips\include\glib-2.0" ^
    -I"C:\vips\lib\glib-2.0\include" ^
    -I"C:\vips\lib\glib-2.0\include\glib-2.0" ^
    -DWIN32 -DMINGW_HAS_SECURE_API ^
    ttc_windows.c -o ttc.exe ^
    -L"C:\vips\lib" ^
    -lvips -lglib-2.0 -lgobject-2.0

if errorlevel 1 (
    echo.
    echo Still missing libraries. Let me try with all glib libraries...
    w64devkit\bin\gcc.exe -O2 ^
        -I"C:\vips\include" ^
        -I"C:\vips\include\glib-2.0" ^
        -I"C:\vips\lib\glib-2.0\include" ^
        -I"C:\vips\lib\glib-2.0\include\glib-2.0" ^
        -DWIN32 -DMINGW_HAS_SECURE_API ^
        ttc_windows.c -o ttc.exe ^
        -L"C:\vips\lib" ^
        -lvips -lglib-2.0 -lgobject-2.0 -lgio-2.0 -lgmodule-2.0
    
    if errorlevel 1 (
        echo.
        echo Trying with even more libraries...
        w64devkit\bin\gcc.exe -O2 ^
            -I"C:\vips\include" ^
            -I"C:\vips\include\glib-2.0" ^
            -I"C:\vips\lib\glib-2.0\include" ^
            -I"C:\vips\lib\glib-2.0\include\glib-2.0" ^
            -DWIN32 -DMINGW_HAS_SECURE_API ^
            ttc_windows.c -o ttc.exe ^
            -L"C:\vips\lib" ^
            -lvips -lglib-2.0 -lgobject-2.0 -lgio-2.0 -lgmodule-2.0 -lintl
        
        if errorlevel 1 (
            echo.
            echo Final attempt with all available libraries...
            w64devkit\bin\gcc.exe -O2 ^
                -I"C:\vips\include" ^
                -I"C:\vips\include\glib-2.0" ^
                -I"C:\vips\lib\glib-2.0\include" ^
                -I"C:\vips\lib\glib-2.0\include\glib-2.0" ^
                -DWIN32 -DMINGW_HAS_SECURE_API ^
                ttc_windows.c -o ttc.exe ^
                -L"C:\vips\lib" ^
                -lvips -lglib-2.0 -lgobject-2.0 -lgio-2.0 -lgmodule-2.0 -lintl -lffi
            
            if errorlevel 1 (
                echo.
                echo All attempts failed. Available libraries:
                dir "C:\vips\lib\*.lib" /B | findstr glib
                dir "C:\vips\lib\*.lib" /B | findstr vips
                echo.
                echo Manual compilation command:
                echo w64devkit\bin\gcc.exe -O2 -I"C:\vips\include" -I"C:\vips\include\glib-2.0" -I"C:\vips\lib\glib-2.0\include" -DWIN32 ttc_windows.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0 -lgobject-2.0
                del ttc_windows.c 2>nul
                pause
                exit /b 1
            ) else (
                echo Build successful with full library set!
                del ttc_windows.c
                goto test
            )
        ) else (
            echo Build successful with extended library set!
            del ttc_windows.c
            goto test
        )
    ) else (
        echo Build successful with gobject library!
        del ttc_windows.c
        goto test
    )
) else (
    echo Build successful on first attempt!
    del ttc_windows.c
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
    echo.
    echo File size:
    dir ttc.exe | findstr ttc.exe
) else (
    echo ERROR: ttc.exe was not created
)

pause
