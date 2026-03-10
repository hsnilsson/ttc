@echo off
REM Install VIPS library for Windows
REM Downloads and extracts VIPS to C:\vips

echo Installing VIPS library for Test Target Cropper...
echo.

REM Check if VIPS is already installed
if exist "C:\vips\bin\vips-8.dll" (
    echo VIPS already installed at C:\vips
    echo.
    echo Testing VIPS installation...
    C:\vips\bin\vips.exe --version
    if errorlevel 1 (
        echo VIPS installation found but not working properly.
        echo Continuing with reinstallation...
    ) else (
        echo VIPS installation verified!
        echo You can now build ttc using build.bat
        pause
        exit /b 0
    )
)

echo Downloading VIPS...
REM Download VIPS Windows binary (using curl if available, else show manual instructions)
curl -L -o vips-dev-win.zip "https://github.com/libvips/libvips/releases/download/v8.15.1/vips-dev-win-x64-8.15.1.zip" 2>nul

if not exist "vips-dev-win.zip" (
    echo.
    echo Automatic download failed. Please install VIPS manually:
    echo.
    echo 1. Go to: https://github.com/libvips/libvips/releases
    echo 2. Download the latest "vips-dev-win-x64" zip file
    echo 3. Extract it to C:\vips
    echo 4. Run this script again to verify installation
    echo.
    pause
    exit /b 1
)

echo Extracting VIPS to C:\vips...
powershell -Command "Expand-Archive -Path 'vips-dev-win.zip' -DestinationPath 'C:\vips' -Force"

if errorlevel 1 (
    echo Extraction failed! Please extract manually to C:\vips
    pause
    exit /b 1
)

echo Cleaning up...
del vips-dev-win.zip

REM Add VIPS to PATH for current session
set PATH=%PATH%;C:\vips\bin

echo Testing VIPS installation...
C:\vips\bin\vips.exe --version

if errorlevel 1 (
    echo.
    echo VIPS installation failed or incomplete.
    echo Please check that C:\vips\bin\vips.exe exists and works.
    pause
    exit /b 1
)

echo.
echo VIPS installation successful!
echo.
echo You can now build ttc using:
echo   build.bat
echo.
echo Or manually:
echo   gcc -O2 -I"C:\vips\include" ttc.c -o ttc.exe -L"C:\vips\lib" -lvips -lglib-2.0
echo.

pause
