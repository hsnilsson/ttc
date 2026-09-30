@echo off
setlocal enabledelayedexpansion
REM Download stb_image header-only library

echo ========================================
echo Installing stb_image
echo ========================================
echo.

echo Downloading stb_image.h...
curl -L -o "stb_image.h" "https://raw.githubusercontent.com/nothings/stb/master/stb_image.h"

if not exist "stb_image.h" (
    echo ERROR: Failed to download stb_image.h
    pause
    exit /b 1
)

echo Downloading stb_image_write.h...
curl -L -o "stb_image_write.h" "https://raw.githubusercontent.com/nothings/stb/master/stb_image_write.h"

if not exist "stb_image_write.h" (
    echo ERROR: Failed to download stb_image_write.h
    pause
    exit /b 1
)

echo.
echo SUCCESS! stb libraries downloaded
echo.

pause
