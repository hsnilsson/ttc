@echo off
setlocal enabledelayedexpansion
REM Install libraw from source

echo ========================================
echo Installing libraw from source
echo ========================================
echo.

set "version=0.21.2"
set "downloadUrl=https://github.com/LibRaw/LibRaw/archive/refs/tags/%version%.tar.gz"

echo Downloading libraw source %version%...
echo.

REM Remove any existing libraw
if exist "C:\libraw" (
    echo Removing existing libraw...
    rmdir /s /q "C:\libraw"
)

REM Download source
echo Downloading from: %downloadUrl%
curl -L --retry 3 --retry-delay 10 --show-error -o "libraw-%version%.tar.gz" "%downloadUrl%"

if not exist "libraw-%version%.tar.gz" (
    echo ERROR: Failed to download libraw source
    pause
    exit /b 1
)

echo.
echo Download successful!
echo.

echo Extracting libraw source...
REM Use tar to extract (built into Windows 10+)
tar -xf "libraw-%version%.tar.gz" -C C:\

if not exist "C:\LibRaw-%version%" (
    echo ERROR: Failed to extract libraw source
    pause
    exit /b 1
)

REM Rename to standard location
move "C:\LibRaw-%version%" "C:\libraw"

echo.
echo libraw source extracted successfully!
echo.

echo Creating include directory structure...
if not exist "C:\libraw\include" mkdir "C:\libraw\include"
if not exist "C:\libraw\include\libraw" mkdir "C:\libraw\include\libraw"

REM Copy headers
copy "C:\libraw\libraw\libraw.h" "C:\libraw\include\libraw\" >nul 2>&1
copy "C:\libraw\libraw\libraw_alloc.h" "C:\libraw\include\libraw\" >nul 2>&1
copy "C:\libraw\libraw\libraw_const.h" "C:\libraw\include\libraw\" >nul 2>&1
copy "C:\libraw\libraw\libraw_datastream.h" "C:\libraw\include\libraw\" >nul 2>&1
copy "C:\libraw\libraw\libraw_internal.h" "C:\libraw\include\libraw\" >nul 2>&1
copy "C:\libraw\libraw\libraw_types.h" "C:\libraw\include\libraw\" >nul 2>&1

echo.
echo Verifying installation...
if exist "C:\libraw\include\libraw\libraw.h" (
    echo Found: C:\libraw\include\libraw\libraw.h
) else (
    echo ERROR: libraw.h not found
    pause
    exit /b 1
)

echo.
echo NOTE: This is source installation. You may need to build libraw library
echo or use a pre-compiled binary for full functionality.
echo.

echo Cleaning up...
del "libraw-%version%.tar.gz"

echo.
echo SUCCESS! libraw %version% source installed to C:\libraw
echo.

pause
