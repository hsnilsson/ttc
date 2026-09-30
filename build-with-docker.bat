@echo off
setlocal enabledelayedexpansion
REM Build using Docker with GCC and libraw

echo ========================================
echo Building with Docker (GCC + libraw)
echo ========================================
echo.

REM Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found!
    echo Please install Docker Desktop
    pause
    exit /b 1
)

REM Check if source files exist
if not exist "ttc-simple.c" (
    echo ERROR: ttc-simple.c not found!
    pause
    exit /b 1
)

if not exist "stb_image.h" (
    echo ERROR: stb_image.h not found!
    echo Please run: install-stb.bat
    pause
    exit /b 1
)

echo Building Docker image...
docker build -t ttc-builder .

if errorlevel 1 (
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)

echo.
echo Extracting executable from Docker container...
docker run --rm -v "%CD%:/output" ttc-builder cp /app/ttc-simple.exe /output/

if exist "ttc-simple.exe" (
    echo.
    echo SUCCESS! ttc-simple.exe created with DNG support!
    echo.
    
    echo Testing executable:
    ttc-simple.exe --help
    
) else (
    echo ERROR: Failed to extract executable
)

echo.
echo Build complete!

pause
