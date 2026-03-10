@echo off
setlocal enabledelayedexpansion
REM Complete development setup script for Test Target Cropper

echo ========================================
echo Test Target Cropper - Development Setup
echo ========================================
echo.

echo This script sets up the complete development environment
echo for the Test Target Cropper C implementation.
echo.

echo Steps:
echo 1. Install VIPS library
echo 2. Install w64devkit (C compiler)
echo 3. Build and test ttc.exe
echo.

set /p confirm="Proceed with complete development setup? (y/n): "
if /i not "!confirm!"=="y" (
    echo Setup cancelled.
    pause
    exit /b 0
)

echo.
echo ========================================
echo Step 1: Installing VIPS Library
echo ========================================
echo.

call setup-vips.bat

if errorlevel 1 (
    echo ERROR: VIPS setup failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Step 2: Installing w64devkit
echo ========================================
echo.

if exist "w64devkit\bin\gcc.exe" (
    echo w64devkit already installed!
    w64devkit\bin\gcc.exe --version | findstr "gcc"
) else (
    echo Installing w64devkit...
    call install-w64devkit.bat
    
    if errorlevel 1 (
        echo ERROR: w64devkit setup failed
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Step 3: Building and Testing ttc.exe
echo ========================================
echo.

echo Building ttc.exe...
call build-w64devkit.bat

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo Testing ttc.exe with DNG file...
call run-ttc-bash.bat .

echo.
echo ========================================
echo Development Setup Complete!
echo ========================================
echo.

echo SUCCESS! Your development environment is ready.
echo.
echo Available commands:
echo - Build:           build-w64devkit.bat
echo - Test DNG:        ./ttc-bash .
echo - Test help:       ./ttc-bash --help
echo - Test version:    ./ttc-bash --version
echo - Rebuild VIPS:    setup-vips.bat
echo.

echo Project structure:
echo - Source code:     ttc-fixed.c
echo - Executable:      ttc.exe
echo - Build scripts:   build-*.bat
echo - Setup scripts:   setup-*.bat
echo.

echo Ready for Test Target Cropper C development!
pause
