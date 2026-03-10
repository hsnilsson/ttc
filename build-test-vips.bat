@echo off
setlocal enabledelayedexpansion
set PATH=C:\vips\bin;!CD!\w64devkit\bin;!PATH!

w64devkit\bin\gcc.exe -I"C:\vips\include" -I"C:\vips\include\glib-2.0" -I"C:\vips\lib\glib-2.0\include" test-vips-env.c -o test-vips-env.exe -L"C:\vips\lib" -lvips -lglib-2.0 -lgobject-2.0 -lpng16 -lz1

if not errorlevel 1 (
    echo Build successful!
    test-vips-env.exe
) else (
    echo Build failed
)

pause
