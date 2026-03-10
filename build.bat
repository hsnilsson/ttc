@echo off
REM Build script for Test Target Cropper on Windows
REM Requires Visual Studio Build Tools or Visual Studio with C++ tools

echo Setting up Visual Studio environment...
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" 2>nul
if errorlevel 1 (
    call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" 2>nul
    if errorlevel 1 (
        call "C:\Program Files\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat" 2>nul
        if errorlevel 1 (
            echo ERROR: Visual Studio Build Tools not found!
            echo Please install Visual Studio Build Tools with C++ tools
            echo Or install MinGW-w64 for gcc
            pause
            exit /b 1
        )
    )
)

echo Building ttc.exe...
cl /EHsc /O2 /I"C:\vips\include" ttc.c /link /LIBPATH:"C:\vips\lib" vips.lib glib-2.0.lib /out:ttc.exe

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo Build successful! ttc.exe created.
echo.
echo Testing ttc.exe:
ttc.exe --version
ttc.exe --help

pause
