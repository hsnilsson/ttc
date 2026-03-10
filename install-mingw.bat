@echo off
REM Install MinGW-w64 for Windows
REM Downloads and sets up MinGW-w64 for C compilation

echo Installing MinGW-w64 for Test Target Cropper...
echo.

REM Check if MinGW is already in PATH
gcc --version >nul 2>&1
if errorlevel 1 (
    echo MinGW not found in PATH
) else (
    echo MinGW already available!
    gcc --version
    echo.
    echo You can now build ttc using:
    echo   gcc -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0
    pause
    exit /b 0
)

echo Downloading MinGW-w64...
curl -L -o mingw-w64.zip "https://github.com/niXman/mingw-builds-autoinstall/releases/download/13.2.0-rt_v11-rev1/mingw-w64-x86_64-13.2.0-release-posix-seh-rt_v11-rev1.7z" 2>nul

if not exist "mingw-w64.zip" (
    echo.
    echo Automatic download failed. Please install MinGW-w64 manually:
    echo.
    echo 1. Go to: https://www.mingw-w64.org/downloads/
    echo 2. Download MinGW-w64 for x86_64, posix threads, seh exceptions
    echo 3. Extract to C:\mingw64
    echo 4. Add C:\mingw64\bin to your PATH
    echo.
    pause
    exit /b 1
)

echo Extracting MinGW-w64...
REM Use 7z if available, else show manual instructions
7z x mingw-w64.zip -oC:\ >nul 2>&1

if errorlevel 1 (
    echo.
    echo 7z not available. Please extract mingw-w64.zip manually to C:\mingw64
    echo Then add C:\mingw64\bin to your PATH
    pause
    exit /b 1
)

echo Cleaning up...
del mingw-w64.zip

REM Add MinGW to PATH for current session
set PATH=%PATH%;C:\mingw64\bin

echo Testing MinGW installation...
gcc --version

if errorlevel 1 (
    echo.
    echo MinGW installation failed or not in PATH.
    echo Please check that C:\mingw64\bin\gcc.exe exists.
    pause
    exit /b 1
)

echo.
echo MinGW installation successful!
echo.
echo You can now build ttc using:
echo   gcc -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0
echo.

pause
