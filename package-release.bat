@echo off
setlocal enabledelayedexpansion
REM Package the release for distribution

echo ========================================
echo Packaging Release for Distribution
echo ========================================
echo.

REM Create the release first
call create-release.bat

if not exist "release" (
    echo ERROR: Release folder not found.
    pause
    exit /b 1
)

echo.
echo Creating distribution packages...
echo.

REM Get current date for versioning
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"

set "VERSION=1.2.0"
set "DATE=%YYYY%%MM%%DD%"

echo Creating ZIP package...
if exist "7z.exe" (
    echo Using 7-Zip...
    7z a -tzip "ttc-c-v%VERSION%-%DATE%.zip" release\*
) else (
    echo Using PowerShell...
    powershell -Command "Compress-Archive -Path 'release\*' -DestinationPath 'ttc-c-v%VERSION%-%DATE%.zip' -Force"
)

echo.
echo Creating archive with source...
if exist "7z.exe" (
    7z a -tzip "ttc-c-v%VERSION%-%DATE%-with-source.zip" release\* ttc-fixed.c Makefile build-*.bat *.md
) else (
    powershell -Command "Compress-Archive -Path 'release\*', 'ttc-fixed.c', 'Makefile', 'build-*.bat', '*.md' -DestinationPath 'ttc-c-v%VERSION%-%DATE%-with-source.zip' -Force"
)

echo.
echo ========================================
echo Packaging Complete!
echo ========================================
echo.

echo Created packages:
if exist "ttc-c-v%VERSION%-%DATE%.zip" (
    echo - ttc-c-v%VERSION%-%DATE%.zip (binary package)
    dir "ttc-c-v%VERSION%-%DATE%.zip" | findstr "ttc-c-v%VERSION%-%DATE%.zip"
)

if exist "ttc-c-v%VERSION%-%DATE%-with-source.zip" (
    echo - ttc-c-v%VERSION%-%DATE%-with-source.zip (with source)
    dir "ttc-c-v%VERSION%-%DATE%-with-source.zip" | findstr "ttc-c-v%VERSION%-%DATE%-with-source.zip"
)

echo.
echo Package contents:
echo - Binary executable (ttc.exe)
echo - Documentation and scripts
echo - Installation instructions
echo - VIPS DLL collection script
echo - Release notes and package info

echo.
echo Ready for GitHub release!
echo Upload the ZIP files to the releases page.

pause
